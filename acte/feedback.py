"""FeedbackLearning: online adaptation of the trust model from labeled feedback.

ACTE's risk function R(s) = σ(b + Σ w_i x_i) is a logistic model, so it admits
a principled online update rule: stochastic gradient descent on the binary
cross-entropy loss. Given a script's feature vector ``x`` and a ground-truth
label ``y`` ∈ {0 (safe), 1 (dangerous)}, with prediction ``p = σ(z)``:

    ∂L/∂w_i = (p − y) · x_i
    ∂L/∂b   = (p − y)

    w_i ← w_i − η · (p − y) · x_i
    b   ← b   − η · (p − y)

This is a real learning rule: feeding labeled feedback measurably changes the
engine's weights and therefore its future decisions. The class can also tune
the decision threshold to a target operating point (e.g. minimize false
positives) on a validation set.

An optional L2 penalty keeps weights from drifting too far from their auditable
hand-set priors.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from acte.trust_engine import TrustEvaluationEngine, ALL_FEATURES


@dataclass
class TrainingStats:
    epochs: int = 0
    final_loss: float = 0.0
    loss_history: List[float] = field(default_factory=list)
    weight_delta_norm: float = 0.0


class FeedbackLearning:
    """Online logistic-regression-style updater for the TrustEvaluationEngine."""

    def __init__(
        self,
        engine: TrustEvaluationEngine,
        learning_rate: float = 0.3,
        l2: float = 1e-3,
        seed: int = 42,
    ):
        self.engine = engine
        self.lr = learning_rate
        self.l2 = l2
        self.seed = seed

    # -- single online step ---------------------------------------------------
    def update_one(self, features: Dict[str, float], label: int) -> float:
        """Apply one SGD step for a single labeled example. Returns the loss."""
        z = self.engine.bias
        for name in ALL_FEATURES:
            group = name.split(".", 1)[0]
            if not self.engine.enabled_components.get(group, True):
                continue
            z += self.engine.weights.get(name, 0.0) * features.get(name, 0.0)
        p = _sigmoid(z)
        error = p - label  # gradient of BCE wrt logit

        for name in ALL_FEATURES:
            group = name.split(".", 1)[0]
            if not self.engine.enabled_components.get(group, True):
                continue
            x = features.get(name, 0.0)
            w = self.engine.weights.get(name, 0.0)
            grad = error * x + self.l2 * w
            self.engine.weights[name] = w - self.lr * grad
        self.engine.bias -= self.lr * error
        return _bce(p, label)

    # -- batch / epoch training ----------------------------------------------
    def train(
        self,
        dataset: List[Tuple[Dict[str, float], int]],
        epochs: int = 25,
    ) -> TrainingStats:
        """Train over (features, label) pairs for several epochs.

        Returns statistics including the loss curve and the L2 norm of the total
        weight change, which proves the model actually moved.
        """
        rng = _Lcg(self.seed)
        before = dict(self.engine.weights)
        before_bias = self.engine.bias

        stats = TrainingStats()
        order = list(range(len(dataset)))
        for epoch in range(epochs):
            rng.shuffle(order)
            epoch_loss = 0.0
            for idx in order:
                feats, label = dataset[idx]
                epoch_loss += self.update_one(feats, label)
            mean_loss = epoch_loss / max(1, len(dataset))
            stats.loss_history.append(mean_loss)

        stats.epochs = epochs
        stats.final_loss = stats.loss_history[-1] if stats.loss_history else 0.0
        delta_sq = sum(
            (self.engine.weights[k] - before.get(k, 0.0)) ** 2 for k in self.engine.weights
        )
        delta_sq += (self.engine.bias - before_bias) ** 2
        stats.weight_delta_norm = math.sqrt(delta_sq)
        return stats

    # -- decision-threshold tuning -------------------------------------------
    def tune_threshold(
        self,
        scored: List[Tuple[float, int]],
        target: str = "f1",
        max_fpr: float = 0.05,
    ) -> float:
        """Pick a decision threshold from (risk_score, label) pairs.

        ``target='f1'`` maximizes F1; ``target='min_fp'`` picks the lowest
        threshold whose false-positive rate stays under ``max_fpr`` while
        keeping recall as high as possible. The chosen threshold is written back
        to the engine and returned.
        """
        candidates = sorted({round(s, 3) for s, _ in scored} | {0.5})
        best_thr, best_score = 0.5, -1.0
        for thr in candidates:
            tp = fp = tn = fn = 0
            for score, label in scored:
                pred = 1 if score >= thr else 0
                if pred == 1 and label == 1:
                    tp += 1
                elif pred == 1 and label == 0:
                    fp += 1
                elif pred == 0 and label == 0:
                    tn += 1
                else:
                    fn += 1
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            fpr = fp / (fp + tn) if (fp + tn) else 0.0
            if target == "f1":
                f1 = (2 * precision * recall / (precision + recall)
                      if (precision + recall) else 0.0)
                metric = f1
            else:  # min_fp: maximize recall subject to FPR <= max_fpr
                metric = recall if fpr <= max_fpr else -1.0
            if metric > best_score:
                best_score, best_thr = metric, thr
        self.engine.decision_threshold = best_thr
        return best_thr


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


def _bce(p: float, y: int, eps: float = 1e-12) -> float:
    p = min(1 - eps, max(eps, p))
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


class _Lcg:
    """Tiny deterministic linear-congruential RNG for reproducible shuffles.

    Using our own RNG (rather than the global ``random`` module) keeps training
    order independent of any other code that might touch the global seed.
    """

    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFF

    def _next(self) -> int:
        self.state = (1103515245 * self.state + 12345) & 0x7FFFFFFF
        return self.state

    def shuffle(self, seq: List[int]) -> None:
        for i in range(len(seq) - 1, 0, -1):
            j = self._next() % (i + 1)
            seq[i], seq[j] = seq[j], seq[i]
