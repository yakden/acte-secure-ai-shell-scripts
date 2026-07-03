"""RQ7 — probability calibration of the risk score.

The four trust levels (TRUSTED < 0.25, MONITOR < 0.50, RESTRICT < 0.80, DENY)
assume the risk score behaves like a probability: a script scored 0.7 should be
dangerous roughly 70% of the time. Ranking quality (ROC-AUC) does not imply
that. This module measures calibration directly — a reliability curve, the
Expected Calibration Error (ECE), and the Brier score — and then recalibrates
with isotonic regression and Platt scaling, both fit on the training split only
and evaluated on the held-out test split so there is no leakage.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from acte.trust_engine import TrustEvaluationEngine
from experiments.acte_eval import compute_features, train_and_eval
from experiments.dataset import Sample

_FULL = {"semantic": True, "context": True, "threat": True}


def expected_calibration_error(y_true, prob, n_bins: int = 10) -> Dict:
    """Binned ECE plus the per-bin reliability points."""
    y_true = np.asarray(y_true, dtype=float)
    prob = np.asarray(prob, dtype=float)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    bins = []
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (prob > lo) & (prob <= hi) if i > 0 else (prob >= lo) & (prob <= hi)
        cnt = int(mask.sum())
        if cnt == 0:
            bins.append({"lo": lo, "hi": hi, "count": 0, "confidence": None, "accuracy": None})
            continue
        conf = float(prob[mask].mean())
        acc = float(y_true[mask].mean())
        ece += (cnt / n) * abs(acc - conf)
        bins.append({"lo": float(lo), "hi": float(hi), "count": cnt,
                     "confidence": conf, "accuracy": acc})
    return {"ece": float(ece), "bins": bins}


def brier_score(y_true, prob) -> float:
    y_true = np.asarray(y_true, dtype=float)
    prob = np.asarray(prob, dtype=float)
    return float(np.mean((prob - y_true) ** 2))


def evaluate_calibration(
    train: List[Sample], test: List[Sample], epochs: int = 40, seed: int = 1337,
    n_bins: int = 10,
) -> Dict:
    """Measure and improve calibration of the full ACTE risk score."""
    train_feats = compute_features(train)
    test_feats = compute_features(test)
    y_train = [s.label for s in train]
    y_test = [s.label for s in test]

    # Train the full model exactly as RQ1 does; recover the engine to score train.
    _, test_scores, _, engine = train_and_eval(
        train, test, train_feats, test_feats,
        enabled_components=dict(_FULL), use_feedback=True,
        epochs=epochs, seed=seed,
    )
    train_scores = [engine.evaluate_features(f).risk_score for f in train_feats]

    raw = expected_calibration_error(y_test, test_scores, n_bins)
    out = {
        "n_bins": n_bins,
        "raw": {"ece": raw["ece"], "brier": brier_score(y_test, test_scores),
                "bins": raw["bins"]},
    }

    # Isotonic (monotone, non-parametric) fit on TRAIN scores only.
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(np.asarray(train_scores), np.asarray(y_train, dtype=float))
    iso_test = iso.predict(np.asarray(test_scores))
    out["isotonic"] = {
        "ece": expected_calibration_error(y_test, iso_test, n_bins)["ece"],
        "brier": brier_score(y_test, iso_test),
    }

    # Platt (sigmoid) fit on TRAIN scores only.
    platt = LogisticRegression()
    platt.fit(np.asarray(train_scores).reshape(-1, 1), y_train)
    platt_test = platt.predict_proba(np.asarray(test_scores).reshape(-1, 1))[:, 1]
    out["platt"] = {
        "ece": expected_calibration_error(y_test, platt_test, n_bins)["ece"],
        "brier": brier_score(y_test, platt_test),
    }
    out["reliability_raw"] = raw["bins"]
    return out
