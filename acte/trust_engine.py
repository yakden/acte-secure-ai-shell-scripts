"""TrustEvaluationEngine: the formal risk and trust model at ACTE's core.

Risk function R(s)
------------------
Every script ``s`` is reduced to a named feature vector ``x(s)`` whose entries
are grouped by the component that produced them:

* ``semantic.*``      -- structural facts from the SemanticParser,
* ``context.*``       -- the five normalized ContextExtractor dimensions,
* ``threat.*``        -- aggregate / per-category ThreatIntel signature weights.

The model is a logistic (log-linear) risk function:

    z(s) = b + Σ_i w_i · x_i(s)              (the "logit")
    R(s) = σ(z(s)) = 1 / (1 + e^(−z(s)))     ∈ (0, 1)

R(s) is the **continuous risk score**. Because σ is strictly increasing, R is
monotonic in the weighted feature aggregate z: adding evidence (a positive
weighted feature) never decreases risk, and benign signals (negative weights)
never increase it. This is the documented monotonicity property.

Trust function T(s)
-------------------
Trust is the strictly decreasing complement of risk:

    T(s) = 1 − R(s)                          ∈ (0, 1)

so higher risk ⇒ lower trust, monotonically. The continuous trust value is
mapped to a discrete trust level via fixed risk thresholds:

    R < 0.25            -> TRUSTED
    0.25 ≤ R < 0.50     -> MONITOR
    0.50 ≤ R < 0.80     -> RESTRICT
    R ≥ 0.80            -> DENY

For binary detection metrics a script is flagged "dangerous" when
R(s) ≥ ``decision_threshold`` (default 0.50, i.e. RESTRICT or DENY).

The weights ``w_i`` and bias ``b`` start from auditable hand-set defaults and
can be adapted online by :class:`acte.feedback.FeedbackLearning`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from acte.semantic_parser import ParsedScript
from acte.context_extractor import ContextFeatures
from acte.threat_intel import SignatureHit, ThreatIntel


class TrustLevel(str, Enum):
    TRUSTED = "TRUSTED"
    MONITOR = "MONITOR"
    RESTRICT = "RESTRICT"
    DENY = "DENY"


# Feature groups -> the component responsible. Used by the ablation study to
# disable an entire component by masking its feature group to zero.
FEATURE_GROUPS = {
    "semantic": [
        "semantic.pipes_to_shell",
        "semantic.has_destructive_cmd",
        "semantic.has_network_cmd",
        "semantic.has_device_target",
        "semantic.cmd_substitution_density",
    ],
    "context": [
        "context.privilege_required",
        "context.network_egress",
        "context.filesystem_scope",
        "context.irreversibility",
        "context.obfuscation",
    ],
    "threat": [
        "threat.weight_norm",
        "threat.max_category_norm",
        "threat.distinct_categories",
    ],
}

ALL_FEATURES = [f for grp in FEATURE_GROUPS.values() for f in grp]

# Hand-set default weights (the "cold start" model). Chosen so the prototype is
# reasonable before any feedback learning; FeedbackLearning fine-tunes them.
DEFAULT_WEIGHTS: Dict[str, float] = {
    "semantic.pipes_to_shell": 1.6,
    "semantic.has_destructive_cmd": 1.1,
    "semantic.has_network_cmd": 0.7,
    "semantic.has_device_target": 1.3,
    "semantic.cmd_substitution_density": 0.6,
    "context.privilege_required": 1.2,
    "context.network_egress": 1.3,
    "context.filesystem_scope": 1.4,
    "context.irreversibility": 1.8,
    "context.obfuscation": 1.7,
    "threat.weight_norm": 3.4,
    "threat.max_category_norm": 1.5,
    "threat.distinct_categories": 0.9,
}
DEFAULT_BIAS = -2.4

# Normalization constants (keep feature magnitudes ~[0, 1]).
_SIG_WEIGHT_SCALE = 10.0       # aggregate signature weight saturating point
_SIG_CATEGORY_SCALE = 9.5      # single-category weight saturating point
_MAX_CATEGORIES = 5.0


@dataclass
class TrustAssessment:
    """The full result of evaluating one script."""

    risk_score: float
    trust_score: float
    trust_level: TrustLevel
    logit: float
    features: Dict[str, float] = field(default_factory=dict)
    weighted_contributions: Dict[str, float] = field(default_factory=dict)
    signature_hits: List[SignatureHit] = field(default_factory=list)
    decision_dangerous: bool = False

    def to_dict(self) -> dict:
        return {
            "risk_score": self.risk_score,
            "trust_score": self.trust_score,
            "trust_level": self.trust_level.value,
            "logit": self.logit,
            "decision_dangerous": self.decision_dangerous,
            "features": self.features,
            "weighted_contributions": self.weighted_contributions,
            "signature_hits": [h.id for h in self.signature_hits],
        }


class TrustEvaluationEngine:
    """Compute R(s), T(s), and the discrete trust level for a script."""

    # Risk thresholds for discrete trust levels (see module docstring).
    LEVEL_THRESHOLDS = [
        (0.25, TrustLevel.TRUSTED),
        (0.50, TrustLevel.MONITOR),
        (0.80, TrustLevel.RESTRICT),
        (1.01, TrustLevel.DENY),
    ]

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        bias: float = DEFAULT_BIAS,
        decision_threshold: float = 0.50,
        enabled_components: Optional[Dict[str, bool]] = None,
    ):
        self.weights = dict(DEFAULT_WEIGHTS)
        if weights:
            self.weights.update(weights)
        self.bias = bias
        self.decision_threshold = decision_threshold
        # Ablation control: which feature groups are active.
        self.enabled_components = {
            "semantic": True,
            "context": True,
            "threat": True,
        }
        if enabled_components:
            self.enabled_components.update(enabled_components)

    # -- feature engineering --------------------------------------------------
    def build_features(
        self,
        parsed: ParsedScript,
        context: ContextFeatures,
        hits: List[SignatureHit],
    ) -> Dict[str, float]:
        from acte.threat_intel import ThreatIntel as _TI

        destructive_cmds = {"rm", "dd", "mkfs", "shred", "fdisk", "wipefs", "parted"}
        network_cmds = {"curl", "wget", "nc", "ncat", "netcat", "ssh", "scp",
                        "socat", "ftp", "telnet"}
        cmds = parsed.command_set()

        agg = _TI.aggregate_weight(hits)
        breakdown = _TI.category_breakdown(hits)
        # Only positive (threat) categories count toward the "max category".
        positive_cats = {k: v for k, v in breakdown.items() if v > 0}
        max_cat = max(positive_cats.values()) if positive_cats else 0.0

        sub_density = (
            parsed.command_substitutions / parsed.line_count
            if parsed.line_count
            else 0.0
        )

        feats = {
            "semantic.pipes_to_shell": 1.0 if parsed.pipes_to_shell else 0.0,
            "semantic.has_destructive_cmd": 1.0 if cmds & destructive_cmds else 0.0,
            "semantic.has_network_cmd": 1.0 if cmds & network_cmds else 0.0,
            "semantic.has_device_target": 1.0 if parsed.devices else 0.0,
            "semantic.cmd_substitution_density": min(1.0, sub_density),
            "context.privilege_required": context.privilege_required,
            "context.network_egress": context.network_egress,
            "context.filesystem_scope": context.filesystem_scope,
            "context.irreversibility": context.irreversibility,
            "context.obfuscation": context.obfuscation,
            "threat.weight_norm": _clip(max(0.0, agg) / _SIG_WEIGHT_SCALE),
            "threat.max_category_norm": _clip(max_cat / _SIG_CATEGORY_SCALE),
            "threat.distinct_categories": len(positive_cats) / _MAX_CATEGORIES,
        }
        return feats

    # -- scoring --------------------------------------------------------------
    def evaluate_features(
        self, feats: Dict[str, float], hits: Optional[List[SignatureHit]] = None
    ) -> TrustAssessment:
        """Score a pre-built feature vector (used by training and ablation)."""
        logit = self.bias
        contributions: Dict[str, float] = {}
        for name in ALL_FEATURES:
            group = name.split(".", 1)[0]
            if not self.enabled_components.get(group, True):
                continue  # ablation: component disabled
            x = feats.get(name, 0.0)
            w = self.weights.get(name, 0.0)
            c = w * x
            contributions[name] = c
            logit += c

        risk = _sigmoid(logit)
        trust = 1.0 - risk
        level = self._risk_to_level(risk)
        return TrustAssessment(
            risk_score=risk,
            trust_score=trust,
            trust_level=level,
            logit=logit,
            features=feats,
            weighted_contributions=contributions,
            signature_hits=hits or [],
            decision_dangerous=risk >= self.decision_threshold,
        )

    def evaluate(
        self,
        parsed: ParsedScript,
        context: ContextFeatures,
        hits: List[SignatureHit],
    ) -> TrustAssessment:
        feats = self.build_features(parsed, context, hits)
        return self.evaluate_features(feats, hits)

    # -- helpers --------------------------------------------------------------
    def _risk_to_level(self, risk: float) -> TrustLevel:
        for threshold, level in self.LEVEL_THRESHOLDS:
            if risk < threshold:
                return level
        return TrustLevel.DENY

    def get_params(self) -> dict:
        return {"weights": dict(self.weights), "bias": self.bias}

    def set_params(self, weights: Dict[str, float], bias: float) -> None:
        self.weights.update(weights)
        self.bias = bias


def _sigmoid(z: float) -> float:
    # Numerically stable logistic function.
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))
