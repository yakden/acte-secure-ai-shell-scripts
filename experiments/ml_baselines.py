"""Learned text-classifier baselines (RQ5).

A skeptical reader's first question about ACTE is not "does it beat a linter?"
(ShellCheck was never a security classifier) but "does its structured,
interpretable, 13-feature model beat an off-the-shelf black-box text classifier
trained on the same labels?" This module answers that question directly.

We build three standard supervised baselines on TF-IDF features of the raw
script text (word 1-2 grams plus character 3-5 grams, which is the usual strong
default for short-text/code classification):

* Logistic Regression   -- a linear model, the closest black-box analogue to
                           ACTE's own logistic form but with thousands of opaque
                           lexical features instead of 13 auditable ones;
* Linear SVM             -- a strong margin-based linear baseline;
* Random Forest          -- a non-linear ensemble.

Each baseline is trained and threshold-free-evaluated with the identical
train/test split ACTE uses, and&mdash;critically&mdash;also evaluated on the
independent real-world holdout after training on the full synthetic corpus. The
real-world transfer is where the comparison becomes informative: a bag-of-tokens
model can memorize synthetic vocabulary (hostnames, template phrasing) and score
well in-distribution while failing to generalize, whereas ACTE's semantic and
contextual features are designed to transfer.

All baselines use scikit-learn with fixed seeds; results reproduce exactly.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from experiments.dataset import Sample
from experiments.metrics import classification_metrics


def _vectorizer() -> FeatureUnion:
    """Word (1-2 gram) + character (3-5 gram) TF-IDF, a strong short-text default."""
    return FeatureUnion([
        ("word", TfidfVectorizer(analyzer="word", ngram_range=(1, 2),
                                 min_df=2, sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                                 min_df=2, sublinear_tf=True)),
    ])


def _models(seed: int) -> Dict[str, object]:
    return {
        "TF-IDF + LogReg": LogisticRegression(max_iter=2000, C=4.0,
                                              class_weight="balanced",
                                              random_state=seed),
        "TF-IDF + LinearSVM": LinearSVC(C=1.0, class_weight="balanced",
                                        random_state=seed),
        "TF-IDF + RandomForest": RandomForestClassifier(
            n_estimators=300, random_state=seed, class_weight="balanced_subsample",
            n_jobs=1),
    }


def _scores(model, X) -> np.ndarray:
    """Return a continuous decision score for ROC/PR, whatever the estimator."""
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    if hasattr(model, "decision_function"):
        d = model.decision_function(X)
        # squash to (0,1) purely for AUC ranking (monotone, so AUC is unchanged)
        return 1.0 / (1.0 + np.exp(-d))
    return model.predict(X).astype(float)


def _fit_eval(name, model, train_text, y_train, test_text, y_test, seed) -> Dict:
    pipe = Pipeline([("tfidf", _vectorizer()), ("clf", model)])
    pipe.fit(train_text, y_train)
    pred = pipe.predict(test_text).tolist()
    score = _scores(pipe, test_text).tolist()
    m = classification_metrics(y_test, pred, score)
    m["name"] = name
    return m, pipe


def evaluate_baselines(
    train: List[Sample], test: List[Sample],
    real: List[Sample] = None, seed: int = 1337,
) -> Dict:
    """Train text baselines on the synthetic split; evaluate on test (and real)."""
    train_text = [s.script for s in train]
    test_text = [s.script for s in test]
    y_train = [s.label for s in train]
    y_test = [s.label for s in test]

    on_test: Dict[str, Dict] = {}
    on_real: Dict[str, Dict] = {}

    # For the real-world transfer test we retrain on the FULL synthetic corpus,
    # exactly as ACTE's RQ4 protocol does, so the comparison is apples-to-apples.
    full_text = train_text + test_text
    y_full = y_train + y_test
    real_text = [s.script for s in real] if real else None
    y_real = [s.label for s in real] if real else None

    for name, model in _models(seed).items():
        m, _ = _fit_eval(name, model, train_text, y_train, test_text, y_test, seed)
        on_test[name] = m
        if real:
            # Fresh estimator of the same kind, trained on all synthetic data.
            mr, piper = _fit_eval(name, _models(seed)[name], full_text, y_full,
                                  real_text, y_real, seed)
            on_real[name] = mr

    return {"on_synthetic_test": on_test, "on_real_world": on_real, "seed": seed}
