"""ACTE: Adaptive Context-Aware Trust Execution.

A research prototype for securing AI-generated shell scripts. The package
exposes a small set of composable analysis components that turn a raw shell
script into a continuous risk score, a discrete trust level, and an adaptive
execution policy.

Pipeline overview
------------------
    raw script
        -> SemanticParser      (commands / AST features)
        -> ContextExtractor    (execution-context features)
        -> ThreatIntel         (pattern -> weight signatures)
        -> TrustEvaluationEngine (R(s) risk function, T(s) trust function)
        -> PolicyGenerator     (seccomp / Rego / namespace policy)
        -> RuntimeMonitor      (syscall-logging sketch)

FeedbackLearning provides an online weight/threshold update mechanism that
adapts the TrustEvaluationEngine from labeled feedback.
"""

from acte.semantic_parser import SemanticParser, ParsedScript
from acte.context_extractor import ContextExtractor, ContextFeatures
from acte.threat_intel import ThreatIntel, SignatureHit
from acte.trust_engine import TrustEvaluationEngine, TrustAssessment, TrustLevel
from acte.policy_generator import PolicyGenerator, ExecutionPolicy
from acte.feedback import FeedbackLearning
from acte.runtime_monitor import RuntimeMonitor
from acte.pipeline import ACTEPipeline

__version__ = "1.0.0"

__all__ = [
    "SemanticParser",
    "ParsedScript",
    "ContextExtractor",
    "ContextFeatures",
    "ThreatIntel",
    "SignatureHit",
    "TrustEvaluationEngine",
    "TrustAssessment",
    "TrustLevel",
    "PolicyGenerator",
    "ExecutionPolicy",
    "FeedbackLearning",
    "RuntimeMonitor",
    "ACTEPipeline",
    "__version__",
]
