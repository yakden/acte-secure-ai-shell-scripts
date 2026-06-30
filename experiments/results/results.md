# ACTE Experiment Results

> All numbers below were produced by a real, reproducible run of the ACTE prototype (`python -m experiments.run_all`). Nothing is hardcoded.

- Generated (UTC): `2026-06-30T13:07:39.808832+00:00`
- Seed: `1337`  |  Training epochs: `40`  |  Test fraction: `0.4`
- Python `3.11.6`  |  Platform `Linux-6.17.0-1010-aws-x86_64-with-glibc2.36`
- Dataset: **420 samples** (train=252, test=168, test positives=76)

## Dataset split by category

| Category | Train safe | Train dangerous | Test safe | Test dangerous |
|---|---|---|---|---|
| ai_generated | 31 | 14 | 21 | 9 |
| malicious | 0 | 66 | 0 | 44 |
| obfuscated | 0 | 33 | 0 | 22 |
| safe_everyday | 57 | 0 | 38 | 0 |
| sysadmin | 50 | 1 | 33 | 1 |

## RQ1 — Detection accuracy of dangerous (AI-generated) shell scripts

**ACTE (full model) on held-out test set:**

| Metric | Value |
|---|---|
| Precision | 0.9848 |
| Recall | 0.8553 |
| F1 | 0.9155 |
| MCC | 0.8605 |
| Accuracy | 0.9286 |
| ROC-AUC | 0.9757 |
| PR-AUC | 0.9781 |
| False Positive Rate | 0.0109 |
| False Negative Rate | 0.1447 |
| Decision threshold (tuned) | 0.5000 |

Confusion matrix (test): TN=91, FP=1, FN=11, TP=65

Online learning moved the model: loss 0.3450 → 0.2884 over 40 epochs (‖Δweights‖ = 6.0792).

### Per-category detection (ACTE full)

| Category | n | dangerous | safe | Recall (dangerous) | FPR (safe) |
|---|---|---|---|---|---|
| ai_generated | 30 | 9 | 21 | 1.000 | 0.000 |
| malicious | 44 | 44 | 0 | 0.750 | n/a |
| obfuscated | 22 | 22 | 0 | 1.000 | n/a |
| safe_everyday | 38 | 0 | 38 | n/a | 0.000 |
| sysadmin | 34 | 1 | 33 | 1.000 | 0.030 |

## Ablation study — contribution of each component

Each configuration is trained and evaluated with the identical protocol; the drop versus `full` quantifies the disabled component's contribution.

| Configuration | Precision | Recall | F1 | MCC | Accuracy | FPR | ROC-AUC |
|---|---|---|---|---|---|---|---|
| full | 0.985 | 0.855 | 0.915 | 0.861 | 0.929 | 0.011 | 0.976 |
| no_semantic | 0.957 | 0.868 | 0.910 | 0.846 | 0.923 | 0.033 | 0.967 |
| no_context | 0.985 | 0.882 | 0.931 | 0.883 | 0.940 | 0.011 | 0.969 |
| no_threat | 0.833 | 0.789 | 0.811 | 0.663 | 0.833 | 0.130 | 0.896 |
| no_feedback | 0.766 | 0.947 | 0.847 | 0.710 | 0.845 | 0.239 | 0.952 |

**F1 delta vs full model:**

| Disabled component | F1 | Δ F1 vs full |
|---|---|---|
| no_semantic | 0.910 | -0.005 |
| no_context | 0.931 | 0.015 |
| no_threat | 0.811 | -0.105 |
| no_feedback | 0.847 | -0.068 |

## RQ2 — Computational cost (per-script analysis latency)

| Statistic | Milliseconds |
|---|---|
| Mean | 0.509 |
| Median | 0.452 |
| p95 | 0.954 |
| p99 | 1.335 |
| Min | 0.193 |
| Max | 1.374 |
| Stdev | 0.218 |
| Throughput (scripts/s) | 1962.9 |

Measured over 420 scripts, 3 repeats each (min taken).

## RQ3 — False-positive reduction vs the ShellCheck baseline

ShellCheck version `0.9.0`. Mapping: *dangerous if any finding level in {error, warning}*. Mean findings/script: 0.27.

| Detector | Precision | Recall | F1 | MCC | Accuracy | FPR |
|---|---|---|---|---|---|---|
| ACTE (full) | 0.985 | 0.855 | 0.915 | 0.861 | 0.929 | 0.011 |
| ShellCheck (error+warning) | 0.273 | 0.079 | 0.122 | -0.140 | 0.488 | 0.174 |
| ShellCheck (error only) | 1.000 | 0.013 | 0.026 | 0.085 | 0.554 | 0.000 |

**False-positive rate: ACTE 0.011 vs ShellCheck 0.174 → ACTE achieves a 93.8% relative reduction in false positives.**

## Figures

- `../figures/roc_curve.png` — ROC curve (ACTE, test set)
- `../figures/pr_curve.png` — Precision-Recall curve (ACTE, test set)
- `../figures/ablation_f1.png` — F1 by ablation configuration
- `../figures/baseline_comparison.png` — ACTE vs ShellCheck
