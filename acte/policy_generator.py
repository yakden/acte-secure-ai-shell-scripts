"""PolicyGenerator: turn a trust level into an adaptive execution policy.

The generated artifacts are *sketches* intended to demonstrate how an ACTE
trust decision would translate into concrete runtime constraints. They are not
enforced live by this prototype (that would require root and a container/seccomp
runtime); they are emitted as data so they can be inspected, version-controlled
and, in a production deployment, handed to the relevant enforcement layer.

For each trust level we emit:
* a seccomp profile sketch (syscall allow/deny lists in Docker's JSON shape),
* an Open Policy Agent (Rego) policy snippet,
* namespace / cgroup resource constraints.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List

from acte.trust_engine import TrustAssessment, TrustLevel


# Baseline set of syscalls every level may use (kept intentionally small).
_BASE_SYSCALLS = [
    "read", "write", "close", "fstat", "lseek", "mmap", "munmap", "brk",
    "rt_sigaction", "rt_sigprocmask", "exit", "exit_group", "arch_prctl",
    "access", "openat", "newfstatat", "getrandom",
]

# Syscalls layered in (allowed) as trust increases.
_LEVEL_EXTRA_SYSCALLS: Dict[TrustLevel, List[str]] = {
    TrustLevel.DENY: [],
    TrustLevel.RESTRICT: ["stat", "getdents64", "fcntl"],
    TrustLevel.MONITOR: ["stat", "getdents64", "fcntl", "clone", "execve",
                         "wait4", "pipe2", "dup2"],
    TrustLevel.TRUSTED: ["stat", "getdents64", "fcntl", "clone", "execve",
                         "wait4", "pipe2", "dup2", "socket", "connect",
                         "fork", "vfork", "setuid", "setgid"],
}

# Network and privilege posture per level.
_LEVEL_PROFILE = {
    TrustLevel.TRUSTED: {
        "action": "allow",
        "network": "allow",
        "new_privileges": True,
        "read_only_rootfs": False,
        "cpu_quota": "unlimited",
        "memory_limit": "unlimited",
        "pids_limit": 4096,
    },
    TrustLevel.MONITOR: {
        "action": "allow_with_audit",
        "network": "allow",
        "new_privileges": False,
        "read_only_rootfs": False,
        "cpu_quota": "50%",
        "memory_limit": "1g",
        "pids_limit": 512,
    },
    TrustLevel.RESTRICT: {
        "action": "sandbox",
        "network": "deny",
        "new_privileges": False,
        "read_only_rootfs": True,
        "cpu_quota": "20%",
        "memory_limit": "256m",
        "pids_limit": 64,
    },
    TrustLevel.DENY: {
        "action": "deny",
        "network": "deny",
        "new_privileges": False,
        "read_only_rootfs": True,
        "cpu_quota": "0%",
        "memory_limit": "0",
        "pids_limit": 0,
    },
}


@dataclass
class ExecutionPolicy:
    """A generated, adaptive execution policy for one script."""

    trust_level: TrustLevel
    decision: str
    seccomp_profile: dict = field(default_factory=dict)
    rego_policy: str = ""
    namespace_constraints: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "trust_level": self.trust_level.value,
            "decision": self.decision,
            "seccomp_profile": self.seccomp_profile,
            "rego_policy": self.rego_policy,
            "namespace_constraints": self.namespace_constraints,
        }


class PolicyGenerator:
    """Generate :class:`ExecutionPolicy` artifacts from a trust assessment."""

    def generate(self, assessment: TrustAssessment) -> ExecutionPolicy:
        level = assessment.trust_level
        profile = _LEVEL_PROFILE[level]
        return ExecutionPolicy(
            trust_level=level,
            decision=profile["action"],
            seccomp_profile=self._seccomp(level, profile),
            rego_policy=self._rego(level, profile, assessment),
            namespace_constraints=self._namespaces(level, profile),
        )

    # -- seccomp --------------------------------------------------------------
    def _seccomp(self, level: TrustLevel, profile: dict) -> dict:
        allowed = sorted(set(_BASE_SYSCALLS) | set(_LEVEL_EXTRA_SYSCALLS[level]))
        default_action = "SCMP_ACT_ERRNO" if level != TrustLevel.TRUSTED else "SCMP_ACT_ALLOW"
        sketch = {
            "defaultAction": default_action,
            "comment": (
                f"ACTE seccomp sketch for trust level {level.value}. "
                "Not enforced by the prototype; suitable for docker --security-opt "
                "seccomp=<file> in a real deployment."
            ),
            "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_AARCH64"],
            "syscalls": [
                {"names": allowed, "action": "SCMP_ACT_ALLOW"},
            ],
        }
        if profile["network"] == "deny":
            sketch["syscalls"].append(
                {
                    "names": ["socket", "connect", "bind", "sendto", "recvfrom"],
                    "action": "SCMP_ACT_ERRNO",
                    "comment": "network egress blocked at this trust level",
                }
            )
        if level == TrustLevel.DENY:
            sketch["syscalls"].append(
                {
                    "names": ["execve", "execveat", "fork", "vfork", "clone"],
                    "action": "SCMP_ACT_KILL_PROCESS",
                    "comment": "execution denied",
                }
            )
        return sketch

    # -- rego -----------------------------------------------------------------
    def _rego(self, level: TrustLevel, profile: dict, assessment: TrustAssessment) -> str:
        allow = "true" if profile["action"] in ("allow", "allow_with_audit") else "false"
        audit = "true" if profile["action"] in ("allow_with_audit", "sandbox") else "false"
        hits = ", ".join(f'"{h.id}"' for h in assessment.signature_hits) or ""
        return (
            "package acte.execution\n\n"
            "# Auto-generated by ACTE PolicyGenerator (sketch, not live-enforced).\n"
            f"# trust_level = {level.value}\n"
            f"# risk_score = {assessment.risk_score:.4f}\n\n"
            f"default allow = false\n\n"
            f"trust_level := \"{level.value}\"\n"
            f"risk_score := {assessment.risk_score:.4f}\n"
            f"matched_signatures := [{hits}]\n\n"
            f"allow {{ trust_level == \"{level.value}\"; {allow} }}\n\n"
            f"audit {{ {audit} }}\n\n"
            f"network_egress_allowed := {str(profile['network'] == 'allow').lower()}\n"
            f"allow_new_privileges := {str(profile['new_privileges']).lower()}\n"
        )

    # -- namespace / cgroup ---------------------------------------------------
    def _namespaces(self, level: TrustLevel, profile: dict) -> dict:
        return {
            "namespaces": ["pid", "mount", "uts", "ipc"]
            + (["net"] if profile["network"] == "deny" else []),
            "network": profile["network"],
            "read_only_rootfs": profile["read_only_rootfs"],
            "no_new_privileges": not profile["new_privileges"],
            "cgroup": {
                "cpu_quota": profile["cpu_quota"],
                "memory_limit": profile["memory_limit"],
                "pids_limit": profile["pids_limit"],
            },
            "capabilities_drop": ["ALL"]
            if level in (TrustLevel.RESTRICT, TrustLevel.DENY)
            else ["NET_ADMIN", "SYS_ADMIN", "SYS_MODULE"],
        }

    @staticmethod
    def to_json(policy: ExecutionPolicy) -> str:
        return json.dumps(policy.to_dict(), indent=2)
