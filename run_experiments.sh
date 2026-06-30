#!/usr/bin/env bash
# Reproducible entrypoint for the full ACTE study.
# Regenerates the dataset, runs all experiments, and writes results + figures
# deterministically (fixed seeds). Equivalent to `python -m experiments.run_all`.
set -euo pipefail

cd "$(dirname "$0")"

echo "[run_experiments] Python: $(python3 --version)"

# Optional: install Python dependencies if missing.
if ! python3 -c "import sklearn, matplotlib, bashlex, numpy" >/dev/null 2>&1; then
    echo "[run_experiments] Installing Python dependencies ..."
    python3 -m pip install -r requirements.txt
fi

# ShellCheck is an optional baseline; warn (do not fail) if absent.
if ! command -v shellcheck >/dev/null 2>&1; then
    echo "[run_experiments] WARNING: shellcheck not found; baseline will be skipped."
    echo "[run_experiments] Install with: sudo apt-get install -y shellcheck"
fi

echo "[run_experiments] Running full experiment harness ..."
python3 -m experiments.run_all

echo "[run_experiments] Done. See experiments/results/ and experiments/figures/."
