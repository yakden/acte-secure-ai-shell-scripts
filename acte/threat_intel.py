"""ThreatIntel: data-driven pattern -> risk-weight signature matching.

Signatures live in ``resources/threat_signatures.json`` so the knowledge base
is auditable and editable without touching code. Each signature contributes an
additive weight when its regex matches the raw script. The aggregate signature
weight is one of the inputs to the TrustEvaluationEngine's risk function.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

_DEFAULT_RESOURCE = os.path.join(
    os.path.dirname(__file__), "resources", "threat_signatures.json"
)


@dataclass
class SignatureHit:
    """A single matched signature."""

    id: str
    category: str
    weight: float
    rationale: str


class ThreatIntel:
    """Load and apply the threat-signature knowledge base."""

    def __init__(self, resource_path: Optional[str] = None):
        self.resource_path = resource_path or _DEFAULT_RESOURCE
        with open(self.resource_path, "r", encoding="utf-8") as fh:
            self._data = json.load(fh)
        self.version = self._data.get("version", "unknown")
        self.categories = self._data.get("categories", {})
        self._signatures = []
        for sig in self._data["signatures"]:
            self._signatures.append(
                {
                    "id": sig["id"],
                    "category": sig["category"],
                    "weight": float(sig["weight"]),
                    "rationale": sig["rationale"],
                    "pattern": re.compile(sig["regex"], re.MULTILINE),
                }
            )

    @property
    def signature_ids(self) -> List[str]:
        return [s["id"] for s in self._signatures]

    def match(self, script: str) -> List[SignatureHit]:
        """Return all signatures whose pattern matches ``script``."""
        hits: List[SignatureHit] = []
        for sig in self._signatures:
            if sig["pattern"].search(script):
                hits.append(
                    SignatureHit(
                        id=sig["id"],
                        category=sig["category"],
                        weight=sig["weight"],
                        rationale=sig["rationale"],
                    )
                )
        return hits

    @staticmethod
    def aggregate_weight(hits: List[SignatureHit]) -> float:
        """Sum the weights of all hits (benign signals are negative)."""
        return float(sum(h.weight for h in hits))

    @staticmethod
    def category_breakdown(hits: List[SignatureHit]) -> Dict[str, float]:
        """Per-category summed weight, useful for explanation and analysis."""
        breakdown: Dict[str, float] = {}
        for h in hits:
            breakdown[h.category] = breakdown.get(h.category, 0.0) + h.weight
        return breakdown
