"""Inter-annotator agreement for the field study (Cohen's kappa, and more).

The single largest limitation of this project is that every label so far is
author-assigned: there is no independent human annotation and hence no
inter-annotator agreement to report. This module is the measurement half of the
turnkey field-study harness. Given two independent annotators' label files over
the *same* scripts, it computes:

  * raw (observed) agreement,
  * Cohen's kappa (chance-corrected agreement for two raters), and
  * the confusion matrix and per-label counts,

so a future revision can report kappa alongside the detection numbers. The
implementation is pure Python with no dependencies, so it is unit-tested and
runs anywhere; :func:`cohen_kappa` is the reusable core.

Label files are JSONL, one object per line: ``{"id": <script-id>, "label": 0|1}``
where 1 = dangerous, 0 = safe. Only ids present in *both* files are scored, and
a mismatch in the id sets is reported rather than silently ignored.
"""

from __future__ import annotations

import argparse
import json
from typing import Dict, List, Sequence, Tuple


def cohen_kappa(a: Sequence[int], b: Sequence[int]) -> float:
    """Cohen's kappa for two equal-length sequences of categorical labels.

    Returns 1.0 for perfect agreement, 0.0 for chance-level agreement, and a
    negative value for systematic disagreement. If both raters are perfectly
    constant and identical (no variance, no disagreement) kappa is defined here
    as 1.0; if they are constant but differ, expected agreement is 0 and kappa
    reduces to the observed agreement.
    """
    if len(a) != len(b):
        raise ValueError("label sequences must have equal length")
    n = len(a)
    if n == 0:
        raise ValueError("cannot compute kappa over zero items")

    labels = sorted(set(a) | set(b))
    po = sum(1 for x, y in zip(a, b) if x == y) / n

    pe = 0.0
    for lab in labels:
        pa = sum(1 for x in a if x == lab) / n
        pb = sum(1 for y in b if y == lab) / n
        pe += pa * pb

    if pe == 1.0:
        # No expected variance; agreement is trivially perfect only if observed.
        return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1.0 - pe)


def confusion(a: Sequence[int], b: Sequence[int]) -> Dict[Tuple[int, int], int]:
    """Confusion counts keyed by ``(annotator_a_label, annotator_b_label)``."""
    out: Dict[Tuple[int, int], int] = {}
    for x, y in zip(a, b):
        out[(x, y)] = out.get((x, y), 0) + 1
    return out


def _load(path: str) -> Dict[str, int]:
    labels: Dict[str, int] = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            labels[str(r["id"])] = int(r["label"])
    return labels


def score_files(path_a: str, path_b: str) -> Dict:
    """Align two annotator files by id and compute the agreement summary."""
    la, lb = _load(path_a), _load(path_b)
    shared = sorted(set(la) & set(lb))
    only_a = sorted(set(la) - set(lb))
    only_b = sorted(set(lb) - set(la))
    if not shared:
        return {"available": False, "reason": "no shared script ids between annotators"}

    a = [la[i] for i in shared]
    b = [lb[i] for i in shared]
    conf = confusion(a, b)
    return {
        "available": True,
        "n_scored": len(shared),
        "raw_agreement": round(sum(1 for x, y in zip(a, b) if x == y) / len(shared), 4),
        "cohen_kappa": round(cohen_kappa(a, b), 4),
        "confusion": {f"{k[0]},{k[1]}": v for k, v in sorted(conf.items())},
        "disagreements": [i for i, (x, y) in zip(shared, zip(a, b)) if x != y],
        "ids_only_in_a": only_a,
        "ids_only_in_b": only_b,
    }


def _interpret(kappa: float) -> str:
    # Landis & Koch (1977) benchmarks, reported for orientation only.
    if kappa < 0:
        return "worse than chance"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Cohen's kappa between two annotator label files.")
    ap.add_argument("annotator_a", help="JSONL: {'id':..., 'label':0|1} per line")
    ap.add_argument("annotator_b", help="JSONL: {'id':..., 'label':0|1} per line")
    args = ap.parse_args(argv)

    res = score_files(args.annotator_a, args.annotator_b)
    if not res.get("available"):
        print("no agreement computed:", res.get("reason"))
        return 1
    print(f"scored {res['n_scored']} shared scripts")
    print(f"raw agreement : {res['raw_agreement']}")
    print(f"Cohen's kappa : {res['cohen_kappa']} ({_interpret(res['cohen_kappa'])})")
    if res["ids_only_in_a"] or res["ids_only_in_b"]:
        print(f"warning: {len(res['ids_only_in_a'])} ids only in A, "
              f"{len(res['ids_only_in_b'])} only in B (excluded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
