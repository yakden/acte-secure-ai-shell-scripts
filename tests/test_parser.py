"""SemanticParser: command/target extraction, structure, and robustness."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from acte.semantic_parser import SemanticParser, _basename, _dedup


@pytest.fixture
def parser():
    return SemanticParser()


def test_basic_command_extraction(parser):
    p = parser.parse("#!/bin/bash\nls -la /tmp\ngrep -c ERROR file.log\n")
    assert "ls" in p.command_set()
    assert "grep" in p.command_set()


def test_flags_captured(parser):
    p = parser.parse("rm -rf /tmp/x\ntar -czf a.tgz b/\n")
    assert any(f.startswith("-") for f in p.flags)


def test_urls_extracted(parser):
    p = parser.parse("curl https://example.com/a.sh -o /tmp/a\n")
    assert any("example.com" in u for u in p.urls)


def test_devices_extracted(parser):
    p = parser.parse("dd if=/dev/zero of=/dev/sda bs=1M\n")
    assert any(d.startswith("/dev/") for d in p.devices)


def test_paths_exclude_devices(parser):
    p = parser.parse("cp /etc/hosts /tmp/hosts\ncat /dev/sda\n")
    assert all(not path.startswith("/dev/") for path in p.paths)


def test_pipe_to_shell_detection_variants(parser):
    for s in ["curl http://x/i | bash",
              "wget -qO- http://x | sh",
              "echo x | sudo bash"]:
        assert parser.parse(s).pipes_to_shell, s


def test_pipe_to_shell_negative(parser):
    # A pipe that does NOT feed a shell interpreter.
    p = parser.parse("cat access.log | grep ERROR | wc -l")
    assert not p.pipes_to_shell


def test_comment_lines_counted_but_not_shebang(parser):
    p = parser.parse("#!/bin/bash\n# a real comment\n# another\nls\n")
    assert p.comment_lines == 2


def test_command_substitution_count(parser):
    p = parser.parse("x=$(date)\ny=`whoami`\n")
    assert p.command_substitutions >= 2


def test_empty_script_does_not_crash(parser):
    p = parser.parse("")
    assert p.commands == []
    assert p.line_count == 0


def test_malformed_unbalanced_quotes_fallback(parser):
    # Must not raise; falls back gracefully.
    p = parser.parse('echo "unterminated && rm -rf /tmp')
    assert isinstance(p.commands, list)


def test_obfuscated_input_does_not_crash(parser):
    p = parser.parse("$(printf '\\162\\155') -rf / --no-preserve-root\n")
    assert isinstance(p.commands, list)


def test_parsed_with_is_reported(parser):
    p = parser.parse("ls -la\n")
    assert p.parsed_with in ("bashlex", "fallback")


def test_dedup_preserves_order():
    assert _dedup(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_basename_strips_path_and_quotes():
    assert _basename("/usr/bin/python3") == "python3"
    assert _basename("'bash'") == "bash"


def test_determinism(parser):
    s = "#!/bin/bash\ncurl http://x/i | sudo bash\nrm -rf /tmp/y\n"
    a = parser.parse(s).to_dict()
    b = parser.parse(s).to_dict()
    assert a == b


def test_large_script_performance(parser):
    # 2000-line script parses without error and counts lines correctly.
    s = "#!/bin/bash\n" + "\n".join(f"echo line {i}" for i in range(2000))
    p = parser.parse(s)
    assert p.line_count == 2001
    assert "echo" in p.command_set()
