"""ACTEPipeline: the end-to-end orchestration of all ACTE components.

This is the public entry point most users want: give it a shell script string
and it returns a fully-populated result containing the parse, the context
features, the matched signatures, the trust assessment, and the generated
execution policy. It also exposes the intermediate feature vector so the
experiment harness can reuse it for training and ablation without re-parsing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from acte.semantic_parser import SemanticParser, ParsedScript
from acte.context_extractor import ContextExtractor, ContextFeatures
from acte.threat_intel import ThreatIntel, SignatureHit
from acte.trust_engine import TrustEvaluationEngine, TrustAssessment
from acte.policy_generator import PolicyGenerator, ExecutionPolicy


@dataclass
class ACTEResult:
    parsed: ParsedScript
    context: ContextFeatures
    signature_hits: List[SignatureHit]
    features: Dict[str, float]
    assessment: TrustAssessment
    policy: ExecutionPolicy
    latency_ms: float

    def to_dict(self) -> dict:
        return {
            "parsed": self.parsed.to_dict(),
            "context": self.context.as_vector(),
            "signature_hits": [h.id for h in self.signature_hits],
            "features": self.features,
            "assessment": self.assessment.to_dict(),
            "policy": self.policy.to_dict(),
            "latency_ms": self.latency_ms,
        }


class ACTEPipeline:
    """Compose parser, context, threat-intel, trust engine and policy gen."""

    def __init__(
        self,
        engine: Optional[TrustEvaluationEngine] = None,
        threat_intel: Optional[ThreatIntel] = None,
    ):
        self.parser = SemanticParser()
        self.context_extractor = ContextExtractor()
        self.threat_intel = threat_intel or ThreatIntel()
        self.engine = engine or TrustEvaluationEngine()
        self.policy_generator = PolicyGenerator()

    def analyze(self, script: str, generate_policy: bool = True) -> ACTEResult:
        start = time.perf_counter()

        parsed = self.parser.parse(script)
        context = self.context_extractor.extract(parsed)
        # When the threat-intel component is ablated we skip signature matching
        # entirely so its features are genuinely absent, not just zero-weighted.
        if self.engine.enabled_components.get("threat", True):
            hits = self.threat_intel.match(script)
        else:
            hits = []
        feats = self.engine.build_features(parsed, context, hits)
        assessment = self.engine.evaluate_features(feats, hits)

        policy = (
            self.policy_generator.generate(assessment) if generate_policy else None
        )
        latency_ms = (time.perf_counter() - start) * 1000.0

        return ACTEResult(
            parsed=parsed,
            context=context,
            signature_hits=hits,
            features=feats,
            assessment=assessment,
            policy=policy,
            latency_ms=latency_ms,
        )

    def features_for(self, script: str) -> Dict[str, float]:
        """Compute just the feature vector (used by FeedbackLearning training)."""
        parsed = self.parser.parse(script)
        context = self.context_extractor.extract(parsed)
        hits = (
            self.threat_intel.match(script)
            if self.engine.enabled_components.get("threat", True)
            else []
        )
        return self.engine.build_features(parsed, context, hits)
