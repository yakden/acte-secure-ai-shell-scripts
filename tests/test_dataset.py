"""Dataset integrity, reproducibility, and the real-world holdout."""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from data import generate_dataset
from data.real_world import build as real_world_build
from experiments.dataset import (
    REAL_WORLD_OK,
    load_samples,
    stratified_split,
    split_summary,
)


@pytest.fixture(scope="module")
def samples():
    return load_samples()


def test_manifest_matches_files(samples):
    assert len(samples) == 420
    for s in samples:
        assert os.path.exists(s.path), s.path
        assert s.label in (0, 1)
        assert s.template  # template id recorded for grouped CV


def test_script_bodies_nonempty(samples):
    assert all(s.script.strip() for s in samples)


def test_manifest_label_consistency():
    # Every manifest row's label_name must agree with its numeric label.
    manifest = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "data", "manifest.jsonl")
    with open(manifest) as fh:
        for line in fh:
            rec = json.loads(line)
            expected = "dangerous" if rec["label"] == 1 else "safe"
            assert rec["label_name"] == expected, rec["id"]


def test_generation_is_byte_reproducible(tmp_path):
    # Regenerate and confirm the manifest hash is stable across two runs.
    def manifest_hash():
        generate_dataset.generate(verbose=False)
        with open(generate_dataset.MANIFEST_JSONL, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    assert manifest_hash() == manifest_hash()


def test_categories_present(samples):
    cats = {s.category for s in samples}
    assert cats == {"safe_everyday", "malicious", "ai_generated", "obfuscated", "sysadmin"}


def test_both_classes_present(samples):
    labels = {s.label for s in samples}
    assert labels == {0, 1}


def test_stratified_split_disjoint_and_covers(samples):
    train, test = stratified_split(samples, test_fraction=0.4, seed=1337)
    train_ids = {s.id for s in train}
    test_ids = {s.id for s in test}
    assert not (train_ids & test_ids)
    assert len(train_ids | test_ids) == len(samples)


def test_split_summary_counts(samples):
    train, test = stratified_split(samples, test_fraction=0.4, seed=1337)
    summ = split_summary(train, test)
    assert summ["n_train"] + summ["n_test"] == len(samples)
    assert summ["test_positives"] == sum(s.label for s in test)


def test_split_is_deterministic(samples):
    a = stratified_split(samples, 0.4, seed=1337)[1]
    b = stratified_split(samples, 0.4, seed=1337)[1]
    assert [s.id for s in a] == [s.id for s in b]


# ---------------------------- real-world holdout --------------------------- #
def test_real_world_builds_and_loads():
    real_world_build.build(verbose=False)
    assert REAL_WORLD_OK
    real = load_samples(_real_world_manifest())
    assert len(real) >= 30
    assert {s.label for s in real} == {0, 1}
    for s in real:
        assert os.path.exists(s.path)


def test_real_world_disjoint_from_synthetic(samples):
    real = load_samples(_real_world_manifest())
    syn_scripts = {s.script for s in samples}
    # No byte-identical overlap ...
    overlap = [s.id for s in real if s.script in syn_scripts]
    assert overlap == [], f"real-world scripts duplicate synthetic ones: {overlap}"


def test_real_world_not_near_duplicate_of_training(samples):
    # ... and no *near*-duplicate either: a truly independent holdout must not
    # contain a script that is a trivial edit of a training sample. We cap the
    # max sequence similarity to any training script well below 1.0.
    import difflib
    real = load_samples(_real_world_manifest())
    offenders = []
    for r in real:
        best = max(difflib.SequenceMatcher(None, r.script, s.script).ratio()
                   for s in samples)
        if best >= 0.85:
            offenders.append((r.id, round(best, 2)))
    assert offenders == [], f"real-world scripts too similar to training: {offenders}"


def _real_world_manifest():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "real_world", "manifest.jsonl")
