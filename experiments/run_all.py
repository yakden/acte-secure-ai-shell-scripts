"""Single deterministic entrypoint for the entire ACTE study.

Run with:  python -m experiments.run_all

Steps (all seeded for reproducibility):
  1. Regenerate the labeled dataset.
  2. Load and stratify-split it.
  3. Train + evaluate ACTE and the four ablations (RQ1).
  4. Render ROC, PR, ablation and baseline-comparison figures.
  5. Run the ShellCheck baseline on the same test split (RQ3).
  6. Measure per-script analysis latency (RQ2).
  7. Write machine-readable results.json and human-readable results.md.
"""

from __future__ import annotations

import json
import os
import platform
import random
import sys
from datetime import datetime, timezone

import numpy as np

from data import generate_dataset
from experiments import acte_eval, baseline_shellcheck, figures, latency
from experiments.dataset import load_samples, stratified_split, split_summary

SEED = 1337
HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, "results")
FIGURES_DIR = os.path.join(HERE, "figures")
EPOCHS = 40
TEST_FRACTION = 0.4


def main() -> int:
    random.seed(SEED)
    np.random.seed(SEED)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    print("=" * 70)
    print("ACTE experiment harness — deterministic run (seed=%d)" % SEED)
    print("=" * 70)

    # 1. dataset ------------------------------------------------------------
    print("\n[1/7] Regenerating dataset ...")
    records = generate_dataset.generate(verbose=True)

    # 2. load + split -------------------------------------------------------
    print("\n[2/7] Loading and splitting ...")
    samples = load_samples()
    train, test = stratified_split(samples, test_fraction=TEST_FRACTION, seed=SEED)
    split = split_summary(train, test)
    print("  train=%d  test=%d  (test positives=%d)"
          % (split["n_train"], split["n_test"], split["test_positives"]))

    # 3. ACTE + ablation ----------------------------------------------------
    print("\n[3/7] Training + evaluating ACTE and ablations ...")
    acte = acte_eval.run_full_and_ablation(train, test, epochs=EPOCHS, seed=SEED)
    full = acte["configs"]["full"]
    print("  ACTE(full): precision=%.3f recall=%.3f F1=%.3f MCC=%.3f acc=%.3f"
          % (full["precision"], full["recall"], full["f1"], full["mcc"], full["accuracy"]))

    # 4. figures ------------------------------------------------------------
    print("\n[4/7] Rendering figures ...")
    y_true = [s.label for s in test]
    roc_path = os.path.join(FIGURES_DIR, "roc_curve.png")
    pr_path = os.path.join(FIGURES_DIR, "pr_curve.png")
    abl_path = os.path.join(FIGURES_DIR, "ablation_f1.png")
    figures.plot_roc(y_true, acte["full_test_scores"], roc_path, full.get("roc_auc", 0.0))
    figures.plot_pr(y_true, acte["full_test_scores"], pr_path, full.get("pr_auc", 0.0))
    abl_labels = list(acte["configs"].keys())
    abl_f1 = [acte["configs"][k]["f1"] for k in abl_labels]
    figures.plot_ablation_bar(abl_labels, abl_f1, abl_path)
    print("  saved roc_curve.png, pr_curve.png, ablation_f1.png")

    # 5. ShellCheck baseline ------------------------------------------------
    print("\n[5/7] Running ShellCheck baseline ...")
    baseline = baseline_shellcheck.evaluate_baseline(test)
    cmp_path = os.path.join(FIGURES_DIR, "baseline_comparison.png")
    if baseline.get("available"):
        bm = baseline["metrics"]
        print("  ShellCheck: precision=%.3f recall=%.3f F1=%.3f FPR=%.3f"
              % (bm["precision"], bm["recall"], bm["f1"], bm["false_positive_rate"]))
        figures.plot_baseline_comparison(
            ["ACTE", "ShellCheck"],
            [full["precision"], bm["precision"]],
            [full["recall"], bm["recall"]],
            [full["false_positive_rate"], bm["false_positive_rate"]],
            cmp_path,
        )
        print("  saved baseline_comparison.png")
    else:
        print("  ShellCheck UNAVAILABLE — baseline skipped (not fabricated):",
              baseline.get("reason"))

    # 6. latency ------------------------------------------------------------
    print("\n[6/7] Measuring latency ...")
    lat = latency.measure_latency(samples, repeats=3, warmup=5)
    print("  mean=%.3f ms  median=%.3f ms  p95=%.3f ms"
          % (lat["mean_ms"], lat["median_ms"], lat["p95_ms"]))

    # 7. write results ------------------------------------------------------
    print("\n[7/7] Writing results ...")
    results = {
        "meta": _meta(split, records),
        "rq1_detection": {
            "acte_full": full,
            "ablation": acte["configs"],
            "per_category": acte["full_per_category"],
        },
        "rq2_latency": lat,
        "rq3_baseline": baseline,
    }
    results_json = os.path.join(RESULTS_DIR, "results.json")
    with open(results_json, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)

    md = render_markdown(results, acte, baseline, lat, split)
    with open(os.path.join(RESULTS_DIR, "results.md"), "w", encoding="utf-8") as fh:
        fh.write(md)

    print("  wrote results.json and results.md")
    print("\nDONE. Key numbers:")
    _print_key_numbers(full, baseline, lat, acte)
    return 0


def _meta(split, records) -> dict:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "epochs": EPOCHS,
        "test_fraction": TEST_FRACTION,
        "n_samples": len(records),
        "split": split,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "note": "All metrics are produced by a real, reproducible run of the ACTE prototype.",
    }


def _print_key_numbers(full, baseline, lat, acte):
    print(f"  RQ1  ACTE F1={full['f1']:.3f}  precision={full['precision']:.3f}  "
          f"recall={full['recall']:.3f}  MCC={full['mcc']:.3f}  "
          f"ROC-AUC={full.get('roc_auc', float('nan')):.3f}")
    print(f"  RQ2  latency mean={lat['mean_ms']:.3f}ms  p95={lat['p95_ms']:.3f}ms")
    if baseline.get("available"):
        bm = baseline["metrics"]
        print(f"  RQ3  ACTE FPR={full['false_positive_rate']:.3f}  vs  "
              f"ShellCheck FPR={bm['false_positive_rate']:.3f}")


# --------------------------------------------------------------------------- #
# Markdown report                                                             #
# --------------------------------------------------------------------------- #
def _fmt(x, nd=4):
    if x is None:
        return "n/a"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def render_markdown(results, acte, baseline, lat, split) -> str:
    full = results["rq1_detection"]["acte_full"]
    meta = results["meta"]
    L = []
    L.append("# ACTE Experiment Results\n")
    L.append("> All numbers below were produced by a real, reproducible run of the "
             "ACTE prototype (`python -m experiments.run_all`). Nothing is hardcoded.\n")
    L.append(f"- Generated (UTC): `{meta['generated_at_utc']}`")
    L.append(f"- Seed: `{meta['seed']}`  |  Training epochs: `{meta['epochs']}`  "
             f"|  Test fraction: `{meta['test_fraction']}`")
    L.append(f"- Python `{meta['python']}`  |  Platform `{meta['platform']}`")
    L.append(f"- Dataset: **{meta['n_samples']} samples** "
             f"(train={split['n_train']}, test={split['n_test']}, "
             f"test positives={split['test_positives']})\n")

    # Split table
    L.append("## Dataset split by category\n")
    L.append("| Category | Train safe | Train dangerous | Test safe | Test dangerous |")
    L.append("|---|---|---|---|---|")
    cats = sorted(set(list(split["train_by_category"]) + list(split["test_by_category"])))
    for c in cats:
        tr = split["train_by_category"].get(c, {"safe": 0, "dangerous": 0})
        te = split["test_by_category"].get(c, {"safe": 0, "dangerous": 0})
        L.append(f"| {c} | {tr['safe']} | {tr['dangerous']} | {te['safe']} | {te['dangerous']} |")
    L.append("")

    # RQ1
    L.append("## RQ1 — Detection accuracy of dangerous (AI-generated) shell scripts\n")
    cm = full["confusion_matrix"]
    L.append("**ACTE (full model) on held-out test set:**\n")
    L.append("| Metric | Value |")
    L.append("|---|---|")
    L.append(f"| Precision | {_fmt(full['precision'])} |")
    L.append(f"| Recall | {_fmt(full['recall'])} |")
    L.append(f"| F1 | {_fmt(full['f1'])} |")
    L.append(f"| MCC | {_fmt(full['mcc'])} |")
    L.append(f"| Accuracy | {_fmt(full['accuracy'])} |")
    L.append(f"| ROC-AUC | {_fmt(full.get('roc_auc'))} |")
    L.append(f"| PR-AUC | {_fmt(full.get('pr_auc'))} |")
    L.append(f"| False Positive Rate | {_fmt(full['false_positive_rate'])} |")
    L.append(f"| False Negative Rate | {_fmt(full['false_negative_rate'])} |")
    L.append(f"| Decision threshold (tuned) | {_fmt(full.get('decision_threshold'))} |")
    L.append("")
    L.append(f"Confusion matrix (test): TN={cm['tn']}, FP={cm['fp']}, "
             f"FN={cm['fn']}, TP={cm['tp']}\n")
    if "training" in full:
        tr = full["training"]
        L.append(f"Online learning moved the model: loss {_fmt(tr['initial_loss'])} → "
                 f"{_fmt(tr['final_loss'])} over {tr['epochs']} epochs "
                 f"(‖Δweights‖ = {_fmt(tr['weight_delta_norm'])}).\n")

    # Per-category
    L.append("### Per-category detection (ACTE full)\n")
    L.append("| Category | n | dangerous | safe | Recall (dangerous) | FPR (safe) |")
    L.append("|---|---|---|---|---|---|")
    for cat, d in results["rq1_detection"]["per_category"].items():
        L.append(f"| {cat} | {d['n']} | {d['n_dangerous']} | {d['n_safe']} | "
                 f"{_fmt(d['recall_dangerous'], 3)} | {_fmt(d['false_positive_rate_safe'], 3)} |")
    L.append("")

    # Ablation
    L.append("## Ablation study — contribution of each component\n")
    L.append("Each configuration is trained and evaluated with the identical "
             "protocol; the drop versus `full` quantifies the disabled component's "
             "contribution.\n")
    L.append("| Configuration | Precision | Recall | F1 | MCC | Accuracy | FPR | ROC-AUC |")
    L.append("|---|---|---|---|---|---|---|---|")
    fullf1 = full["f1"]
    for name, m in results["rq1_detection"]["ablation"].items():
        L.append(f"| {name} | {_fmt(m['precision'],3)} | {_fmt(m['recall'],3)} | "
                 f"{_fmt(m['f1'],3)} | {_fmt(m['mcc'],3)} | {_fmt(m['accuracy'],3)} | "
                 f"{_fmt(m['false_positive_rate'],3)} | {_fmt(m.get('roc_auc'),3)} |")
    L.append("")
    L.append("**F1 delta vs full model:**\n")
    L.append("| Disabled component | F1 | Δ F1 vs full |")
    L.append("|---|---|---|")
    for name, m in results["rq1_detection"]["ablation"].items():
        if name == "full":
            continue
        L.append(f"| {name} | {_fmt(m['f1'],3)} | {_fmt(m['f1'] - fullf1, 3)} |")
    L.append("")

    # RQ2
    L.append("## RQ2 — Computational cost (per-script analysis latency)\n")
    L.append("| Statistic | Milliseconds |")
    L.append("|---|---|")
    L.append(f"| Mean | {_fmt(lat['mean_ms'],3)} |")
    L.append(f"| Median | {_fmt(lat['median_ms'],3)} |")
    L.append(f"| p95 | {_fmt(lat['p95_ms'],3)} |")
    L.append(f"| p99 | {_fmt(lat['p99_ms'],3)} |")
    L.append(f"| Min | {_fmt(lat['min_ms'],3)} |")
    L.append(f"| Max | {_fmt(lat['max_ms'],3)} |")
    L.append(f"| Stdev | {_fmt(lat['stdev_ms'],3)} |")
    L.append(f"| Throughput (scripts/s) | {_fmt(lat['throughput_scripts_per_sec'],1)} |")
    L.append(f"\nMeasured over {lat['n_scripts']} scripts, "
             f"{lat['repeats_per_script']} repeats each (min taken).\n")

    # RQ3
    L.append("## RQ3 — False-positive reduction vs the ShellCheck baseline\n")
    if baseline.get("available"):
        bm = baseline["metrics"]
        L.append(f"ShellCheck version `{baseline['version']}`. "
                 f"Mapping: *{baseline['mapping']}*. "
                 f"Mean findings/script: {_fmt(baseline['mean_findings_per_script'],2)}.\n")
        L.append("| Detector | Precision | Recall | F1 | MCC | Accuracy | FPR |")
        L.append("|---|---|---|---|---|---|---|")
        L.append(f"| ACTE (full) | {_fmt(full['precision'],3)} | {_fmt(full['recall'],3)} | "
                 f"{_fmt(full['f1'],3)} | {_fmt(full['mcc'],3)} | {_fmt(full['accuracy'],3)} | "
                 f"{_fmt(full['false_positive_rate'],3)} |")
        L.append(f"| ShellCheck (error+warning) | {_fmt(bm['precision'],3)} | "
                 f"{_fmt(bm['recall'],3)} | {_fmt(bm['f1'],3)} | {_fmt(bm['mcc'],3)} | "
                 f"{_fmt(bm['accuracy'],3)} | {_fmt(bm['false_positive_rate'],3)} |")
        be = baseline["metrics_error_only"]
        L.append(f"| ShellCheck (error only) | {_fmt(be['precision'],3)} | "
                 f"{_fmt(be['recall'],3)} | {_fmt(be['f1'],3)} | {_fmt(be['mcc'],3)} | "
                 f"{_fmt(be['accuracy'],3)} | {_fmt(be['false_positive_rate'],3)} |")
        L.append("")
        fpr_acte = full["false_positive_rate"]
        fpr_sc = bm["false_positive_rate"]
        if fpr_sc > 0:
            reduction = (fpr_sc - fpr_acte) / fpr_sc * 100.0
            L.append(f"**False-positive rate: ACTE {_fmt(fpr_acte,3)} vs "
                     f"ShellCheck {_fmt(fpr_sc,3)} → ACTE achieves a "
                     f"{reduction:.1f}% relative reduction in false positives.**\n")
        else:
            L.append(f"**False-positive rate: ACTE {_fmt(fpr_acte,3)} vs "
                     f"ShellCheck {_fmt(fpr_sc,3)}.**\n")
    else:
        L.append(f"> ShellCheck baseline **unavailable** — skipped, not fabricated. "
                 f"Reason: {baseline.get('reason')}\n")

    # Figures
    L.append("## Figures\n")
    L.append("- `../figures/roc_curve.png` — ROC curve (ACTE, test set)")
    L.append("- `../figures/pr_curve.png` — Precision-Recall curve (ACTE, test set)")
    L.append("- `../figures/ablation_f1.png` — F1 by ablation configuration")
    if baseline.get("available"):
        L.append("- `../figures/baseline_comparison.png` — ACTE vs ShellCheck")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
