"""Cross-validation for ACTE — the rigorous replacement for a single split.

A single held-out split (however carefully stratified) reports one number and
gives no sense of how much that number would move under a different partition.
This module runs the full ACTE protocol (train feedback + tune threshold on the
training folds, evaluate on the held-out fold) inside two cross-validation
schemes and reports **mean ± standard deviation** across folds, so every
headline metric comes with a spread rather than a single point estimate.

Two schemes, answering two different questions:

* **Stratified k-fold** (``stratified_cv``) — folds are stratified by
  ``(category, label)`` so class balance is preserved. This estimates
  generalization to *new samples drawn from the same distribution*.

* **Grouped leave-template-out k-fold** (``grouped_cv``) — folds are split by
  the *generating template*, so no script produced by a template ever appears
  in both the training and the evaluation fold. This is the harder, more honest
  test: it estimates generalization to *scripts whose structure the model has
  not seen during training*, and it rules out the "template memorization"
  objection to synthetic corpora.

Everything is seeded; re-running reproduces identical folds and metrics.
"""

from __future__ import annotations

import statistics
from typing import Dict, List, Tuple

from experiments.acte_eval import compute_features, train_and_eval
from experiments.dataset import Sample
from experiments.metrics import classification_metrics

# Metrics we summarize across folds.
_SUMMARY_KEYS = [
    "precision", "recall", "f1", "mcc", "accuracy",
    "false_positive_rate", "false_negative_rate", "roc_auc", "pr_auc",
]

_FULL_COMPONENTS = {"semantic": True, "context": True, "threat": True}


# --------------------------------------------------------------------------- #
# Fold construction                                                           #
# --------------------------------------------------------------------------- #
def stratified_folds(
    samples: List[Sample], k: int = 5, seed: int = 1337
) -> List[List[int]]:
    """Assign each sample to one of ``k`` folds, stratified by label.

    Uses scikit-learn's :class:`StratifiedKFold` so every fold preserves the
    positive/negative ratio of the full corpus. Returns ``k`` index lists.
    """
    from sklearn.model_selection import StratifiedKFold

    y = [s.label for s in samples]
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    dummy = [[0]] * len(samples)
    return [sorted(test_idx.tolist()) for _, test_idx in skf.split(dummy, y)]


def grouped_folds(
    samples: List[Sample], k: int = 5, seed: int = 1337
) -> List[List[int]]:
    """Assign folds by generating template, stratified on label.

    Uses scikit-learn's :class:`StratifiedGroupKFold`, which keeps every
    template (the group) wholly inside one fold *and* balances the label
    distribution across folds. This avoids the near-single-class folds that a
    naive greedy grouping produces (and that would make per-fold precision/FPR
    meaningless), while still guaranteeing no template spans train and test.
    """
    from sklearn.model_selection import StratifiedGroupKFold

    y = [s.label for s in samples]
    groups = [s.template for s in samples]
    sgkf = StratifiedGroupKFold(n_splits=k, shuffle=True, random_state=seed)
    dummy = [[0]] * len(samples)
    return [sorted(test_idx.tolist()) for _, test_idx in sgkf.split(dummy, y, groups)]


# --------------------------------------------------------------------------- #
# Cross-validation driver                                                     #
# --------------------------------------------------------------------------- #
def _run_cv(
    samples: List[Sample],
    feats: List[Dict[str, float]],
    folds: List[List[int]],
    epochs: int,
    seed: int,
    tune_threshold: bool = False,
) -> Dict:
    """Train/evaluate the full model once per fold; aggregate the results.

    ``tune_threshold`` defaults to False: each fold uses the model's fixed
    default operating point (:math:`\\tau=0.5`). Tuning an F1-optimal threshold
    on the small, per-fold training partitions is a known variance amplifier and
    makes the cross-validated spread reflect threshold noise rather than model
    stability, so the conservative fixed-threshold estimate is reported instead.
    """
    per_fold: List[Dict] = []
    oof_scores: List[float] = [0.0] * len(samples)   # out-of-fold risk scores
    oof_pred: List[int] = [0] * len(samples)
    oof_true: List[int] = [0] * len(samples)
    oof_mask: List[bool] = [False] * len(samples)

    for fold_id, test_idx in enumerate(folds):
        test_set = set(test_idx)
        train_idx = [i for i in range(len(samples)) if i not in test_set]

        train = [samples[i] for i in train_idx]
        test = [samples[i] for i in test_idx]
        train_feats = [feats[i] for i in train_idx]
        test_feats = [feats[i] for i in test_idx]

        metrics, scores, pred, _ = train_and_eval(
            train, test, train_feats, test_feats,
            enabled_components=dict(_FULL_COMPONENTS), use_feedback=True,
            epochs=epochs, seed=seed, tune_threshold=tune_threshold,
        )
        metrics["fold"] = fold_id
        metrics["n_test"] = len(test)
        per_fold.append(metrics)

        for local, gi in enumerate(test_idx):
            oof_scores[gi] = scores[local]
            oof_pred[gi] = pred[local]
            oof_true[gi] = samples[gi].label
            oof_mask[gi] = True

    summary = _summarize(per_fold)
    # Pooled out-of-fold metrics: every sample is scored exactly once, by a
    # model that never saw it, so this is a single honest confusion matrix.
    pooled = classification_metrics(oof_true, oof_pred, oof_scores)
    return {
        "k": len(folds),
        "epochs": epochs,
        "per_fold": per_fold,
        "summary": summary,
        "pooled_oof": pooled,
        "oof_scores": oof_scores,
        "oof_true": oof_true,
        "oof_pred": oof_pred,
    }


def _summarize(per_fold: List[Dict]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for key in _SUMMARY_KEYS:
        vals = [m[key] for m in per_fold if m.get(key) is not None]
        if not vals:
            continue
        out[key] = {
            "mean": float(statistics.fmean(vals)),
            "std": float(statistics.pstdev(vals)) if len(vals) > 1 else 0.0,
            "min": float(min(vals)),
            "max": float(max(vals)),
            "values": [float(v) for v in vals],
        }
    return out


def run_cross_validation(
    samples: List[Sample], k: int = 5, epochs: int = 40, seed: int = 1337,
    tune_threshold: bool = False,
) -> Dict:
    """Run both stratified and grouped (leave-template-out) k-fold CV.

    Feature extraction is deterministic and label-independent, so computing it
    once over the whole corpus before splitting introduces no train/test
    leakage; feedback learning (and optional threshold tuning) still happens on
    the training folds only.
    """
    feats = compute_features(samples)
    strat = _run_cv(samples, feats, stratified_folds(samples, k, seed), epochs, seed,
                    tune_threshold=tune_threshold)
    grouped = _run_cv(samples, feats, grouped_folds(samples, k, seed), epochs, seed,
                      tune_threshold=tune_threshold)

    n_templates = len({s.template for s in samples})
    return {
        "stratified": strat,
        "grouped_leave_template_out": grouped,
        "n_samples": len(samples),
        "n_templates": n_templates,
        "seed": seed,
    }
