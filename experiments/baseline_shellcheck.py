"""ShellCheck baseline detector.

ShellCheck is a static-analysis linter for shell scripts. It is *not* a security
classifier, but it is the most widely deployed automated shell-script checker,
which makes it a meaningful baseline for RQ3 (false-positive behavior). We run
ShellCheck on every test sample and map its findings to a binary "dangerous"
decision using a documented, deliberately charitable rule:

    A script is flagged dangerous if ShellCheck reports at least one finding
    whose severity level is 'error' or 'warning'.

This is the operating point most likely to *catch* problems (and therefore most
favorable to the baseline). We also record an 'error-only' variant for context.
If the ShellCheck binary is unavailable, the baseline is skipped and clearly
marked as unavailable -- its numbers are never fabricated.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Dict, List, Optional

from experiments.dataset import Sample
from experiments.metrics import classification_metrics


def shellcheck_available() -> Optional[str]:
    """Return the resolved ShellCheck path, or None if not installed."""
    return shutil.which("shellcheck")


def _run_shellcheck(path: str) -> List[dict]:
    """Run shellcheck on one file and return its findings (possibly empty)."""
    try:
        proc = subprocess.run(
            ["shellcheck", "-f", "json", "-s", "bash", path],
            capture_output=True, text=True, timeout=30,
        )
    except Exception:
        return []
    out = proc.stdout.strip()
    if not out:
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return []


def evaluate_baseline(test: List[Sample]) -> Dict:
    """Run ShellCheck over the test split and compute baseline metrics."""
    if not shellcheck_available():
        return {"available": False, "reason": "shellcheck binary not found on PATH"}

    version = _shellcheck_version()
    y_true = [s.label for s in test]

    pred_warn: List[int] = []   # flag on error OR warning
    pred_err: List[int] = []    # flag on error only
    finding_counts: List[int] = []

    for s in test:
        findings = _run_shellcheck(s.path)
        finding_counts.append(len(findings))
        levels = {f.get("level", "") for f in findings}
        pred_warn.append(1 if (levels & {"error", "warning"}) else 0)
        pred_err.append(1 if ("error" in levels) else 0)

    metrics_warn = classification_metrics(y_true, pred_warn)
    metrics_err = classification_metrics(y_true, pred_err)

    return {
        "available": True,
        "version": version,
        "mapping": "dangerous if any finding level in {error, warning}",
        "metrics": metrics_warn,
        "metrics_error_only": metrics_err,
        "predictions": pred_warn,
        "mean_findings_per_script": (
            sum(finding_counts) / len(finding_counts) if finding_counts else 0.0
        ),
    }


def _shellcheck_version() -> str:
    try:
        proc = subprocess.run(
            ["shellcheck", "--version"], capture_output=True, text=True, timeout=10
        )
        for line in proc.stdout.splitlines():
            if line.lower().startswith("version:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return "unknown"
