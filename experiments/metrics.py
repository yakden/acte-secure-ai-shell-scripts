"""Classification metrics computed with scikit-learn.

All numbers reported by the harness flow through this module so that there is a
single, auditable definition of every metric. Positive class = 1 = dangerous.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    matthews_corrcoef,
    precision_recall_curve,
    precision_recall_fscore_support,
    roc_curve,
)


def classification_metrics(
    y_true: List[int], y_pred: List[int], y_score: Optional[List[float]] = None
) -> Dict:
    """Compute the full metric bundle for one detector on one split."""
    y_true = list(y_true)
    y_pred = list(y_pred)

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", pos_label=1, zero_division=0
    )
    acc = accuracy_score(y_true, y_pred)
    mcc = matthews_corrcoef(y_true, y_pred) if len(set(y_true)) > 1 else 0.0

    # Confusion matrix with an explicit label order so tn/fp/fn/tp are stable.
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    fnr = fn / (fn + tp) if (fn + tp) else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0

    out = {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "mcc": float(mcc),
        "accuracy": float(acc),
        "false_positive_rate": float(fpr),
        "false_negative_rate": float(fnr),
        "specificity": float(specificity),
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "support": {
            "n": len(y_true),
            "positives": int(sum(y_true)),
            "negatives": int(len(y_true) - sum(y_true)),
        },
    }

    if y_score is not None and len(set(y_true)) > 1:
        out["roc_auc"] = _roc_auc(y_true, y_score)
        out["pr_auc"] = _pr_auc(y_true, y_score)
    return out


def _roc_auc(y_true: List[int], y_score: List[float]) -> float:
    fpr, tpr, _ = roc_curve(y_true, y_score)
    return float(auc(fpr, tpr))


def _pr_auc(y_true: List[int], y_score: List[float]) -> float:
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    return float(auc(recall, precision))


def roc_points(y_true: List[int], y_score: List[float]):
    fpr, tpr, thr = roc_curve(y_true, y_score)
    return fpr, tpr, thr


def pr_points(y_true: List[int], y_score: List[float]):
    precision, recall, thr = precision_recall_curve(y_true, y_score)
    return precision, recall, thr


def per_category_recall(
    samples, y_pred: List[int]
) -> Dict[str, Dict[str, float]]:
    """Detection rate per corpus category (recall on dangerous, FPR on safe)."""
    by_cat: Dict[str, Dict[str, List[int]]] = {}
    for s, pred in zip(samples, y_pred):
        d = by_cat.setdefault(s.category, {"true": [], "pred": []})
        d["true"].append(s.label)
        d["pred"].append(pred)

    out: Dict[str, Dict[str, float]] = {}
    for cat, d in sorted(by_cat.items()):
        yt = np.array(d["true"])
        yp = np.array(d["pred"])
        pos = yt == 1
        neg = yt == 0
        recall = float((yp[pos] == 1).mean()) if pos.any() else None
        fpr = float((yp[neg] == 1).mean()) if neg.any() else None
        out[cat] = {
            "n": int(len(yt)),
            "n_dangerous": int(pos.sum()),
            "n_safe": int(neg.sum()),
            "recall_dangerous": recall,
            "false_positive_rate_safe": fpr,
        }
    return out
