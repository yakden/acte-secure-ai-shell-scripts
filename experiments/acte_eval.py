"""Train and evaluate ACTE, including the component ablation study.

Protocol
--------
1. Compute the full feature vector for every sample once (with all components
   active). Feature extraction is deterministic.
2. The ACTE model starts from auditable hand-set default weights. The
   FeedbackLearning module then performs logistic SGD on the **train** split
   only, and tunes the decision threshold on the train split.
3. The trained model is evaluated on the held-out **test** split. Continuous
   risk scores are kept for ROC / PR analysis.

Ablation
--------
Each ablated configuration is trained and evaluated with exactly the same
protocol so the comparison is fair:
* ``no_semantic`` / ``no_context`` / ``no_threat`` mask that feature group to
  zero (the component contributes nothing), then re-train feedback.
* ``no_feedback`` keeps all features but skips learning (cold-start default
  weights, fixed 0.5 threshold), isolating the contribution of online learning.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from acte.trust_engine import TrustEvaluationEngine, FEATURE_GROUPS
from acte.feedback import FeedbackLearning
from acte.pipeline import ACTEPipeline
from experiments.dataset import Sample
from experiments.metrics import classification_metrics, per_category_recall


def compute_features(samples: List[Sample]) -> List[Dict[str, float]]:
    """Compute the full ACTE feature vector for each sample (all components on)."""
    pipeline = ACTEPipeline(engine=TrustEvaluationEngine())
    return [pipeline.features_for(s.script) for s in samples]


def _score(engine: TrustEvaluationEngine, feats: Dict[str, float]) -> float:
    return engine.evaluate_features(feats).risk_score


def train_and_eval(
    train: List[Sample],
    test: List[Sample],
    train_feats: List[Dict[str, float]],
    test_feats: List[Dict[str, float]],
    enabled_components: Dict[str, bool],
    use_feedback: bool,
    epochs: int = 40,
    seed: int = 1337,
    tune_threshold: bool = True,
) -> Tuple[Dict, List[float], List[int], object]:
    """Train (optionally) and evaluate one configuration.

    Returns (metrics_dict, test_scores, test_predictions, engine).
    """
    engine = TrustEvaluationEngine(enabled_components=enabled_components)

    train_stats = None
    if use_feedback:
        learner = FeedbackLearning(engine, learning_rate=0.3, l2=1e-3, seed=seed)
        dataset = list(zip(train_feats, [s.label for s in train]))
        train_stats = learner.train(dataset, epochs=epochs)
        if tune_threshold:
            train_scores = [_score(engine, f) for f in train_feats]
            learner.tune_threshold(
                list(zip(train_scores, [s.label for s in train])), target="f1"
            )

    test_scores = [_score(engine, f) for f in test_feats]
    thr = engine.decision_threshold
    test_pred = [1 if s >= thr else 0 for s in test_scores]
    y_true = [s.label for s in test]

    metrics = classification_metrics(y_true, test_pred, test_scores)
    metrics["decision_threshold"] = float(thr)
    if train_stats is not None:
        metrics["training"] = {
            "epochs": train_stats.epochs,
            "final_loss": train_stats.final_loss,
            "initial_loss": train_stats.loss_history[0] if train_stats.loss_history else None,
            "weight_delta_norm": train_stats.weight_delta_norm,
        }
    return metrics, test_scores, test_pred, engine


def run_full_and_ablation(
    train: List[Sample],
    test: List[Sample],
    epochs: int = 40,
    seed: int = 1337,
) -> Dict:
    """Run the full ACTE model plus the four ablations; return everything."""
    train_feats = compute_features(train)
    test_feats = compute_features(test)

    configs = [
        ("full", {"semantic": True, "context": True, "threat": True}, True),
        ("no_semantic", {"semantic": False, "context": True, "threat": True}, True),
        ("no_context", {"semantic": True, "context": False, "threat": True}, True),
        ("no_threat", {"semantic": True, "context": True, "threat": False}, True),
        ("no_feedback", {"semantic": True, "context": True, "threat": True}, False),
    ]

    results: Dict[str, Dict] = {}
    full_scores: List[float] = []
    full_pred: List[int] = []
    for name, comps, use_fb in configs:
        metrics, scores, pred, _ = train_and_eval(
            train, test, train_feats, test_feats,
            enabled_components=comps, use_feedback=use_fb,
            epochs=epochs, seed=seed,
        )
        results[name] = metrics
        if name == "full":
            full_scores = scores
            full_pred = pred

    return {
        "configs": results,
        "full_test_scores": full_scores,
        "full_test_pred": full_pred,
        "full_per_category": per_category_recall(test, full_pred),
        "feature_groups": FEATURE_GROUPS,
    }
