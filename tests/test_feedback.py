"""FeedbackLearning: SGD update rule, convergence, and threshold tuning."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from acte.feedback import FeedbackLearning, _bce, _Lcg
from acte.trust_engine import ALL_FEATURES, TrustEvaluationEngine


def _feats(**kw):
    f = {k: 0.0 for k in ALL_FEATURES}
    f.update(kw)
    return f


def test_single_step_returns_loss_and_moves_bias():
    e = TrustEvaluationEngine()
    learner = FeedbackLearning(e, learning_rate=0.5)
    b0 = e.bias
    loss = learner.update_one(_feats(**{"threat.weight_norm": 1.0}), label=1)
    assert loss > 0
    assert e.bias != b0  # error != 0 so bias updates


def test_training_reduces_loss_on_separable_data():
    e = TrustEvaluationEngine()
    learner = FeedbackLearning(e, learning_rate=0.4, seed=1)
    safe = _feats()
    danger = _feats(**{"threat.weight_norm": 1.0, "context.irreversibility": 1.0})
    stats = learner.train([(safe, 0), (danger, 1)] * 25, epochs=15)
    assert stats.loss_history[0] > stats.loss_history[-1]
    assert stats.weight_delta_norm > 0


def test_training_keeps_decision_direction():
    e = TrustEvaluationEngine()
    learner = FeedbackLearning(e, learning_rate=0.5, seed=2)
    safe = _feats()
    danger = _feats(**{"threat.weight_norm": 1.0})
    learner.train([(safe, 0), (danger, 1)] * 20, epochs=10)
    assert e.evaluate_features(danger).risk_score > e.evaluate_features(safe).risk_score


def test_l2_penalty_effect_is_applied():
    # With a huge L2, weights should be pulled toward small magnitudes over time.
    e = TrustEvaluationEngine()
    start = dict(e.weights)
    learner = FeedbackLearning(e, learning_rate=0.1, l2=0.5, seed=3)
    learner.train([(_feats(), 0)] * 30, epochs=20)
    # At least one weight moved (regularization + gradient acted).
    assert any(abs(e.weights[k] - start[k]) > 1e-6 for k in e.weights)


def test_threshold_tuning_prefers_separating_point():
    e = TrustEvaluationEngine()
    learner = FeedbackLearning(e)
    thr = learner.tune_threshold([(0.1, 0), (0.2, 0), (0.8, 1), (0.9, 1)], target="f1")
    assert 0.2 < thr <= 0.8
    assert e.decision_threshold == thr


def test_threshold_tuning_min_fp_respects_fpr_cap():
    e = TrustEvaluationEngine()
    learner = FeedbackLearning(e)
    scored = [(0.1, 0), (0.4, 0), (0.45, 0), (0.6, 1), (0.7, 1), (0.9, 1)]
    thr = learner.tune_threshold(scored, target="min_fp", max_fpr=0.0)
    # With zero tolerated FPR, threshold must exclude all negatives.
    fp = sum(1 for s, y in scored if s >= thr and y == 0)
    assert fp == 0


def test_bce_bounds():
    assert _bce(0.5, 1) == pytest.approx(0.6931, abs=1e-3)
    assert _bce(1.0, 1) < 1e-6
    assert _bce(0.0, 1) > 10  # clamped, large but finite


def test_lcg_shuffle_is_deterministic():
    a = list(range(20))
    b = list(range(20))
    _Lcg(123).shuffle(a)
    _Lcg(123).shuffle(b)
    assert a == b
    assert sorted(a) == list(range(20))  # permutation preserved


def test_ablation_group_frozen_during_training():
    # A disabled group's weights must not be updated by SGD.
    e = TrustEvaluationEngine(enabled_components={"semantic": False, "context": True, "threat": True})
    frozen = {k: e.weights[k] for k in e.weights if k.startswith("semantic.")}
    learner = FeedbackLearning(e, learning_rate=0.5, seed=4)
    learner.train([(_feats(**{"semantic.pipes_to_shell": 1.0, "threat.weight_norm": 1.0}), 1)] * 20, epochs=10)
    for k, v in frozen.items():
        assert e.weights[k] == v, f"disabled feature {k} was updated"
