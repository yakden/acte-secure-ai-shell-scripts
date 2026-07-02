"""Statistical rigor for the ACTE evaluation: confidence intervals + tests.

Point estimates alone (``F1 = 0.915``) do not tell a reader whether a
difference is real or noise. This module adds two standard, well-understood
tools:

* **Bootstrap confidence intervals** (``bootstrap_ci``) — resample the test set
  with replacement ``B`` times, recompute a metric on each resample, and report
  the 2.5th / 97.5th percentiles as a 95% CI. This quantifies how much each
  headline metric would move under sampling variation, without any parametric
  assumption about the metric's distribution.

* **McNemar's test** (``mcnemar``) — the correct paired test for comparing two
  classifiers on the *same* test items. It looks only at the items the two
  detectors disagree on (the discordant pairs ``b`` and ``c``) and asks whether
  that disagreement is one-sided beyond chance. We use the exact binomial form,
  which is valid for the small discordant counts typical here (no large-sample
  chi-square approximation required).

Both are deterministic given the seed, so the reported intervals reproduce.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

import numpy as np

from experiments.metrics import classification_metrics


def _metric_fn(name: str) -> Callable[[List[int], List[int], Optional[List[float]]], float]:
    def fn(yt, yp, ys):
        m = classification_metrics(yt, yp, ys)
        return float(m.get(name, 0.0))
    return fn


def bootstrap_ci(
    y_true: List[int],
    y_pred: List[int],
    y_score: Optional[List[float]] = None,
    metrics: Optional[List[str]] = None,
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 1337,
) -> Dict[str, Dict[str, float]]:
    """Percentile bootstrap 95% CIs for a bundle of classification metrics.

    Resampling is stratified within the positive and negative classes so that
    every bootstrap replicate keeps both classes present (otherwise AUC/MCC are
    undefined on degenerate resamples).
    """
    metrics = metrics or ["precision", "recall", "f1", "mcc",
                          "accuracy", "false_positive_rate", "roc_auc", "pr_auc"]
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have equal length")
    if y_score is not None and len(y_score) != len(y_true):
        raise ValueError("y_score must match y_true length")
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    y_score = np.asarray(y_score) if y_score is not None else None

    pos_idx = np.where(y_true == 1)[0]
    neg_idx = np.where(y_true == 0)[0]
    rng = np.random.default_rng(seed)

    samples: Dict[str, List[float]] = {m: [] for m in metrics}
    for _ in range(n_boot):
        bp = rng.choice(pos_idx, size=len(pos_idx), replace=True)
        bn = rng.choice(neg_idx, size=len(neg_idx), replace=True)
        idx = np.concatenate([bp, bn])
        yt = y_true[idx].tolist()
        yp = y_pred[idx].tolist()
        ys = y_score[idx].tolist() if y_score is not None else None
        m = classification_metrics(yt, yp, ys)
        for name in metrics:
            v = m.get(name)
            if v is not None:
                samples[name].append(float(v))

    lo_p, hi_p = 100 * (alpha / 2), 100 * (1 - alpha / 2)
    point = classification_metrics(y_true.tolist(), y_pred.tolist(),
                                   y_score.tolist() if y_score is not None else None)
    out: Dict[str, Dict[str, float]] = {}
    for name in metrics:
        vals = samples[name]
        if not vals:
            continue
        out[name] = {
            "point": float(point.get(name, 0.0)),
            "ci_low": float(np.percentile(vals, lo_p)),
            "ci_high": float(np.percentile(vals, hi_p)),
            "n_boot": len(vals),
        }
    return out


def mcnemar(
    y_true: List[int], pred_a: List[int], pred_b: List[int]
) -> Dict[str, float]:
    """Exact McNemar test comparing detector A vs detector B on paired items.

    ``b`` = items A got right but B got wrong; ``c`` = items B got right but A
    got wrong. Under H0 (equal error rates) each discordant item is a fair coin,
    so the two-sided exact p-value is the binomial tail probability. Returns the
    counts, the p-value, and which detector has fewer errors.
    """
    yt = list(y_true)
    a = list(pred_a)
    b = list(pred_b)
    a_correct_b_wrong = 0   # "b" in McNemar notation
    b_correct_a_wrong = 0   # "c"
    both_correct = both_wrong = 0
    for t, pa, pb in zip(yt, a, b):
        ca, cb = (pa == t), (pb == t)
        if ca and cb:
            both_correct += 1
        elif ca and not cb:
            a_correct_b_wrong += 1
        elif cb and not ca:
            b_correct_a_wrong += 1
        else:
            both_wrong += 1

    n = a_correct_b_wrong + b_correct_a_wrong
    k = min(a_correct_b_wrong, b_correct_a_wrong)
    p_value = _exact_binomial_two_sided(k, n)
    return {
        "a_correct_b_wrong": a_correct_b_wrong,
        "b_correct_a_wrong": b_correct_a_wrong,
        "both_correct": both_correct,
        "both_wrong": both_wrong,
        "n_discordant": n,
        "p_value": float(p_value),
        "significant_at_0.05": bool(p_value < 0.05),
        "better_detector": (
            "A" if a_correct_b_wrong > b_correct_a_wrong
            else "B" if b_correct_a_wrong > a_correct_b_wrong else "tie"
        ),
    }


def _exact_binomial_two_sided(k: int, n: int) -> float:
    """Two-sided exact binomial p-value for k successes in n trials, p=0.5."""
    if n == 0:
        return 1.0
    from math import comb
    # P(X <= k) under Binomial(n, 0.5); double it for the two-sided test.
    tail = sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)
