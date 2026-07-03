"""RQ8 — stronger baselines that isolate features from the linear model.

The reviewer's objection to the RQ5 baselines is fair: comparing a hand-tuned
13-feature logistic model to TF-IDF conflates "ACTE as a feature set" with
"ACTE as a linear model," and the TF-IDF baselines were untuned. This module
adds three sharper comparisons, all trained train-only:

* ``gbdt_on_acte_features`` — the SAME 13 ACTE features fed to a gradient-boosted
  tree. If it beats the logistic ACTE, the ceiling is the linear model, not the
  features; if not, the features are the limit.
* ``union_features_plus_tfidf`` — the 13 features concatenated with TF-IDF, to
  test whether the engineered features add signal on top of lexical features.
* ``tfidf_logreg_tuned`` — the TF-IDF + logistic baseline with C selected by
  train-only grid search, so RQ5 is not a comparison against an untuned model.

A frozen code-transformer baseline (CodeBERT/StarEncoder) is intentionally NOT
included: its weights cannot be fetched in this offline environment, and
fabricating it would defeat the point. It is documented as future work.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline

from acte.trust_engine import ALL_FEATURES
from experiments.acte_eval import compute_features
from experiments.dataset import Sample
from experiments.metrics import classification_metrics
from experiments.ml_baselines import _vectorizer


def _feature_matrix(feats: List[Dict[str, float]]) -> np.ndarray:
    return np.asarray([[f.get(k, 0.0) for k in ALL_FEATURES] for f in feats], dtype=float)


def _scores(model, X):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    d = model.decision_function(X)
    return 1.0 / (1.0 + np.exp(-d))


def evaluate_extended_baselines(
    train: List[Sample], test: List[Sample], seed: int = 1337
) -> Dict:
    y_tr = [s.label for s in train]
    y_te = [s.label for s in test]
    Xtr = _feature_matrix(compute_features(train))
    Xte = _feature_matrix(compute_features(test))
    txt_tr = [s.script for s in train]
    txt_te = [s.script for s in test]

    out: Dict[str, Dict] = {}

    # (1) GBDT on the 13 ACTE features
    gbdt = HistGradientBoostingClassifier(random_state=seed, max_depth=4,
                                          learning_rate=0.1, max_iter=300)
    gbdt.fit(Xtr, y_tr)
    out["gbdt_on_acte_features"] = classification_metrics(
        y_te, gbdt.predict(Xte).tolist(), _scores(gbdt, Xte).tolist())

    # (2) Union: TF-IDF (sparse) + 13 dense features
    vec = _vectorizer()
    Ttr = vec.fit_transform(txt_tr)
    Tte = vec.transform(txt_te)
    Utr = hstack([Ttr, csr_matrix(Xtr)]).tocsr()
    Ute = hstack([Tte, csr_matrix(Xte)]).tocsr()
    union = LogisticRegression(max_iter=2000, C=4.0, class_weight="balanced",
                               random_state=seed)
    union.fit(Utr, y_tr)
    out["union_features_plus_tfidf"] = classification_metrics(
        y_te, union.predict(Ute).tolist(), _scores(union, Ute).tolist())

    # (3) Tuned TF-IDF + LogReg (grid over C, train-only CV)
    pipe = Pipeline([("tfidf", _vectorizer()),
                     ("clf", LogisticRegression(max_iter=2000, class_weight="balanced",
                                                random_state=seed))])
    grid = GridSearchCV(pipe, {"clf__C": [0.25, 1.0, 4.0, 16.0]},
                        scoring="f1", cv=5, n_jobs=1)
    grid.fit(txt_tr, y_tr)
    best = grid.best_estimator_
    out["tfidf_logreg_tuned"] = classification_metrics(
        y_te, best.predict(txt_te).tolist(), _scores(best, txt_te).tolist())
    out["tfidf_logreg_tuned"]["best_C"] = float(grid.best_params_["clf__C"])

    out["note"] = ("CodeBERT/StarEncoder baseline omitted: model weights are not "
                   "downloadable in this offline environment; documented as future work.")
    return out
