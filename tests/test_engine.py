"""TrustEvaluationEngine: risk/trust functions, monotonicity, thresholds."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from acte.trust_engine import (
    ALL_FEATURES,
    DEFAULT_WEIGHTS,
    FEATURE_GROUPS,
    TrustEvaluationEngine,
    TrustLevel,
    _sigmoid,
)


@pytest.fixture
def engine():
    return TrustEvaluationEngine()


def test_risk_trust_are_complements(engine):
    a = engine.evaluate_features({k: 0.3 for k in ALL_FEATURES})
    assert a.risk_score + a.trust_score == pytest.approx(1.0, abs=1e-9)


def test_risk_in_open_unit_interval(engine):
    # Features are normalized to [0, 1]; risk stays strictly inside (0, 1).
    for scale in (0.0, 0.25, 0.5, 0.75, 1.0):
        a = engine.evaluate_features({k: scale for k in ALL_FEATURES})
        assert 0.0 < a.risk_score < 1.0


def test_monotonic_in_every_positive_feature(engine):
    base = {k: 0.0 for k in ALL_FEATURES}
    r0 = engine.evaluate_features(dict(base)).risk_score
    for name, w in DEFAULT_WEIGHTS.items():
        if w <= 0:
            continue
        bumped = dict(base)
        bumped[name] = 1.0
        r = engine.evaluate_features(bumped).risk_score
        assert r >= r0 - 1e-12, f"risk decreased when raising {name}"


def test_thresholds_map_to_levels(engine):
    assert engine._risk_to_level(0.10) == TrustLevel.TRUSTED
    assert engine._risk_to_level(0.30) == TrustLevel.MONITOR
    assert engine._risk_to_level(0.60) == TrustLevel.RESTRICT
    assert engine._risk_to_level(0.90) == TrustLevel.DENY


def test_all_zero_is_trusted(engine):
    a = engine.evaluate_features({k: 0.0 for k in ALL_FEATURES})
    assert a.trust_level == TrustLevel.TRUSTED


def test_all_max_is_deny(engine):
    a = engine.evaluate_features({k: 1.0 for k in ALL_FEATURES})
    assert a.trust_level == TrustLevel.DENY


def test_decision_threshold_respected():
    e = TrustEvaluationEngine(decision_threshold=0.5)
    feats = {k: 0.0 for k in ALL_FEATURES}
    feats["threat.weight_norm"] = 1.0
    a = e.evaluate_features(feats)
    assert a.decision_dangerous == (a.risk_score >= 0.5)


def test_ablation_disables_feature_group():
    e = TrustEvaluationEngine(enabled_components={"semantic": True, "context": True, "threat": False})
    feats = {k: 1.0 for k in ALL_FEATURES}
    a = e.evaluate_features(feats)
    # No threat feature may contribute when the group is disabled.
    assert all(k not in a.weighted_contributions for k in FEATURE_GROUPS["threat"])


def test_contributions_sum_to_logit_minus_bias(engine):
    feats = {k: 0.4 for k in ALL_FEATURES}
    a = engine.evaluate_features(feats)
    assert sum(a.weighted_contributions.values()) == pytest.approx(a.logit - engine.bias, abs=1e-9)


def test_sigmoid_numerics():
    assert _sigmoid(0.0) == pytest.approx(0.5)
    assert _sigmoid(1000) == pytest.approx(1.0, abs=1e-9)
    assert _sigmoid(-1000) == pytest.approx(0.0, abs=1e-9)


def test_get_set_params_roundtrip(engine):
    p = engine.get_params()
    engine.set_params({"semantic.pipes_to_shell": 9.9}, bias=-1.0)
    assert engine.weights["semantic.pipes_to_shell"] == 9.9
    assert engine.bias == -1.0
    # Original snapshot unaffected.
    assert p["weights"]["semantic.pipes_to_shell"] != 9.9


def test_to_dict_serializable(engine):
    import json
    a = engine.evaluate_features({k: 0.5 for k in ALL_FEATURES})
    json.dumps(a.to_dict())  # must not raise
