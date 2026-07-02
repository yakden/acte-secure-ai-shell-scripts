"""RQ4 — generalization to real, non-synthetic scripts (external validation).

Protocol
--------
1. Train the ACTE full model on the **entire** synthetic corpus (all 420
   samples): run feedback learning, then tune the decision threshold — both on
   synthetic data only.
2. Freeze the model. Evaluate it, exactly once, on the hand-authored
   ``data/real_world`` holdout (see ``data/real_world/build.py``). None of these
   scripts were seen during training or threshold tuning.

Because training and evaluation come from independent script populations, the
resulting metrics measure true generalization — not memorization of the
generating templates. A per-script table is emitted so every decision (and
especially the deliberately hard cases) is auditable.
"""

from __future__ import annotations

import os
from typing import Dict, List

from acte.feedback import FeedbackLearning
from acte.trust_engine import TrustEvaluationEngine
from experiments.acte_eval import compute_features
from experiments.dataset import REAL_WORLD_MANIFEST, Sample, load_samples
from experiments.metrics import classification_metrics
from experiments.stats import bootstrap_ci


def _train_on_all(
    train: List[Sample], train_feats: List[Dict[str, float]],
    epochs: int, seed: int,
) -> TrustEvaluationEngine:
    engine = TrustEvaluationEngine(
        enabled_components={"semantic": True, "context": True, "threat": True}
    )
    learner = FeedbackLearning(engine, learning_rate=0.3, l2=1e-3, seed=seed)
    learner.train(list(zip(train_feats, [s.label for s in train])), epochs=epochs)
    train_scores = [engine.evaluate_features(f).risk_score for f in train_feats]
    learner.tune_threshold(
        list(zip(train_scores, [s.label for s in train])), target="f1"
    )
    return engine


def evaluate_real_world(epochs: int = 40, seed: int = 1337) -> Dict:
    """Train on all synthetic data; evaluate on the real-world holdout."""
    if not os.path.exists(REAL_WORLD_MANIFEST):
        return {"available": False,
                "reason": "real-world manifest not found; run data.real_world.build"}

    synthetic = load_samples()                       # full synthetic corpus
    real = load_samples(REAL_WORLD_MANIFEST)         # external holdout

    syn_feats = compute_features(synthetic)
    engine = _train_on_all(synthetic, syn_feats, epochs=epochs, seed=seed)
    thr = engine.decision_threshold

    real_feats = compute_features(real)
    scores = [engine.evaluate_features(f).risk_score for f in real_feats]
    pred = [1 if s >= thr else 0 for s in scores]
    y_true = [s.label for s in real]

    metrics = classification_metrics(y_true, pred, scores)
    metrics["decision_threshold"] = float(thr)

    ci = bootstrap_ci(y_true, pred, scores,
                      metrics=["precision", "recall", "f1", "accuracy"],
                      n_boot=2000, seed=seed)

    per_script = []
    for s, sc, p in zip(real, scores, pred):
        per_script.append({
            "id": s.id,
            "category": s.category,
            "label": s.label,
            "risk_score": float(sc),
            "predicted": p,
            "correct": bool(p == s.label),
            "rationale": s.rationale,
        })

    errors = [r for r in per_script if not r["correct"]]
    return {
        "available": True,
        "n_scripts": len(real),
        "n_dangerous": int(sum(y_true)),
        "n_safe": int(len(y_true) - sum(y_true)),
        "trained_on": "full synthetic corpus (%d samples)" % len(synthetic),
        "decision_threshold": float(thr),
        "metrics": metrics,
        "bootstrap_ci": ci,
        "per_script": per_script,
        "errors": errors,
    }
