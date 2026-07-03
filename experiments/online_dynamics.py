"""RQ9 — does online learning earn its place, and can the feedback loop be poisoned?

Two experiments the reviewer asked for.

Concept drift. The paper claims online adaptation as a selling point but never
shows it buying anything. Here we treat one category (``obfuscated`` — the
evasive family) as a distribution the deployed model has not seen: ACTE is
trained on every other category, and we compare its recall on the novel family
*frozen* versus *after a handful of online SGD updates* on a small labelled
slice of it. If online recovers recall the frozen model lost, the mechanism is
justified; if not, it is not.

Feedback poisoning. A per-example SGD loop is an attack surface: whoever supplies
the MONITOR-tier feedback labels can move the boundary. We measure how many
mislabelled updates it takes to flip a genuinely dangerous canary script from
"dangerous" to "safe," quantifying the loop's fragility.
"""

from __future__ import annotations

from typing import Dict, List

from acte.feedback import FeedbackLearning
from acte.trust_engine import TrustEvaluationEngine
from experiments.acte_eval import compute_features
from experiments.dataset import Sample

_FULL = {"semantic": True, "context": True, "threat": True}


def _train_full(train: List[Sample], epochs: int, seed: int):
    engine = TrustEvaluationEngine()
    feats = compute_features(train)
    learner = FeedbackLearning(engine, learning_rate=0.3, l2=1e-3, seed=seed)
    learner.train(list(zip(feats, [s.label for s in train])), epochs=epochs)
    trs = [engine.evaluate_features(f).risk_score for f in feats]
    learner.tune_threshold(list(zip(trs, [s.label for s in train])), target="f1")
    return engine


def _recall_dangerous(engine, samples: List[Sample]) -> float:
    thr = engine.decision_threshold
    dang = [s for s in samples if s.label == 1]
    if not dang:
        return 0.0
    feats = compute_features(dang)
    hit = sum(1 for f in feats if engine.evaluate_features(f).risk_score >= thr)
    return hit / len(dang)


def concept_drift(samples: List[Sample], epochs: int = 40, seed: int = 1337,
                  drift_category: str = "obfuscated") -> Dict:
    base = [s for s in samples if s.category != drift_category]
    drift = [s for s in samples if s.category == drift_category and s.label == 1]
    # deterministic split of the novel family into adapt / eval halves
    drift = sorted(drift, key=lambda s: s.id)
    adapt = drift[::2]
    hold = drift[1::2]

    engine = _train_full(base, epochs, seed)
    frozen_recall = _recall_dangerous(engine, hold)

    # online: a few passes of single-example updates on the adapt slice only
    learner = FeedbackLearning(engine, learning_rate=0.3, l2=1e-3, seed=seed)
    adapt_feats = compute_features(adapt)
    for _ in range(5):
        for f in adapt_feats:
            learner.update_one(f, 1)
    online_recall = _recall_dangerous(engine, hold)

    return {
        "drift_category": drift_category,
        "n_base_train": len(base),
        "n_adapt": len(adapt),
        "n_eval": len(hold),
        "frozen_recall_on_novel": round(frozen_recall, 3),
        "online_recall_on_novel": round(online_recall, 3),
        "recall_recovered": round(online_recall - frozen_recall, 3),
    }


def feedback_poisoning(train: List[Sample], test: List[Sample],
                       epochs: int = 40, seed: int = 1337) -> Dict:
    engine = _train_full(train, epochs, seed)
    thr = engine.decision_threshold

    # canary: the highest-risk dangerous test script
    dang = [s for s in test if s.label == 1]
    feats = compute_features(dang)
    scored = sorted(zip(dang, feats),
                    key=lambda p: engine.evaluate_features(p[1]).risk_score, reverse=True)
    canary, canary_feat = scored[0]
    start_risk = engine.evaluate_features(canary_feat).risk_score

    # attacker feeds the canary's own features labelled "safe" (0)
    learner = FeedbackLearning(engine, learning_rate=0.3, l2=1e-3, seed=seed)
    flips_at = None
    trajectory = []
    for k in range(1, 51):
        learner.update_one(canary_feat, 0)
        r = engine.evaluate_features(canary_feat).risk_score
        trajectory.append(round(r, 3))
        if flips_at is None and r < thr:
            flips_at = k
            break

    return {
        "threshold": round(thr, 3),
        "canary_id": canary.id,
        "canary_start_risk": round(start_risk, 3),
        "poisoned_labels_to_flip": flips_at,
        "risk_trajectory": trajectory,
        "note": ("A small number of attacker-controlled 'safe' feedback labels on a "
                 "dangerous script suffices to flip its decision; the online loop needs "
                 "authenticated, rate-limited, multi-party feedback in deployment."),
    }
