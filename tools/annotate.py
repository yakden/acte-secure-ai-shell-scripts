"""Two-annotator labelling CLI for the field-study corpus.

The reviewer's decisive test is third-party scripts labelled by *independent*
annotators with reported inter-annotator agreement. This is the human half of
the harness: it presents each script to an annotator one at a time and records a
safe/dangerous judgement, writing a JSONL label file that ``tools.agreement``
consumes. Run it twice (two different people, same corpus, separate output
files), then compute Cohen's kappa.

Nothing here is executed or scored automatically: the whole point is that a
human, not the detector's author, assigns the label. The script text is only
displayed.

Usage::

    python -m tools.annotate --corpus data/field/manifest.jsonl \
        --out annotations/annotator_a.jsonl --annotator A

The corpus manifest is JSONL with at least ``{"id":..., "path":...}`` per line,
where ``path`` is relative to the manifest's directory (the format produced by
``tools.collect_llm_scripts`` and by ``data/external/fetch_external.py``).
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List


def _load_manifest(path: str) -> List[Dict]:
    base = os.path.dirname(os.path.abspath(path))
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            r["_abs"] = os.path.join(base, r["path"]) if not os.path.isabs(r["path"]) else r["path"]
            out.append(r)
    return out


def _load_done(out_path: str) -> Dict[str, int]:
    done: Dict[str, int] = {}
    if os.path.exists(out_path):
        with open(out_path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    done[str(r["id"])] = int(r["label"])
    return done


def _prompt_label(sid: str) -> int | None:
    while True:
        ans = input(f"[{sid}] label — (s)afe / (d)angerous / (q)uit: ").strip().lower()
        if ans in ("s", "safe", "0"):
            return 0
        if ans in ("d", "dangerous", "1"):
            return 1
        if ans in ("q", "quit"):
            return None
        print("  please answer s, d, or q")


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Independent human annotation of a script corpus.")
    ap.add_argument("--corpus", required=True, help="manifest JSONL with id + path per line")
    ap.add_argument("--out", required=True, help="output JSONL label file (resumable)")
    ap.add_argument("--annotator", default="", help="annotator id, recorded in the file")
    ap.add_argument("--max-chars", type=int, default=4000, help="truncate long scripts in the display")
    args = ap.parse_args(argv)

    corpus = _load_manifest(args.corpus)
    done = _load_done(args.out)
    remaining = [r for r in corpus if str(r["id"]) not in done]
    print(f"{len(corpus)} scripts, {len(done)} already labelled, {len(remaining)} to go.\n")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "a", encoding="utf-8") as out_fh:
        for r in remaining:
            sid = str(r["id"])
            try:
                body = open(r["_abs"], encoding="utf-8", errors="replace").read()
            except OSError as exc:
                print(f"  skip {sid}: {exc}")
                continue
            print("=" * 72)
            print(f"id: {sid}   provenance: {r.get('provenance', r.get('rationale', '?'))}")
            print("-" * 72)
            print(body[: args.max_chars])
            if len(body) > args.max_chars:
                print(f"... [truncated, {len(body) - args.max_chars} more chars]")
            print("-" * 72)
            label = _prompt_label(sid)
            if label is None:
                print("stopped; progress saved.")
                break
            out_fh.write(json.dumps({"id": sid, "label": label,
                                     "annotator": args.annotator}) + "\n")
            out_fh.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
