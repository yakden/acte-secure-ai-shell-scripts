"""RQ6 — adaptive-evasion robustness.

Both the threat model (paper Section II-B) and the reviewers ask the obvious
question: what happens under an adversary who edits a dangerous script to look
benign without changing what it does? This module answers it with two
behaviour-preserving transformations applied to the dangerous scripts, and
measures how much detection each transformation costs ACTE versus a lexical
TF-IDF baseline.

The transformations preserve the malicious commands exactly (a reverse shell is
still a reverse shell); they only touch surface features:

* ``benign_camouflage`` — prepend a shebang, ``set -euo pipefail``, and several
  reassuring comments. This directly probes the monotonicity property: those
  tokens carry *negative* weight (benign signals) and higher comment density, so
  a monotone risk model must lower its score even though behaviour is unchanged.
* ``lexical_disguise`` — rename attacker hostnames/IPs to innocuous-looking ones
  and rename shell variables. This attacks a bag-of-tokens classifier that has
  learned specific lexical strings, while leaving the dangerous commands intact.

For each detector we report recall on the original dangerous scripts and on each
mutated variant; the drop is the evasion success. Everything is deterministic.
"""

from __future__ import annotations

import re
from typing import Dict, List

from acte.feedback import FeedbackLearning
from acte.trust_engine import TrustEvaluationEngine
from experiments.acte_eval import compute_features
from experiments.dataset import Sample
from experiments.ml_baselines import _models, _vectorizer
from sklearn.pipeline import Pipeline

# Attacker strings that appear in the corpus, mapped to innocuous-looking ones.
_HOST_DISGUISE = [
    (r"malware\.test", "cdn.internal-tools.example"),
    (r"evil-host\.test", "mirror.company-cache.example"),
    (r"attacker\.example\.com", "assets.company-cdn.example"),
    (r"bad-actor\.example\.org", "pkg.company-repo.example"),
    (r"c2\.example\.net", "telemetry.company-ops.example"),
    (r"185\.243\.5\.7", "10.20.30.40"),
    (r"203\.0\.113\.9", "10.20.30.41"),
    (r"198\.51\.100\.7", "10.20.30.42"),
]

_BENIGN_HEADER = (
    "#!/usr/bin/env bash\n"
    "set -euo pipefail\n"
    "# Routine maintenance task, reviewed and approved by the ops team.\n"
    "# This script is idempotent and safe to re-run.\n"
    "# See runbook RB-142 for context and rollback steps.\n"
)


def benign_camouflage(script: str) -> str:
    """Prepend benign-signal boilerplate; behaviour is unchanged."""
    body = script
    if body.startswith("#!"):
        # drop the original shebang line; our header supplies one
        body = body.split("\n", 1)[1] if "\n" in body else ""
    return _BENIGN_HEADER + body


def lexical_disguise(script: str) -> str:
    """Rename attacker hosts/IPs and a common variable; behaviour is unchanged."""
    out = script
    for pat, repl in _HOST_DISGUISE:
        out = re.sub(pat, repl, out)
    # rename a frequently-seen variable name to something anodyne
    out = re.sub(r"\bpayload\b", "artifact", out)
    return out


_MUTATIONS = {
    "benign_camouflage": benign_camouflage,
    "lexical_disguise": lexical_disguise,
    "both": lambda s: lexical_disguise(benign_camouflage(s)),
}


def _recall(pred: List[int]) -> float:
    return sum(pred) / len(pred) if pred else 0.0


def evaluate_adversarial(
    train: List[Sample], test: List[Sample], epochs: int = 40, seed: int = 1337
) -> Dict:
    """Measure recall of ACTE and a TF-IDF baseline on mutated dangerous scripts."""
    dangerous = [s for s in test if s.label == 1]

    # --- ACTE: train full model + tune threshold on train (train-only) ---
    engine = TrustEvaluationEngine()
    train_feats = compute_features(train)
    learner = FeedbackLearning(engine, learning_rate=0.3, l2=1e-3, seed=seed)
    learner.train(list(zip(train_feats, [s.label for s in train])), epochs=epochs)
    tr_scores = [engine.evaluate_features(f).risk_score for f in train_feats]
    learner.tune_threshold(list(zip(tr_scores, [s.label for s in train])), target="f1")
    thr = engine.decision_threshold

    def acte_pred(scripts: List[str]) -> List[int]:
        from acte.pipeline import ACTEPipeline
        pipe = ACTEPipeline(engine=engine)
        return [1 if pipe.analyze(x, generate_policy=False).assessment.risk_score >= thr
                else 0 for x in scripts]

    # --- TF-IDF + LogReg baseline (train on same train split) ---
    tfidf = Pipeline([("tfidf", _vectorizer()), ("clf", _models(seed)["TF-IDF + LogReg"])])
    tfidf.fit([s.script for s in train], [s.label for s in train])

    def ml_pred(scripts: List[str]) -> List[int]:
        return tfidf.predict(scripts).tolist()

    originals = [s.script for s in dangerous]
    results: Dict[str, Dict] = {
        "n_dangerous": len(dangerous),
        "decision_threshold": float(thr),
        "acte": {"original_recall": _recall(acte_pred(originals))},
        "tfidf_logreg": {"original_recall": _recall(ml_pred(originals))},
    }
    for name, fn in _MUTATIONS.items():
        mutated = [fn(x) for x in originals]
        results["acte"][name] = _recall(acte_pred(mutated))
        results["tfidf_logreg"][name] = _recall(ml_pred(mutated))

    # convenience deltas (recall drop under each mutation)
    for det in ("acte", "tfidf_logreg"):
        base = results[det]["original_recall"]
        results[det]["drops"] = {
            name: round(base - results[det][name], 3) for name in _MUTATIONS
        }
    return results
