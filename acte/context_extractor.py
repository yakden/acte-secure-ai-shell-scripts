"""ContextExtractor: derive execution-context features from a parsed script.

Where the SemanticParser answers *what commands are present*, the
ContextExtractor answers *what would happen if this ran*: does it need root,
does it touch the network, how broad is its filesystem scope, is it
irreversible, and does it show signs of obfuscation. These features are scaled
to [0, 1] so they can be combined linearly inside the TrustEvaluationEngine and
inspected directly during ablation studies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Dict

from acte.semantic_parser import ParsedScript


# Commands that imply each contextual dimension.
_PRIVILEGED_CMDS = {"sudo", "su", "doas", "pkexec", "setcap", "visudo"}
_NETWORK_CMDS = {"curl", "wget", "nc", "ncat", "netcat", "ssh", "scp", "ftp",
                 "telnet", "socat", "rsync", "tftp"}
_DESTRUCTIVE_CMDS = {"rm", "dd", "mkfs", "shred", "fdisk", "parted", "wipefs",
                     "mke2fs"}
_SENSITIVE_ROOTS = ("/etc", "/boot", "/usr", "/bin", "/sbin", "/lib", "/dev",
                    "/var", "/root", "/sys", "/proc")


@dataclass
class ContextFeatures:
    """Execution-context features, each normalized to [0, 1]."""

    privilege_required: float = 0.0
    network_egress: float = 0.0
    filesystem_scope: float = 0.0
    irreversibility: float = 0.0
    obfuscation: float = 0.0

    def as_vector(self) -> Dict[str, float]:
        return asdict(self)


class ContextExtractor:
    """Compute :class:`ContextFeatures` from a :class:`ParsedScript`."""

    def extract(self, parsed: ParsedScript) -> ContextFeatures:
        cmds = parsed.command_set()
        raw = parsed.raw
        feats = ContextFeatures()

        feats.privilege_required = self._privilege(cmds, raw)
        feats.network_egress = self._network(cmds, parsed)
        feats.filesystem_scope = self._fs_scope(parsed)
        feats.irreversibility = self._irreversibility(cmds, raw)
        feats.obfuscation = self._obfuscation(parsed, raw)
        return feats

    # -- individual dimensions ------------------------------------------------
    @staticmethod
    def _privilege(cmds, raw) -> float:
        score = 0.0
        if cmds & _PRIVILEGED_CMDS:
            score += 0.7
        if re.search(r"NOPASSWD|/etc/sudoers|chmod\s+(\+s|4[0-7]{3})", raw):
            score += 0.3
        return min(1.0, score)

    @staticmethod
    def _network(cmds, parsed: ParsedScript) -> float:
        score = 0.0
        if cmds & _NETWORK_CMDS:
            score += 0.5
        if parsed.urls:
            score += 0.3
        if parsed.pipes_to_shell:
            score += 0.2
        if re.search(r"/dev/(tcp|udp)/", parsed.raw):
            score += 0.4
        return min(1.0, score)

    @staticmethod
    def _fs_scope(parsed: ParsedScript) -> float:
        score = 0.0
        targets = parsed.paths + parsed.devices
        if any(t.startswith(_SENSITIVE_ROOTS) for t in targets):
            score += 0.5
        if parsed.devices:
            score += 0.3
        # Recursive or wildcard operations broaden the scope substantially.
        if re.search(r"-[a-zA-Z]*[rR][a-zA-Z]*\b", parsed.raw) and parsed.paths:
            score += 0.2
        if re.search(r"\s(/|/\*|~|\$HOME)(\s|$)", parsed.raw):
            score += 0.3
        return min(1.0, score)

    @staticmethod
    def _irreversibility(cmds, raw) -> float:
        score = 0.0
        if cmds & _DESTRUCTIVE_CMDS:
            score += 0.5
        if re.search(r"\brm\b[^\n]*-[a-zA-Z]*[rf]", raw):
            score += 0.2
        if re.search(r"\bdd\b[^\n]*of=/dev/|mkfs|--no-preserve-root|>\s*/dev/sd", raw):
            score += 0.3
        if re.search(r"\b(shred|wipefs)\b", raw):
            score += 0.2
        return min(1.0, score)

    @staticmethod
    def _obfuscation(parsed: ParsedScript, raw: str) -> float:
        score = 0.0
        if re.search(r"\bbase64\s+(-d|--decode)\b", raw):
            score += 0.35
        if re.search(r"\beval\b", raw):
            score += 0.25
        if re.search(r"(\\x[0-9a-fA-F]{2}){4,}", raw):
            score += 0.25
        if re.search(r"\$\(\s*printf[^\n]*\\[0-7]{3}", raw):
            score += 0.2
        if re.search(r"\brev\b|\btr\b[^\n]*\[", raw):
            score += 0.1
        # Many command substitutions relative to script size hint at indirection.
        if parsed.line_count and parsed.command_substitutions / max(1, parsed.line_count) > 1.5:
            score += 0.15
        return min(1.0, score)
