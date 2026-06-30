"""RuntimeMonitor: a syscall-logging enforcement sketch.

This component documents *how* an ACTE-generated :class:`ExecutionPolicy` would
be enforced at runtime, without requiring root or a live sandbox. Given a policy
it can:

* report which syscalls would be allowed, audited, or blocked,
* simulate a stream of observed syscalls and decide the action for each,
* emit a structured audit log.

In a production deployment the same decision table would be backed by a real
seccomp-bpf filter plus an eBPF/auditd tap; here it is a faithful but inert
simulation so the behavior is testable and reproducible.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from acte.policy_generator import ExecutionPolicy
from acte.trust_engine import TrustLevel


@dataclass
class MonitorEvent:
    syscall: str
    action: str          # "allow" | "audit" | "block" | "kill"
    reason: str


@dataclass
class MonitorReport:
    trust_level: str
    decision: str
    events: List[MonitorEvent] = field(default_factory=list)
    blocked: int = 0
    audited: int = 0
    allowed: int = 0
    killed: int = 0

    def to_dict(self) -> dict:
        return {
            "trust_level": self.trust_level,
            "decision": self.decision,
            "allowed": self.allowed,
            "audited": self.audited,
            "blocked": self.blocked,
            "killed": self.killed,
            "events": [e.__dict__ for e in self.events],
        }


class RuntimeMonitor:
    """Simulate enforcement of a generated execution policy (no root needed)."""

    def __init__(self, policy: ExecutionPolicy):
        self.policy = policy
        self._allow, self._block, self._kill = self._build_tables(policy)
        self._audit = policy.decision in ("allow_with_audit", "sandbox")

    @staticmethod
    def _build_tables(policy: ExecutionPolicy):
        allow, block, kill = set(), set(), set()
        for rule in policy.seccomp_profile.get("syscalls", []):
            names = rule.get("names", [])
            action = rule.get("action", "")
            if action == "SCMP_ACT_ALLOW":
                allow.update(names)
            elif action == "SCMP_ACT_ERRNO":
                block.update(names)
            elif action == "SCMP_ACT_KILL_PROCESS":
                kill.update(names)
        default_block = policy.seccomp_profile.get("defaultAction") == "SCMP_ACT_ERRNO"
        return allow, block, (kill, default_block)

    def decide(self, syscall: str) -> MonitorEvent:
        kill_set, default_block = self._kill
        if syscall in kill_set:
            return MonitorEvent(syscall, "kill", "syscall on kill list at this trust level")
        if syscall in self._block:
            return MonitorEvent(syscall, "block", "syscall explicitly blocked by policy")
        if syscall in self._allow:
            action = "audit" if self._audit else "allow"
            reason = "allowed (audited)" if self._audit else "allowed by policy"
            return MonitorEvent(syscall, action, reason)
        # Not on any list: governed by the default action.
        if default_block:
            return MonitorEvent(syscall, "block", "blocked by default action (not allow-listed)")
        return MonitorEvent(syscall, "allow", "permitted by default-allow policy")

    def observe(self, syscalls: List[str]) -> MonitorReport:
        """Run a simulated syscall trace through the policy decision table."""
        report = MonitorReport(
            trust_level=self.policy.trust_level.value,
            decision=self.policy.decision,
        )
        for sc in syscalls:
            ev = self.decide(sc)
            report.events.append(ev)
            if ev.action == "allow":
                report.allowed += 1
            elif ev.action == "audit":
                report.audited += 1
            elif ev.action == "block":
                report.blocked += 1
            elif ev.action == "kill":
                report.killed += 1
        return report

    def explain(self) -> str:
        return (
            f"RuntimeMonitor[{self.policy.trust_level.value}] decision="
            f"{self.policy.decision}; allow={len(self._allow)} syscalls, "
            f"block={len(self._block)}, audit={'on' if self._audit else 'off'}. "
            "Enforcement is simulated (no root / no live seccomp in the prototype)."
        )
