"""RQ11 — false-positive rate on a real, third-party benign corpus.

This is the sharpest external test we can run in an offline sandbox: measure the
false-positive rate of a synthetic-trained, frozen ACTE on the official install
and setup scripts of mainstream open-source projects (``data/external``), which
no one on this project authored. These scripts legitimately use the very idioms
the synthetic corpus penalises — ``curl | bash``, ``sudo``, piping remote
content — so they are the real hard negatives.

The result is reported exactly as measured, favourable or not. We evaluate ACTE
and every learned baseline on the same scripts so the comparison is like-for-like.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List

from experiments.acte_eval import compute_features
from experiments.cluster_bootstrap import wilson_interval
from experiments.dataset import DATA_DIR, Sample, load_samples
from experiments.ml_baselines import _models, _vectorizer
from experiments.online_dynamics import _train_full
from sklearn.pipeline import Pipeline

EXTERNAL_MANIFEST = os.path.join(DATA_DIR, "external", "manifest.jsonl")


def _load_external() -> List[Sample]:
    out: List[Sample] = []
    if not os.path.exists(EXTERNAL_MANIFEST):
        return out
    with open(EXTERNAL_MANIFEST) as fh:
        for line in fh:
            r = json.loads(line)
            p = os.path.join(DATA_DIR, r["path"])
            if not os.path.exists(p):
                continue
            out.append(Sample(r["id"], r["category"], int(r["label"]),
                              r.get("rationale", ""), p, open(p).read(),
                              r.get("template", "external")))
    return out


def evaluate_external(epochs: int = 40, seed: int = 1337) -> Dict:
    ext = _load_external()
    if not ext:
        return {"available": False, "reason": "external corpus not fetched"}

    syn = load_samples()
    n = len(ext)
    y = [s.label for s in ext]  # all 0 (benign) by provenance
    n_neg = sum(1 for v in y if v == 0)

    # ACTE (frozen, trained on full synthetic)
    engine = _train_full(syn, epochs, seed)
    thr = engine.decision_threshold
    feats = compute_features(ext)
    scores = [engine.evaluate_features(f).risk_score for f in feats]
    acte_flagged = [(ext[i].id, round(scores[i], 3)) for i in range(n) if scores[i] >= thr]
    acte_fp = len(acte_flagged)

    detectors = {"ACTE": acte_fp}
    for bname in ("TF-IDF + LogReg", "TF-IDF + LinearSVM", "TF-IDF + RandomForest"):
        pipe = Pipeline([("tfidf", _vectorizer()), ("clf", _models(seed)[bname])])
        pipe.fit([s.script for s in syn], [s.label for s in syn])
        detectors[bname] = int(sum(pipe.predict([s.script for s in ext]).tolist()))

    out = {
        "available": True,
        "n_scripts": n,
        "n_benign": n_neg,
        "decision_threshold": float(thr),
        "false_positives": {k: {"count": v, "fpr": round(v / n_neg, 3),
                                "wilson_ci": wilson_interval(v, n_neg)}
                            for k, v in detectors.items()},
        "acte_flagged": acte_flagged,
        "sources": [{"id": s.id, "provenance": s.rationale} for s in ext],
        "note": ("Benign labels are by provenance (official installers of popular OSS), "
                 "not independent human annotation; a third-party dangerous corpus, real "
                 "LLM outputs, and inter-annotator agreement remain future work."),
    }
    return out
