"""Dataset loading and deterministic train/test splitting."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
MANIFEST = os.path.join(DATA_DIR, "manifest.jsonl")


@dataclass
class Sample:
    id: str
    category: str
    label: int
    rationale: str
    path: str          # absolute path to the .sh file
    script: str        # the script contents


def load_samples() -> List[Sample]:
    """Load every sample described in the manifest, reading its script body."""
    samples: List[Sample] = []
    with open(MANIFEST, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            # rec["path"] is stored relative to the data dir (e.g. "scripts/x.sh").
            abs_path = os.path.join(DATA_DIR, rec["path"])
            with open(abs_path, "r", encoding="utf-8") as sf:
                script = sf.read()
            samples.append(
                Sample(
                    id=rec["id"],
                    category=rec["category"],
                    label=int(rec["label"]),
                    rationale=rec.get("rationale", ""),
                    path=abs_path,
                    script=script,
                )
            )
    return samples


def stratified_split(
    samples: List[Sample], test_fraction: float = 0.4, seed: int = 1337
) -> Tuple[List[Sample], List[Sample]]:
    """Deterministic split stratified by (category, label).

    Stratifying on both category and label keeps every corpus category and both
    classes represented in train and test, which matters for the per-category
    analysis and for stable metrics.
    """
    import random

    rng = random.Random(seed)
    buckets: Dict[Tuple[str, int], List[Sample]] = {}
    for s in samples:
        buckets.setdefault((s.category, s.label), []).append(s)

    train: List[Sample] = []
    test: List[Sample] = []
    for key in sorted(buckets.keys()):
        group = sorted(buckets[key], key=lambda s: s.id)
        rng.shuffle(group)
        n_test = max(1, round(len(group) * test_fraction)) if len(group) > 1 else 0
        test.extend(group[:n_test])
        train.extend(group[n_test:])

    train.sort(key=lambda s: s.id)
    test.sort(key=lambda s: s.id)
    return train, test


def split_summary(train: List[Sample], test: List[Sample]) -> dict:
    def breakdown(rows: List[Sample]) -> dict:
        out: Dict[str, Dict[str, int]] = {}
        for s in rows:
            c = out.setdefault(s.category, {"safe": 0, "dangerous": 0})
            c["dangerous" if s.label == 1 else "safe"] += 1
        return out

    return {
        "n_total": len(train) + len(test),
        "n_train": len(train),
        "n_test": len(test),
        "train_by_category": breakdown(train),
        "test_by_category": breakdown(test),
        "train_positives": sum(s.label for s in train),
        "test_positives": sum(s.label for s in test),
    }
