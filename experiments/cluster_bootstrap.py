"""Cluster (block) bootstrap and Wilson intervals.

The samples are not independent: ~70 templates generate 420 scripts, so scripts
from one template are correlated. A per-sample bootstrap that resamples the 168
test scripts as if independent understates variance and yields intervals that
are too narrow. The correct procedure resamples whole *templates* (clusters) with
replacement, which is what ``cluster_bootstrap_ci`` does. For a metric estimated
from zero events (the real-world holdout's 0/20 false positives), the percentile
bootstrap is degenerate, so we also provide the Wilson score interval, which is
the standard interval for a binomial proportion near 0 or 1.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

import numpy as np

from experiments.dataset import Sample
from experiments.metrics import classification_metrics


def wilson_interval(k: int, n: int, z: float = 1.96) -> Dict[str, float]:
    """Wilson score 95% interval for k successes in n trials."""
    if n == 0:
        return {"point": 0.0, "low": 0.0, "high": 1.0}
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return {"point": float(p), "low": float(max(0.0, center - half)),
            "high": float(min(1.0, center + half))}


def cluster_bootstrap_ci(
    samples: List[Sample], y_pred: List[int], y_score: Optional[List[float]],
    metrics: Optional[List[str]] = None, n_boot: int = 2000, seed: int = 1337,
    alpha: float = 0.05,
) -> Dict:
    """Percentile CIs from a bootstrap that resamples whole templates.

    Compares interval widths against a naive per-sample bootstrap to make the
    understatement explicit.
    """
    metrics = metrics or ["precision", "recall", "f1", "false_positive_rate"]
    y = np.asarray([s.label for s in samples])
    pred = np.asarray(y_pred)
    score = np.asarray(y_score) if y_score is not None else None
    rng = np.random.default_rng(seed)

    # index samples by template (the cluster)
    tmpl_to_idx: Dict[str, List[int]] = {}
    for i, s in enumerate(samples):
        tmpl_to_idx.setdefault(s.template, []).append(i)
    templates = list(tmpl_to_idx)

    def _metric_bundle(idx):
        yt = y[idx].tolist()
        if len(set(yt)) < 2:
            return None
        yp = pred[idx].tolist()
        ys = score[idx].tolist() if score is not None else None
        m = classification_metrics(yt, yp, ys)
        return {k: m.get(k) for k in metrics}

    def _run(resample_fn):
        acc = {k: [] for k in metrics}
        for _ in range(n_boot):
            idx = resample_fn()
            mb = _metric_bundle(idx)
            if mb is None:
                continue
            for k in metrics:
                if mb[k] is not None:
                    acc[k].append(mb[k])
        lo_p, hi_p = 100 * (alpha / 2), 100 * (1 - alpha / 2)
        out = {}
        for k in metrics:
            if acc[k]:
                out[k] = {"low": float(np.percentile(acc[k], lo_p)),
                          "high": float(np.percentile(acc[k], hi_p))}
        return out

    def _cluster_resample():
        chosen = rng.choice(len(templates), size=len(templates), replace=True)
        idx = []
        for c in chosen:
            idx.extend(tmpl_to_idx[templates[c]])
        return np.asarray(idx)

    def _sample_resample():
        return rng.integers(0, len(samples), size=len(samples))

    point = classification_metrics(
        y.tolist(), pred.tolist(), score.tolist() if score is not None else None)
    cluster = _run(_cluster_resample)
    naive = _run(_sample_resample)

    result = {"n_templates": len(templates), "n_samples": len(samples), "point": {}}
    for k in metrics:
        result["point"][k] = float(point.get(k, 0.0))
    result["cluster_bootstrap"] = cluster
    result["naive_bootstrap"] = naive
    # width comparison
    result["width_ratio"] = {}
    for k in metrics:
        if k in cluster and k in naive:
            cw = cluster[k]["high"] - cluster[k]["low"]
            nw = naive[k]["high"] - naive[k]["low"]
            result["width_ratio"][k] = round(cw / nw, 2) if nw > 0 else None
    return result
