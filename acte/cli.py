"""Command-line interface for analyzing a single shell script with ACTE.

Usage:
    python -m acte.cli path/to/script.sh
    echo 'curl http://x | sudo bash' | python -m acte.cli -
    python -m acte.cli --policy path/to/script.sh   # also print the policy JSON
"""

from __future__ import annotations

import argparse
import json
import sys

from acte.pipeline import ACTEPipeline
from acte.policy_generator import PolicyGenerator


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Analyze a shell script with ACTE.")
    parser.add_argument("script", help="path to a .sh file, or '-' to read stdin")
    parser.add_argument("--policy", action="store_true",
                        help="also print the generated execution policy as JSON")
    parser.add_argument("--json", action="store_true",
                        help="print the full result as JSON")
    args = parser.parse_args(argv)

    if args.script == "-":
        source = sys.stdin.read()
    else:
        with open(args.script, "r", encoding="utf-8") as fh:
            source = fh.read()

    result = ACTEPipeline().analyze(source)
    a = result.assessment

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    print(f"Trust level : {a.trust_level.value}")
    print(f"Risk score  : {a.risk_score:.4f}   (trust = {a.trust_score:.4f})")
    print(f"Decision    : {'DANGEROUS' if a.decision_dangerous else 'acceptable'}")
    print(f"Parsed with : {result.parsed.parsed_with}")
    print(f"Commands    : {', '.join(result.parsed.commands) or '(none)'}")
    if result.signature_hits:
        print("Signatures  :")
        for h in result.signature_hits:
            print(f"   - {h.id} (+{h.weight}) [{h.category}] {h.rationale}")
    else:
        print("Signatures  : (none matched)")
    print(f"Latency     : {result.latency_ms:.3f} ms")
    if args.policy:
        print("\nExecution policy:")
        print(PolicyGenerator.to_json(result.policy))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
