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
    """Assign each sample to one of ``k`` folds, stratified by (category,label).

    Returns a list of ``k`` index lists into ``samples``.
    """
    import random

    rng = random.Random(seed)
    buckets: Dict[Tuple[str, int], List[int]] = {}
    for i, s in enumerate(samples):
        buckets.setdefault((s.category, s.label), []).append(i)

    folds: List[List[int]] = [[] for _ in range(k)]
    for key in sorted(buckets.keys()):
        idxs = sorted(buckets[key])
        rng.shuffle(idxs)
        # Round-robin the shuffled bucket across folds -> balanced strata.
        for pos, idx in enumerate(idxs):
            folds[pos % k].append(idx)
    for f in folds:
        f.sort()
    return folds


def grouped_folds(
    samples: List[Sample], k: int = 5, seed: int = 1337
) -> List[List[int]]:
    """Assign folds by generating template so a template never spans folds.

    Templates are greedily packed into ``k`` folds while keeping the number of
    dangerous samples roughly balanced, so every fold still contains both
    classes (a requirement for ROC/PR and MCC to be defined).
    """
    import random

    rng = random.Random(seed)
    groups: Dict[str, List[int]] = {}
    for i, s in enumerate(samples):
        groups.setdefault(s.template, []).append(i)

    # Order groups by size (largest first) for a stable, balanced greedy fill.
    ordered = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    rng.shuffle(ordered)  # break size ties deterministically-at-seed
    ordered.sort(key=lambda kv: -len(kv[1]))

    folds: List[List[int]] = [[] for _ in range(k)]
    fold_pos = [0] * k      # count of dangerous samples per fold (balance target)
    for _tpl, idxs in ordered:
        n_pos = sum(samples[i].label for i in idxs)
        # Put this group in whichever fold currently has the fewest positives
        # (ties -> smallest fold), keeping both size and class balance even.
        target = min(range(k), key=lambda j: (fold_pos[j], len(folds[j])))
        folds[target].extend(idxs)
        fold_pos[target] += n_pos
    for f in folds:
        f.sort()
    return folds


# --------------------------------------------------------------------------- #
# Cross-validation driver                                                     #
# --------------------------------------------------------------------------- #
def _run_cv(
    samples: List[Sample],
    feats: List[Dict[str, float]],
    folds: List[List[int]],
    epochs: int,
    seed: int,
) -> Dict:
    """Train/evaluate the full model once per fold; aggregate the results."""
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
            epochs=epochs, seed=seed,
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
    samples: List[Sample], k: int = 5, epochs: int = 40, seed: int = 1337
) -> Dict:
    """Run both stratified and grouped (leave-template-out) k-fold CV."""
    feats = compute_features(samples)
    strat = _run_cv(samples, feats, stratified_folds(samples, k, seed), epochs, seed)
    grouped = _run_cv(samples, feats, grouped_folds(samples, k, seed), epochs, seed)

    n_templates = len({s.template for s in samples})
    return {
        "stratified": strat,
        "grouped_leave_template_out": grouped,
        "n_samples": len(samples),
        "n_templates": n_templates,
        "seed": seed,
    }
