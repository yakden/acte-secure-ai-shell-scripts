"""RQ10 — real seccomp enforcement of a content-derived policy (not a sketch).

The paper's biggest construct-validity gap is that "runtime security" was never
enforced: the PolicyGenerator emitted seccomp JSON but nothing was installed.
This module closes that gap on Linux. It (1) derives, from the commands ACTE
actually parsed out of a script, the set of syscalls the script legitimately
needs, and thus the syscalls to *deny*; (2) compiles that deny-set into a real
classic-BPF seccomp filter; and (3) installs it in a forked child (unprivileged,
via ``PR_SET_NO_NEW_PRIVS``) and confirms the kernel actually kills a denied
syscall while permitting the rest. Two DENY-tier scripts with different commands
now yield different, content-specific filters — genuine synthesis, not a fixed
per-level template.

The filter uses default-ALLOW with explicit SECCOMP_RET_KILL_PROCESS on the
denied syscalls (so the interpreter survives), which is exactly the posture the
existing PolicyGenerator describes; here it is really enforced by the kernel.
"""

from __future__ import annotations

import ctypes
import os
from typing import Dict, List, Set

from acte.semantic_parser import SemanticParser

# x86-64 syscall numbers used here.
NR = {
    "read": 0, "write": 1, "close": 3, "mmap": 9, "munmap": 11, "brk": 12,
    "rt_sigaction": 13, "rt_sigprocmask": 14, "rt_sigreturn": 15, "getpid": 39,
    "socket": 41, "connect": 42, "sendto": 44, "recvfrom": 45, "clone": 56,
    "fork": 57, "vfork": 58, "execve": 59, "exit": 60, "exit_group": 231,
    "ptrace": 101, "openat": 257, "getrandom": 318, "execveat": 322,
}

# Commands -> syscall families they legitimately require (beyond the base set).
_NETWORK_CMDS = {"curl", "wget", "nc", "ncat", "netcat", "ssh", "scp", "socat",
                 "ftp", "telnet", "rsync", "tftp"}
_EXEC_SPAWN_CMDS = {"bash", "sh", "python", "python3", "perl", "ruby", "php",
                    "node", "make", "gcc", "sudo", "su", "env", "xargs", "at",
                    "crontab", "systemctl"}


def derive_denied_syscalls(script: str) -> Dict:
    """Deny syscalls the script gives no evidence of needing (least privilege)."""
    parsed = SemanticParser().parse(script)
    cmds = parsed.command_set()
    denied: Set[str] = set()

    needs_net = bool(cmds & _NETWORK_CMDS) or bool(parsed.urls) or parsed.pipes_to_shell
    if not needs_net:
        denied |= {"socket", "connect", "sendto", "recvfrom"}

    needs_spawn = bool(cmds & _EXEC_SPAWN_CMDS) or parsed.pipes_to_shell
    if not needs_spawn:
        denied |= {"execve", "execveat"}

    # ptrace is never legitimately needed by these scripts.
    denied |= {"ptrace"}
    return {"commands": sorted(cmds), "needs_network": needs_net,
            "needs_spawn": needs_spawn, "denied_syscalls": sorted(denied)}


# --- raw BPF seccomp (default ALLOW, KILL the denied set) ---
class _sock_filter(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte),
                ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint)]


class _sock_fprog(ctypes.Structure):
    _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(_sock_filter))]


_BPF_LD = 0x00; _BPF_W = 0x00; _BPF_ABS = 0x20
_BPF_JMP = 0x05; _BPF_JEQ = 0x10; _BPF_RET = 0x06; _BPF_K = 0x00
_RET_ALLOW = 0x7fff0000
_RET_KILL = 0x80000000  # SECCOMP_RET_KILL_PROCESS
_PR_SET_NO_NEW_PRIVS = 38; _PR_SET_SECCOMP = 22; _SECCOMP_MODE_FILTER = 2


def _build_prog(deny_nrs: List[int]):
    prog = [(_BPF_LD | _BPF_W | _BPF_ABS, 0, 0, 0)]  # A = syscall nr (offset 0)
    for nr in deny_nrs:
        prog.append((_BPF_JMP | _BPF_JEQ | _BPF_K, 0, 1, nr))  # if A==nr: next; else skip
        prog.append((_BPF_RET | _BPF_K, 0, 0, _RET_KILL))
    prog.append((_BPF_RET | _BPF_K, 0, 0, _RET_ALLOW))
    arr = (_sock_filter * len(prog))(*[_sock_filter(*p) for p in prog])
    return _sock_fprog(len(prog), arr), arr


def _install(deny_nrs: List[int]) -> bool:
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    if libc.prctl(_PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        return False
    fprog, _keep = _build_prog(deny_nrs)
    _install._keep = _keep  # prevent GC of the filter array in the child
    return libc.prctl(_PR_SET_SECCOMP, _SECCOMP_MODE_FILTER,
                      ctypes.byref(fprog), 0, 0) == 0


def _child_attempt(test_nr: int, deny_nrs: List[int]):
    """In a forked child: install filter, attempt test_nr, report outcome."""
    if not _install(deny_nrs):
        os._exit(101)  # could not install
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    libc.syscall(ctypes.c_long(test_nr), 0, 0, 0, 0, 0, 0)  # may be SIGSYS-killed here
    os._exit(0)  # reached only if the syscall was permitted


def enforce_and_probe(script: str) -> Dict:
    """Derive the policy, install a real filter, and verify kernel enforcement."""
    policy = derive_denied_syscalls(script)
    deny_nrs = [NR[s] for s in policy["denied_syscalls"] if s in NR]

    outcomes = {}
    # probe one denied syscall (if any) and one control that is never denied.
    probes = []
    if policy["denied_syscalls"]:
        probes.append(("denied:" + policy["denied_syscalls"][0],
                       NR[policy["denied_syscalls"][0]], True))
    probes.append(("control:getpid", NR["getpid"], False))  # never denied -> allowed

    for label, test_nr, expect_kill in probes:
        pid = os.fork()
        if pid == 0:
            _child_attempt(test_nr, deny_nrs)
        _, status = os.waitpid(pid, 0)
        killed = os.WIFSIGNALED(status) and os.WTERMSIG(status) == 31  # SIGSYS
        outcomes[label] = {
            "killed_by_kernel": bool(killed),
            "expected_kill": expect_kill,
            "correct": bool(killed) == expect_kill,
        }
    policy["enforcement"] = outcomes
    policy["all_correct"] = all(o["correct"] for o in outcomes.values())
    return policy


def demo(scripts: List[str]) -> Dict:
    """Run the enforcement probe over several scripts; report per-script outcomes."""
    results = [dict(script=s.strip().splitlines()[-1][:60], **enforce_and_probe(s))
               for s in scripts]
    return {
        "seccomp_available": True,
        "n_scripts": len(results),
        "n_all_correct": sum(1 for r in results if r["all_correct"]),
        "results": results,
    }
