"""Tests for RQ11 (real third-party benign corpus) and the field-study harness
(Cohen's kappa agreement, LLM-script extraction)."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from experiments.dataset import DATA_DIR

EXTERNAL_MANIFEST = os.path.join(DATA_DIR, "external", "manifest.jsonl")
_HAS_CORPUS = os.path.exists(EXTERNAL_MANIFEST)


# ----------------------- RQ11: external benign corpus ---------------------- #
@pytest.mark.skipif(not _HAS_CORPUS, reason="external corpus not fetched")
def test_external_manifest_is_all_benign():
    with open(EXTERNAL_MANIFEST) as fh:
        rows = [json.loads(l) for l in fh if l.strip()]
    assert rows, "manifest is empty"
    # every committed external script is benign by provenance (label 0)
    assert all(int(r["label"]) == 0 for r in rows)
    # each referenced file exists on disk
    for r in rows:
        assert os.path.exists(os.path.join(DATA_DIR, r["path"])), r["path"]


@pytest.mark.skipif(not _HAS_CORPUS, reason="external corpus not fetched")
def test_evaluate_external_structure_and_baselines():
    from experiments.external_eval import evaluate_external
    res = evaluate_external(epochs=40, seed=1337)
    assert res["available"] is True
    assert res["n_benign"] == res["n_scripts"] > 0
    fp = res["false_positives"]
    # ACTE plus all three learned baselines are reported on identical scripts
    for name in ("ACTE", "TF-IDF + LogReg", "TF-IDF + LinearSVM", "TF-IDF + RandomForest"):
        assert name in fp
        entry = fp[name]
        assert 0 <= entry["count"] <= res["n_benign"]
        assert 0.0 <= entry["fpr"] <= 1.0
        assert set(entry["wilson_ci"]) >= {"low", "high"}
        assert entry["wilson_ci"]["low"] <= entry["wilson_ci"]["high"]
    # honesty note about provenance labelling must be present
    assert "provenance" in res["note"].lower()


@pytest.mark.skipif(not _HAS_CORPUS, reason="external corpus not fetched")
def test_evaluate_external_reports_acte_overflagging_direction():
    # This is the construct-validity finding: on genuinely third-party benign
    # installers ACTE's FPR is materially worse than the lexical baselines'.
    # We assert the *direction* (>=), not a brittle exact value.
    from experiments.external_eval import evaluate_external
    res = evaluate_external(epochs=40, seed=1337)
    fp = res["false_positives"]
    baseline_fprs = [fp[b]["fpr"] for b in fp if b != "ACTE"]
    assert fp["ACTE"]["fpr"] >= max(baseline_fprs)


# ----------------------- Cohen's kappa / agreement ------------------------- #
def test_cohen_kappa_perfect_and_chance():
    from tools.agreement import cohen_kappa
    assert cohen_kappa([0, 1, 0, 1], [0, 1, 0, 1]) == pytest.approx(1.0)
    # total disagreement on a balanced set -> negative kappa
    assert cohen_kappa([0, 0, 1, 1], [1, 1, 0, 0]) < 0.0


def test_cohen_kappa_known_value():
    # a=[1,1,1,0,0,0,0,0,0,0], b=[1,1,0,0,0,0,0,0,0,1]
    # po=0.8, pe=0.3*0.3+0.7*0.7=0.58, kappa=(0.8-0.58)/(1-0.58)=0.5238...
    from tools.agreement import cohen_kappa
    a = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
    b = [1, 1, 0, 0, 0, 0, 0, 0, 0, 1]
    assert cohen_kappa(a, b) == pytest.approx(0.5238, abs=1e-3)


def test_cohen_kappa_constant_raters():
    from tools.agreement import cohen_kappa
    assert cohen_kappa([1, 1, 1], [1, 1, 1]) == 1.0
    assert cohen_kappa([1, 1, 1], [0, 0, 0]) == 0.0


def test_cohen_kappa_length_mismatch_raises():
    from tools.agreement import cohen_kappa
    with pytest.raises(ValueError):
        cohen_kappa([0, 1], [0])


def test_score_files_aligns_by_id(tmp_path):
    from tools.agreement import score_files
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    a.write_text("\n".join(json.dumps({"id": i, "label": v})
                           for i, v in [("s1", 1), ("s2", 0), ("s3", 1), ("only_a", 0)]))
    b.write_text("\n".join(json.dumps({"id": i, "label": v})
                           for i, v in [("s1", 1), ("s2", 0), ("s3", 0), ("only_b", 1)]))
    res = score_files(str(a), str(b))
    assert res["available"] is True
    assert res["n_scored"] == 3            # only shared ids
    assert res["disagreements"] == ["s3"]
    assert res["ids_only_in_a"] == ["only_a"]
    assert res["ids_only_in_b"] == ["only_b"]
    assert 0.0 <= res["raw_agreement"] <= 1.0


# ----------------------- LLM script extraction ----------------------------- #
def test_extract_script_from_fenced_block():
    from tools.collect_llm_scripts import extract_script
    reply = "Sure!\n```bash\n#!/bin/bash\necho hi\n```\nHope that helps."
    assert extract_script(reply) == "#!/bin/bash\necho hi"


def test_extract_script_shebang_fallback():
    from tools.collect_llm_scripts import extract_script
    assert extract_script("#!/bin/sh\nls\n") == "#!/bin/sh\nls"


def test_extract_script_none_when_absent():
    from tools.collect_llm_scripts import extract_script
    assert extract_script("I can't help with that.") is None
