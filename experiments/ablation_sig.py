"""Paired significance tests for the ablation deltas.

The ablation table reports point F1 differences between configurations, but their
confidence intervals overlap, so a bare "ThreatIntel is the most discriminative
component" or "removing ContextExtractor improves F1" cannot be asserted from
point estimates alone. This module recomputes each ablation configuration's
per-item test predictions and runs an exact McNemar test of each configuration
against the full model on the *same* held-out items, so the ranking claims are
backed (or not) by a paired test rather than by eyeballing deltas.
"""

from __future__ import annotations

from typing import Dict, List

from experiments.acte_eval import compute_features, train_and_eval
from experiments.dataset import Sample
from experiments.stats import mcnemar

_CONFIGS = [
    ("full", {"semantic": True, "context": True, "threat": True}, True),
    ("no_semantic", {"semantic": False, "context": True, "threat": True}, True),
    ("no_context", {"semantic": True, "context": False, "threat": True}, True),
    ("no_threat", {"semantic": True, "context": True, "threat": False}, True),
    ("no_feedback", {"semantic": True, "context": True, "threat": True}, False),
]


def evaluate_ablation_significance(
    train: List[Sample], test: List[Sample], epochs: int = 40, seed: int = 1337
) -> Dict:
    train_feats = compute_features(train)
    test_feats = compute_features(test)
    y_true = [s.label for s in test]

    preds: Dict[str, List[int]] = {}
    f1s: Dict[str, float] = {}
    for name, comps, use_fb in _CONFIGS:
        metrics, _scores, pred, _ = train_and_eval(
            train, test, train_feats, test_feats,
            enabled_components=comps, use_feedback=use_fb, epochs=epochs, seed=seed,
        )
        preds[name] = pred
        f1s[name] = metrics["f1"]

    full_pred = preds["full"]
    out = {"full_f1": f1s["full"], "comparisons": {}}
    for name in preds:
        if name == "full":
            continue
        mc = mcnemar(y_true, full_pred, preds[name])
        out["comparisons"][name] = {
            "f1": f1s[name],
            "delta_f1": round(f1s[name] - f1s["full"], 4),
            "mcnemar_p": mc["p_value"],
            "significant_at_0.05": mc["significant_at_0.05"],
            "n_discordant": mc["n_discordant"],
        }
    return out
