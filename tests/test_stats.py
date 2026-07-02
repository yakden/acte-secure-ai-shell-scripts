"""Statistical helpers: bootstrap CIs and the exact McNemar test."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from experiments.stats import bootstrap_ci, mcnemar, _exact_binomial_two_sided


def test_bootstrap_ci_brackets_point():
    # Perfect classifier: point = 1.0, CI should include 1.0 and stay in [0,1].
    y_true = [0, 0, 0, 1, 1, 1] * 8
    y_pred = list(y_true)
    ci = bootstrap_ci(y_true, y_pred, metrics=["f1", "accuracy"], n_boot=300, seed=1)
    for m in ("f1", "accuracy"):
        assert ci[m]["point"] == pytest.approx(1.0)
        assert 0.0 <= ci[m]["ci_low"] <= ci[m]["ci_high"] <= 1.0
        assert ci[m]["ci_high"] == pytest.approx(1.0)


def test_bootstrap_ci_is_deterministic():
    y_true = [0, 1] * 20
    y_pred = ([0, 1] * 19) + [1, 0]          # inject 2 errors; same length (40)
    assert len(y_true) == len(y_pred)
    a = bootstrap_ci(y_true, y_pred, metrics=["f1"], n_boot=200, seed=7)
    b = bootstrap_ci(y_true, y_pred, metrics=["f1"], n_boot=200, seed=7)
    assert a["f1"] == b["f1"]


def test_bootstrap_ci_width_nonnegative():
    y_true = [0, 0, 1, 1, 0, 1, 0, 1] * 5
    y_pred = [0, 1, 1, 1, 0, 0, 0, 1] * 5
    ci = bootstrap_ci(y_true, y_pred, metrics=["precision", "recall"], n_boot=300, seed=2)
    for m in ("precision", "recall"):
        assert ci[m]["ci_high"] >= ci[m]["ci_low"]


def test_mcnemar_detects_clear_winner():
    # A is right everywhere B is wrong.
    y_true = [1] * 10 + [0] * 10
    pred_a = list(y_true)                      # perfect
    pred_b = [0] * 10 + [1] * 10               # wrong everywhere
    res = mcnemar(y_true, pred_a, pred_b)
    assert res["better_detector"] == "A"
    assert res["a_correct_b_wrong"] == 20
    assert res["b_correct_a_wrong"] == 0
    assert res["p_value"] < 0.05
    assert res["significant_at_0.05"]


def test_mcnemar_tie_not_significant():
    y_true = [1, 0, 1, 0, 1, 0]
    # Both make one (different) error -> discordant 1/1, not significant.
    pred_a = [1, 0, 1, 1, 1, 0]
    pred_b = [0, 0, 1, 0, 1, 0]
    res = mcnemar(y_true, pred_a, pred_b)
    assert res["a_correct_b_wrong"] == 1
    assert res["b_correct_a_wrong"] == 1
    assert res["p_value"] == pytest.approx(1.0)
    assert not res["significant_at_0.05"]


def test_mcnemar_identical_predictions():
    y_true = [1, 0, 1, 0]
    res = mcnemar(y_true, [1, 0, 1, 0], [1, 0, 1, 0])
    assert res["n_discordant"] == 0
    assert res["p_value"] == 1.0
    assert res["better_detector"] == "tie"


def test_exact_binomial_known_values():
    # 0 of 5 one-sided doubled: 2 * (1/32) = 0.0625.
    assert _exact_binomial_two_sided(0, 5) == pytest.approx(0.0625)
    # n == 0 -> p = 1.
    assert _exact_binomial_two_sided(0, 0) == 1.0
    # Capped at 1.0.
    assert _exact_binomial_two_sided(3, 6) == pytest.approx(1.0)
