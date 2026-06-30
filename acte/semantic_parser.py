"""SemanticParser: turn a shell script into structured command/AST features.

The parser uses ``bashlex`` (a Python port of the bash parser) when the script
is well-formed enough to parse, and falls back to a robust line/word tokenizer
when bashlex raises (which happens often with obfuscated or intentionally
malformed adversarial scripts). Either way it extracts:

* command names actually invoked,
* command-line flags,
* targets (file paths, URLs, devices),
* structural facts (pipes, pipe-to-shell, command substitutions, redirections,
  here-docs, background jobs).

These facts are consumed by ContextExtractor and ThreatIntel downstream.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from typing import List, Set

try:
    import bashlex

    _HAS_BASHLEX = True
except Exception:  # pragma: no cover - bashlex is a declared dependency
    _HAS_BASHLEX = False


# Words that are shell interpreters; a pipe whose right-hand command is one of
# these is the classic "download | shell" remote-execution pattern.
SHELL_INTERPRETERS: Set[str] = {"sh", "bash", "dash", "zsh", "ksh", "csh", "tcsh"}

_URL_RE = re.compile(r"\b(?:https?|ftp|ftps)://[^\s'\"|;&)]+", re.IGNORECASE)
_PATH_RE = re.compile(r"(?<![\w-])(/[A-Za-z0-9_.\-/]+|~/[A-Za-z0-9_.\-/]*)")
_DEVICE_RE = re.compile(r"/dev/[A-Za-z0-9/]+")


@dataclass
class ParsedScript:
    """Structured view of a parsed shell script."""

    raw: str
    parsed_with: str  # "bashlex" or "fallback"
    commands: List[str] = field(default_factory=list)        # command names
    flags: List[str] = field(default_factory=list)           # all flags seen
    words: List[str] = field(default_factory=list)           # all tokens
    paths: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    devices: List[str] = field(default_factory=list)
    pipe_count: int = 0
    pipes_to_shell: bool = False
    command_substitutions: int = 0
    redirections: int = 0
    background_jobs: int = 0
    heredocs: int = 0
    line_count: int = 0
    comment_lines: int = 0

    def command_set(self) -> Set[str]:
        return set(self.commands)

    def to_dict(self) -> dict:
        return {
            "parsed_with": self.parsed_with,
            "commands": self.commands,
            "flags": self.flags,
            "paths": self.paths,
            "urls": self.urls,
            "devices": self.devices,
            "pipe_count": self.pipe_count,
            "pipes_to_shell": self.pipes_to_shell,
            "command_substitutions": self.command_substitutions,
            "redirections": self.redirections,
            "background_jobs": self.background_jobs,
            "heredocs": self.heredocs,
            "line_count": self.line_count,
            "comment_lines": self.comment_lines,
        }


class SemanticParser:
    """Parse shell scripts into :class:`ParsedScript` feature bundles."""

    def parse(self, script: str) -> ParsedScript:
        result = ParsedScript(raw=script, parsed_with="fallback")

        lines = script.splitlines()
        result.line_count = len(lines)
        result.comment_lines = sum(
            1 for ln in lines if ln.strip().startswith("#") and not ln.strip().startswith("#!")
        )

        # Regex-based extraction of targets works regardless of parse strategy
        # and is resilient to obfuscation.
        result.urls = _URL_RE.findall(script)
        result.devices = _DEVICE_RE.findall(script)
        result.paths = [p for p in _PATH_RE.findall(script) if not p.startswith("/dev/")]

        # Structural counts via lightweight scanning (robust to malformed input).
        result.pipe_count = len(re.findall(r"(?<![|])\|(?![|])", script))
        result.command_substitutions = len(re.findall(r"\$\(|`", script))
        result.redirections = len(re.findall(r"(?<![0-9])>>?|<<?", script))
        result.background_jobs = len(re.findall(r"&(?!&)", script))
        result.heredocs = len(re.findall(r"<<-?\s*[\"']?[A-Za-z_]", script))
        result.pipes_to_shell = self._detect_pipe_to_shell(script)

        parsed_ok = False
        if _HAS_BASHLEX:
            parsed_ok = self._parse_with_bashlex(script, result)

        if parsed_ok:
            result.parsed_with = "bashlex"
        else:
            self._parse_fallback(script, result)
            result.parsed_with = "fallback"

        # De-duplicate while preserving order for stable, reproducible output.
        result.commands = _dedup(result.commands)
        result.flags = _dedup(result.flags)
        result.paths = _dedup(result.paths)
        result.urls = _dedup(result.urls)
        result.devices = _dedup(result.devices)
        return result

    # -- bashlex path ---------------------------------------------------------
    def _parse_with_bashlex(self, script: str, result: ParsedScript) -> bool:
        """Populate command/flag/word lists using bashlex. Returns success."""
        commands: List[str] = []
        flags: List[str] = []
        words: List[str] = []
        parsed_any = False

        for line in script.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                trees = bashlex.parse(line)
            except Exception:
                # A single bad line should not abort the whole parse; we simply
                # rely on the fallback for the lines we could not parse.
                continue
            parsed_any = True
            for tree in trees:
                self._walk_bashlex(tree, commands, flags, words)

        if not parsed_any:
            return False

        result.commands = commands
        result.flags = flags
        result.words = words
        return True

    def _walk_bashlex(self, node, commands, flags, words) -> None:
        kind = getattr(node, "kind", None)
        if kind == "command":
            parts = [p for p in node.parts if getattr(p, "kind", None) == "word"]
            for i, part in enumerate(parts):
                word = part.word
                words.append(word)
                if i == 0 and not word.startswith("-"):
                    commands.append(_basename(word))
                elif word.startswith("-"):
                    flags.append(word)
        # Recurse into all children.
        for child in getattr(node, "parts", []) or []:
            self._walk_bashlex(child, commands, flags, words)
        for attr in ("command", "list", "pipe"):
            sub = getattr(node, attr, None)
            if sub is not None and hasattr(sub, "kind"):
                self._walk_bashlex(sub, commands, flags, words)

    # -- fallback path --------------------------------------------------------
    def _parse_fallback(self, script: str, result: ParsedScript) -> None:
        commands: List[str] = []
        flags: List[str] = []
        words: List[str] = []

        # Split on command separators so that each segment's first token is a
        # command name (handles ';', '|', '&&', '||', '&').
        segments = re.split(r"\|\||&&|[;|&\n]", script)
        for seg in segments:
            seg = seg.strip()
            if not seg or seg.startswith("#"):
                continue
            try:
                tokens = shlex.split(seg, comments=True)
            except ValueError:
                # Unbalanced quotes (common in obfuscated payloads): fall back
                # to a naive whitespace split so we still capture tokens.
                tokens = seg.split()
            if not tokens:
                continue
            # Skip common shell keywords/assignments to find the real command.
            cmd = None
            for tok in tokens:
                if "=" in tok and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tok):
                    continue  # variable assignment prefix
                if tok in {"do", "then", "else", "fi", "done", "{", "}", "(", ")"}:
                    continue
                cmd = tok
                break
            if cmd and not cmd.startswith("-"):
                commands.append(_basename(cmd))
            for tok in tokens:
                words.append(tok)
                if tok.startswith("-") and len(tok) > 1:
                    flags.append(tok)

        result.commands = commands
        result.flags = flags
        result.words = words

    # -- helpers --------------------------------------------------------------
    @staticmethod
    def _detect_pipe_to_shell(script: str) -> bool:
        """True if any pipeline feeds into a shell interpreter."""
        for seg in script.split("|")[1:]:
            seg = seg.strip()
            m = re.match(r"(sudo\s+)?(\S+)", seg)
            if not m:
                continue
            target = _basename(m.group(2))
            if target in SHELL_INTERPRETERS:
                return True
        return False


def _basename(word: str) -> str:
    word = word.strip().strip("\"'")
    if "/" in word:
        word = word.rsplit("/", 1)[-1]
    return word


def _dedup(seq: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
