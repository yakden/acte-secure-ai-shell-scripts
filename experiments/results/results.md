# ACTE Experiment Results

> All numbers below were produced by a real, reproducible run of the ACTE prototype (`python -m experiments.run_all`). Nothing is hardcoded.

- Generated (UTC): `2026-07-02T06:10:34.239903+00:00`
- Seed: `1337`  |  Training epochs: `40`  |  Test fraction: `0.4`
- Python `3.11.15`  |  Platform `Linux-6.18.5-x86_64-with-glibc2.39`
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

**Bootstrap 95% confidence intervals** (2000 stratified resamples of the test set):

| Metric | Point | 95% CI |
|---|---|---|
| precision | 0.985 | [0.953, 1.000] |
| recall | 0.855 | [0.776, 0.934] |
| f1 | 0.915 | [0.861, 0.959] |
| mcc | 0.861 | [0.784, 0.930] |
| accuracy | 0.929 | [0.887, 0.964] |
| false_positive_rate | 0.011 | [0.000, 0.033] |
| roc_auc | 0.976 | [0.951, 0.994] |
| pr_auc | 0.978 | [0.957, 0.994] |

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

## RQ1b — Cross-validated detection (robustness of the headline number)

A single held-out split gives one number with no spread. Below, the full ACTE protocol is repeated inside 5-fold cross-validation under two schemes, reported as **mean ± std** across folds.

- **Stratified k-fold** — folds balanced by (category, label); estimates generalization to new samples from the same distribution.
- **Leave-template-out k-fold** — folds split by generating template (of 70 templates), so no template appears in both train and test; the harder test of generalization to unseen script structures, and the direct rebuttal to the 'template memorization' objection.

| Scheme | Precision | Recall | F1 | MCC | ROC-AUC | FPR |
|---|---|---|---|---|---|---|
| Stratified k-fold | 0.994 ± 0.011 | 0.831 ± 0.058 | 0.904 ± 0.033 | 0.849 ± 0.042 | 0.947 ± 0.021 | 0.004 ± 0.009 |
| Leave-template-out | 0.875 ± 0.201 | 0.789 ± 0.217 | 0.815 ± 0.191 | 0.722 ± 0.244 | 0.926 ± 0.071 | 0.076 ± 0.085 |

Pooled out-of-fold (Stratified): F1=0.905, precision=0.994, recall=0.832, FPR=0.004 (every sample scored once, by a model that never trained on it).
Pooled out-of-fold (Leave-template-out): F1=0.817, precision=0.847, recall=0.789, FPR=0.117 (every sample scored once, by a model that never trained on it).

## RQ2 — Computational cost (per-script analysis latency)

| Statistic | Milliseconds |
|---|---|
| Mean | 0.492 |
| Median | 0.462 |
| p95 | 0.941 |
| p99 | 1.111 |
| Min | 0.202 |
| Max | 1.167 |
| Stdev | 0.192 |
| Throughput (scripts/s) | 2033.0 |

Measured over 420 scripts, 3 repeats each (min taken).

## RQ3 — False-positive reduction vs the ShellCheck baseline

ShellCheck version `0.9.0`. Mapping: *dangerous if any finding level in {error, warning}*. Mean findings/script: 0.27.

| Detector | Precision | Recall | F1 | MCC | Accuracy | FPR |
|---|---|---|---|---|---|---|
| ACTE (full) | 0.985 | 0.855 | 0.915 | 0.861 | 0.929 | 0.011 |
| ShellCheck (error+warning) | 0.273 | 0.079 | 0.122 | -0.140 | 0.488 | 0.174 |
| ShellCheck (error only) | 1.000 | 0.013 | 0.026 | 0.085 | 0.554 | 0.000 |

**False-positive rate: ACTE 0.011 vs ShellCheck 0.174 → ACTE achieves a 93.8% relative reduction in false positives.**

**McNemar's exact paired test** (same test items): ACTE-correct/ShellCheck-wrong = 75, ShellCheck-correct/ACTE-wrong = 1, p = 2.04e-21. The difference is statistically significant at α=0.05.

## RQ4 — Generalization to real, non-synthetic scripts

The model is trained on the **full synthetic corpus (420 samples)** and then evaluated once on an independent, hand-authored holdout of **41 real scripts** (21 dangerous, 20 safe) drawn from publicly documented idioms — none seen during training or threshold tuning. This is a true train-synthetic / test-real generalization test.

| Metric | Value |
|---|---|
| Precision | 1.000 |
| Recall | 0.905 |
| F1 | 0.950 |
| Accuracy | 0.951 |
| ROC-AUC | 0.956 |
| False Positive Rate | 0.000 |
| F1 95% CI | [0.865, 1.000] |

Confusion matrix: TN=20, FP=0, FN=2, TP=19 (decision threshold 0.319, fixed from synthetic training).

**Misclassifications** (the honest failure cases):

| id | true | predicted | risk | why it is hard |
|---|---|---|---|---|
| `rw_danger_perl_revshell` | 1 | 0 | 0.085 | Perl reverse shell connecting back to an attacker and exec'ing /bin/sh. |
| `rw_danger_find_delete` | 1 | 0 | 0.155 | Deletes every file from root downward, sidestepping literal 'rm -rf /'. |

## Figures

- `../figures/roc_curve.png` — ROC curve (ACTE, test set)
- `../figures/pr_curve.png` — Precision-Recall curve (ACTE, test set)
- `../figures/ablation_f1.png` — F1 by ablation configuration
- `../figures/cross_validation_f1.png` — per-fold F1 (stratified vs leave-template-out)
- `../figures/baseline_comparison.png` — ACTE vs ShellCheck
- `../figures/real_world_validation.png` — real-world external validation
