"""RQ4 external validation: train on synthetic, evaluate on real scripts."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from data.real_world import build as real_world_build
from experiments.real_world_eval import evaluate_real_world


@pytest.fixture(scope="module")
def result():
    real_world_build.build(verbose=False)
    return evaluate_real_world(epochs=40, seed=1337)


def test_available(result):
    assert result["available"]
    assert result["n_scripts"] == result["n_dangerous"] + result["n_safe"]


def test_generalizes_above_chance(result):
    m = result["metrics"]
    # A trained-on-synthetic model must clearly beat chance on real scripts.
    assert m["f1"] > 0.7
    assert m["roc_auc"] > 0.8


def test_precision_high_on_real_world(result):
    # Low false-positive rate is ACTE's headline property; hold it on real data.
    assert result["metrics"]["false_positive_rate"] <= 0.1


def test_per_script_table_complete(result):
    ps = result["per_script"]
    assert len(ps) == result["n_scripts"]
    for row in ps:
        assert set(row) >= {"id", "label", "risk_score", "predicted", "correct"}
        assert row["correct"] == (row["predicted"] == row["label"])


def test_errors_are_subset_of_per_script(result):
    err_ids = {e["id"] for e in result["errors"]}
    all_ids = {r["id"] for r in result["per_script"]}
    assert err_ids <= all_ids
    # Every listed error is genuinely a misclassification.
    for e in result["errors"]:
        assert e["predicted"] != e["label"]


def test_deterministic(result):
    again = evaluate_real_world(epochs=40, seed=1337)
    assert again["metrics"]["f1"] == pytest.approx(result["metrics"]["f1"])


def test_bootstrap_ci_present(result):
    assert "f1" in result["bootstrap_ci"]
    ci = result["bootstrap_ci"]["f1"]
    assert ci["ci_low"] <= ci["point"] <= ci["ci_high"]
