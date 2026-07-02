"""Learned text-classifier baselines (RQ5): sanity, determinism, and shape."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from experiments.dataset import REAL_WORLD_MANIFEST, load_samples, stratified_split
from experiments.ml_baselines import evaluate_baselines


@pytest.fixture(scope="module")
def result():
    samples = load_samples()
    train, test = stratified_split(samples, 0.4, seed=1337)
    real = load_samples(REAL_WORLD_MANIFEST)
    return evaluate_baselines(train, test, real, seed=1337)


def test_all_baselines_present(result):
    for scheme in ("on_synthetic_test", "on_real_world"):
        names = set(result[scheme])
        assert {"TF-IDF + LogReg", "TF-IDF + LinearSVM", "TF-IDF + RandomForest"} <= names


def test_baselines_beat_chance(result):
    for name, m in result["on_synthetic_test"].items():
        assert m["f1"] > 0.6, f"{name} suspiciously weak on synthetic test"
        assert 0.0 <= m["false_positive_rate"] <= 1.0


def test_metrics_well_formed(result):
    for scheme in ("on_synthetic_test", "on_real_world"):
        for name, m in result[scheme].items():
            for k in ("precision", "recall", "f1"):
                assert 0.0 <= m[k] <= 1.0, (scheme, name, k)


def test_deterministic(result):
    samples = load_samples()
    train, test = stratified_split(samples, 0.4, seed=1337)
    real = load_samples(REAL_WORLD_MANIFEST)
    again = evaluate_baselines(train, test, real, seed=1337)
    for name in result["on_synthetic_test"]:
        assert again["on_synthetic_test"][name]["f1"] == \
            pytest.approx(result["on_synthetic_test"][name]["f1"])
