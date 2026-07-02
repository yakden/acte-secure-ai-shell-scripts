"""Cross-validation: fold integrity, grouping property, and metric sanity."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from experiments.dataset import load_samples
from experiments.cross_validation import (
    grouped_folds,
    run_cross_validation,
    stratified_folds,
)


@pytest.fixture(scope="module")
def samples():
    return load_samples()


def test_stratified_folds_partition(samples):
    folds = stratified_folds(samples, k=5, seed=1337)
    assert len(folds) == 5
    flat = [i for f in folds for i in f]
    assert sorted(flat) == list(range(len(samples)))       # exact partition
    assert len(flat) == len(set(flat))                     # no overlaps


def test_stratified_folds_have_both_classes(samples):
    folds = stratified_folds(samples, k=5, seed=1337)
    for f in folds:
        labels = {samples[i].label for i in f}
        assert labels == {0, 1}, "a fold is missing a class"


def test_grouped_folds_partition(samples):
    folds = grouped_folds(samples, k=5, seed=1337)
    flat = [i for f in folds for i in f]
    assert sorted(flat) == list(range(len(samples)))


def test_grouped_folds_no_template_leakage(samples):
    folds = grouped_folds(samples, k=5, seed=1337)
    fold_templates = []
    for f in folds:
        fold_templates.append({samples[i].template for i in f})
    # No template may appear in more than one fold.
    for i in range(len(fold_templates)):
        for j in range(i + 1, len(fold_templates)):
            assert not (fold_templates[i] & fold_templates[j]), \
                "template leaked across folds"


def test_grouped_folds_have_both_classes(samples):
    folds = grouped_folds(samples, k=5, seed=1337)
    for f in folds:
        labels = {samples[i].label for i in f}
        assert labels == {0, 1}


def test_run_cross_validation_shapes(samples):
    cv = run_cross_validation(samples, k=5, epochs=10, seed=1337)
    for scheme in ("stratified", "grouped_leave_template_out"):
        s = cv[scheme]
        assert len(s["per_fold"]) == 5
        for m in ("f1", "precision", "recall"):
            assert 0.0 <= s["summary"][m]["mean"] <= 1.0
            assert s["summary"][m]["std"] >= 0.0
        # Pooled OOF covers every sample exactly once.
        assert len(s["oof_scores"]) == len(samples)


def test_stratified_beats_grouped_or_close(samples):
    # Generalizing to unseen templates is at least as hard as to unseen samples.
    cv = run_cross_validation(samples, k=5, epochs=20, seed=1337)
    strat = cv["stratified"]["summary"]["f1"]["mean"]
    grouped = cv["grouped_leave_template_out"]["summary"]["f1"]["mean"]
    assert grouped <= strat + 0.05


def test_cross_validation_deterministic(samples):
    a = run_cross_validation(samples, k=5, epochs=10, seed=1337)
    b = run_cross_validation(samples, k=5, epochs=10, seed=1337)
    assert a["stratified"]["summary"]["f1"]["mean"] == \
        b["stratified"]["summary"]["f1"]["mean"]
