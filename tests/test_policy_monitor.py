"""PolicyGenerator + RuntimeMonitor: policy artifacts and enforcement sketch."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from acte.policy_generator import PolicyGenerator
from acte.runtime_monitor import RuntimeMonitor
from acte.trust_engine import ALL_FEATURES, TrustEvaluationEngine, TrustLevel


@pytest.fixture
def gen():
    return PolicyGenerator()


@pytest.fixture
def engine():
    return TrustEvaluationEngine()


def _assess(engine, scale):
    return engine.evaluate_features({k: scale for k in ALL_FEATURES})


def test_policy_generated_for_every_level(gen, engine):
    # Sweep scales to reach each level, assert a coherent policy each time.
    seen = set()
    for scale in (0.0, 0.3, 0.55, 1.0):
        pol = gen.generate(_assess(engine, scale))
        seen.add(pol.trust_level)
        assert "defaultAction" in pol.seccomp_profile
        assert "package acte.execution" in pol.rego_policy
        assert "cgroup" in pol.namespace_constraints
    assert TrustLevel.TRUSTED in seen and TrustLevel.DENY in seen


def test_deny_policy_kills_execution(gen, engine):
    pol = gen.generate(_assess(engine, 1.0))
    assert pol.trust_level == TrustLevel.DENY
    kill_rules = [r for r in pol.seccomp_profile["syscalls"]
                  if r.get("action") == "SCMP_ACT_KILL_PROCESS"]
    assert kill_rules, "DENY must kill execve/fork/clone"


def test_restrict_denies_network(gen, engine):
    pol = gen.generate(_assess(engine, 0.55))
    if pol.trust_level in (TrustLevel.RESTRICT, TrustLevel.DENY):
        assert pol.namespace_constraints["network"] == "deny"
        assert "net" in pol.namespace_constraints["namespaces"]


def test_trusted_allows_network(gen, engine):
    pol = gen.generate(_assess(engine, 0.0))
    assert pol.trust_level == TrustLevel.TRUSTED
    assert pol.namespace_constraints["network"] == "allow"


def test_policy_json_serializable(gen, engine):
    pol = gen.generate(_assess(engine, 1.0))
    json.loads(PolicyGenerator.to_json(pol))  # round-trips


def test_rego_embeds_risk_and_level(gen, engine):
    a = _assess(engine, 1.0)
    pol = gen.generate(a)
    assert a.trust_level.value in pol.rego_policy
    assert f"{a.risk_score:.4f}" in pol.rego_policy


def test_monitor_blocks_network_when_denied(gen, engine):
    pol = gen.generate(_assess(engine, 1.0))
    mon = RuntimeMonitor(pol)
    report = mon.observe(["read", "write", "socket", "connect", "execve"])
    assert report.blocked + report.killed >= 1
    assert report.allowed + report.audited + report.blocked + report.killed == 5


def test_monitor_allows_baseline_syscalls_when_trusted(gen, engine):
    pol = gen.generate(_assess(engine, 0.0))
    mon = RuntimeMonitor(pol)
    report = mon.observe(["read", "write", "close"])
    assert report.blocked == 0 and report.killed == 0


def test_monitor_audit_mode_for_monitor_level(gen, engine):
    pol = gen.generate(_assess(engine, 0.3))
    if pol.trust_level == TrustLevel.MONITOR:
        mon = RuntimeMonitor(pol)
        report = mon.observe(["read", "write"])
        assert report.audited >= 1


def test_monitor_report_counts_consistent(gen, engine):
    pol = gen.generate(_assess(engine, 0.55))
    mon = RuntimeMonitor(pol)
    calls = ["read", "write", "socket", "connect", "execve", "clone", "getrandom"]
    report = mon.observe(calls)
    total = report.allowed + report.audited + report.blocked + report.killed
    assert total == len(calls)
    assert len(report.events) == len(calls)


def test_monitor_explain_is_string(gen, engine):
    pol = gen.generate(_assess(engine, 1.0))
    assert isinstance(RuntimeMonitor(pol).explain(), str)
