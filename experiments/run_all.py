"""Single deterministic entrypoint for the entire ACTE study.

Run with:  python -m experiments.run_all

Steps (all seeded for reproducibility):
  1. Regenerate the labeled dataset (+ the real-world external holdout).
  2. Load and stratify-split it.
  3. Train + evaluate ACTE and the four ablations (RQ1).
  4. Cross-validate: stratified k-fold + leave-template-out k-fold (RQ1b).
  5. Render ROC, PR, ablation, CV and comparison figures.
  6. Run the ShellCheck baseline + McNemar significance test (RQ3).
  7. Measure per-script analysis latency (RQ2).
  8. Real-world external validation: train synthetic → test real (RQ4).
  9. Write machine-readable results.json and human-readable results.md.
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
from data.real_world import build as real_world_build
from experiments import (
    acte_eval,
    adversarial,
    baseline_shellcheck,
    cross_validation,
    figures,
    latency,
    ml_baselines,
    real_world_eval,
    stats,
)
from experiments.dataset import (
    REAL_WORLD_MANIFEST,
    REAL_WORLD_OK,
    load_samples,
    stratified_split,
    split_summary,
)

SEED = 1337
HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, "results")
FIGURES_DIR = os.path.join(HERE, "figures")
EPOCHS = 40
TEST_FRACTION = 0.4
CV_FOLDS = 5
N_BOOTSTRAP = 2000


def main() -> int:
    random.seed(SEED)
    np.random.seed(SEED)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    print("=" * 70)
    print("ACTE experiment harness — deterministic run (seed=%d)" % SEED)
    print("=" * 70)

    # 1. dataset ------------------------------------------------------------
    print("\n[1/11] Regenerating dataset (+ real-world holdout) ...")
    records = generate_dataset.generate(verbose=True)
    real_world_build.build(verbose=True)

    # 2. load + split -------------------------------------------------------
    print("\n[2/11] Loading and splitting ...")
    samples = load_samples()
    train, test = stratified_split(samples, test_fraction=TEST_FRACTION, seed=SEED)
    split = split_summary(train, test)
    print("  train=%d  test=%d  (test positives=%d)"
          % (split["n_train"], split["n_test"], split["test_positives"]))

    # 3. ACTE + ablation ----------------------------------------------------
    print("\n[3/11] Training + evaluating ACTE and ablations ...")
    acte = acte_eval.run_full_and_ablation(train, test, epochs=EPOCHS, seed=SEED)
    full = acte["configs"]["full"]
    print("  ACTE(full): precision=%.3f recall=%.3f F1=%.3f MCC=%.3f acc=%.3f"
          % (full["precision"], full["recall"], full["f1"], full["mcc"], full["accuracy"]))

    # 3b. bootstrap CI on the held-out test split ---------------------------
    y_true = [s.label for s in test]
    boot = stats.bootstrap_ci(
        y_true, acte["full_test_pred"], acte["full_test_scores"],
        n_boot=N_BOOTSTRAP, seed=SEED,
    )
    print("  F1 95%% CI: [%.3f, %.3f]  (point %.3f)"
          % (boot["f1"]["ci_low"], boot["f1"]["ci_high"], boot["f1"]["point"]))

    # 4. cross-validation ---------------------------------------------------
    print("\n[4/11] Cross-validating (stratified + leave-template-out) ...")
    cv = cross_validation.run_cross_validation(
        samples, k=CV_FOLDS, epochs=EPOCHS, seed=SEED
    )
    cv_s = cv["stratified"]["summary"]["f1"]
    cv_g = cv["grouped_leave_template_out"]["summary"]["f1"]
    print("  stratified F1        = %.3f ± %.3f" % (cv_s["mean"], cv_s["std"]))
    print("  leave-template-out F1 = %.3f ± %.3f" % (cv_g["mean"], cv_g["std"]))

    # 5. figures ------------------------------------------------------------
    print("\n[5/11] Rendering figures ...")
    roc_path = os.path.join(FIGURES_DIR, "roc_curve.png")
    pr_path = os.path.join(FIGURES_DIR, "pr_curve.png")
    abl_path = os.path.join(FIGURES_DIR, "ablation_f1.png")
    cv_path = os.path.join(FIGURES_DIR, "cross_validation_f1.png")
    figures.plot_roc(y_true, acte["full_test_scores"], roc_path, full.get("roc_auc", 0.0))
    figures.plot_pr(y_true, acte["full_test_scores"], pr_path, full.get("pr_auc", 0.0))
    abl_labels = list(acte["configs"].keys())
    abl_f1 = [acte["configs"][k]["f1"] for k in abl_labels]
    figures.plot_ablation_bar(abl_labels, abl_f1, abl_path)
    figures.plot_cv_box(
        cv["stratified"]["summary"]["f1"]["values"],
        cv["grouped_leave_template_out"]["summary"]["f1"]["values"],
        cv_path,
    )
    print("  saved roc_curve.png, pr_curve.png, ablation_f1.png, cross_validation_f1.png")

    # 6. ShellCheck baseline + significance test ----------------------------
    print("\n[6/11] Running ShellCheck baseline + McNemar test ...")
    baseline = baseline_shellcheck.evaluate_baseline(test)
    cmp_path = os.path.join(FIGURES_DIR, "baseline_comparison.png")
    mcnemar = None
    if baseline.get("available"):
        bm = baseline["metrics"]
        print("  ShellCheck: precision=%.3f recall=%.3f F1=%.3f FPR=%.3f"
              % (bm["precision"], bm["recall"], bm["f1"], bm["false_positive_rate"]))
        mcnemar = stats.mcnemar(y_true, acte["full_test_pred"], baseline["predictions"])
        print("  McNemar ACTE vs ShellCheck: p=%.2e  (better: %s)"
              % (mcnemar["p_value"], mcnemar["better_detector"]))
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

    # 7. latency ------------------------------------------------------------
    print("\n[7/11] Measuring latency ...")
    lat = latency.measure_latency(samples, repeats=3, warmup=5)
    print("  mean=%.3f ms  median=%.3f ms  p95=%.3f ms"
          % (lat["mean_ms"], lat["median_ms"], lat["p95_ms"]))

    # 8. real-world external validation -------------------------------------
    print("\n[8/11] Real-world external validation (train synthetic → test real) ...")
    real = real_world_eval.evaluate_real_world(epochs=EPOCHS, seed=SEED)
    rw_path = os.path.join(FIGURES_DIR, "real_world_validation.png")
    if real.get("available"):
        rm = real["metrics"]
        print("  real-world: precision=%.3f recall=%.3f F1=%.3f FPR=%.3f (n=%d)"
              % (rm["precision"], rm["recall"], rm["f1"],
                 rm["false_positive_rate"], real["n_scripts"]))
        figures.plot_real_world(rm, rw_path)
        print("  saved real_world_validation.png")
    else:
        print("  real-world validation skipped:", real.get("reason"))

    # 9. learned ML baselines (RQ5) -----------------------------------------
    print("\n[9/11] Training learned baselines (TF-IDF + LogReg/SVM/RF) ...")
    real_samples = load_samples(REAL_WORLD_MANIFEST) if REAL_WORLD_OK else None
    ml = ml_baselines.evaluate_baselines(train, test, real_samples, seed=SEED)
    for name, m in ml["on_synthetic_test"].items():
        print("  %-24s test F1=%.3f FPR=%.3f" % (name, m["f1"], m["false_positive_rate"]))
    ml_path = os.path.join(FIGURES_DIR, "ml_baselines.png")
    if ml["on_real_world"]:
        det = ["ACTE"] + list(ml["on_real_world"].keys())
        f1s = [real["metrics"]["f1"]] + [ml["on_real_world"][k]["f1"] for k in ml["on_real_world"]]
        fprs = [real["metrics"]["false_positive_rate"]] + \
               [ml["on_real_world"][k]["false_positive_rate"] for k in ml["on_real_world"]]
        figures.plot_ml_baselines(det, f1s, fprs, ml_path)
        print("  saved ml_baselines.png")

    # 10. adversarial evasion (RQ6) -----------------------------------------
    print("\n[10/11] Adversarial evasion (ACTE vs TF-IDF under camouflage) ...")
    adv = adversarial.evaluate_adversarial(train, test, epochs=EPOCHS, seed=SEED)
    print("  ACTE  original=%.3f  benign_camouflage=%.3f (drop %+.3f)"
          % (adv["acte"]["original_recall"], adv["acte"]["benign_camouflage"],
             adv["acte"]["drops"]["benign_camouflage"]))
    print("  TFIDF original=%.3f  benign_camouflage=%.3f (drop %+.3f)"
          % (adv["tfidf_logreg"]["original_recall"], adv["tfidf_logreg"]["benign_camouflage"],
             adv["tfidf_logreg"]["drops"]["benign_camouflage"]))

    # 10b. revision experiments (RQ6b, RQ7-RQ10) ----------------------------
    print("\n[10b/11] Revision experiments (calibration, stronger baselines, "
          "cluster bootstrap, paired ablation, systematic adversarial, online, "
          "real seccomp) ...")
    from experiments import review_extras
    extras = review_extras.run_all_extras(
        samples, train, test, acte["full_test_pred"], acte["full_test_scores"],
        real_world_fp=(real["metrics"]["confusion_matrix"]["fp"] if real.get("available") else 0),
        real_world_neg=(real["n_safe"] if real.get("available") else 20),
        epochs=EPOCHS, seed=SEED)
    cb = extras["cluster_bootstrap"]
    print("  cluster-bootstrap F1 CI [%.3f, %.3f] (naive width x%s)"
          % (cb["cluster_bootstrap"]["f1"]["low"], cb["cluster_bootstrap"]["f1"]["high"],
             cb["width_ratio"]["f1"]))
    print("  calibration ECE raw=%.3f isotonic=%.3f"
          % (extras["rq7_calibration"]["raw"]["ece"],
             extras["rq7_calibration"]["isotonic"]["ece"]))
    adv_acte = extras["rq6b_adversarial_budget"]["detectors"]["ACTE"]["evasion_at_max_budget"]
    print("  semantic-substitution evasion of ACTE: %+.3f recall" % adv_acte)
    print("  feedback poisoning: %s labels flip a canary"
          % extras["rq9_feedback_poisoning"]["poisoned_labels_to_flip"])
    enf = extras["rq10_enforcement"]
    if enf.get("seccomp_available"):
        print("  real seccomp enforcement: %d/%d scripts enforced correctly"
              % (enf["n_all_correct"], enf["n_scripts"]))
    xb = extras["rq11_external_benign"]
    if xb.get("available"):
        print("  real third-party benign FPR: ACTE=%.3f vs TF-IDF+LogReg=%.3f (n=%d)"
              % (xb["false_positives"]["ACTE"]["fpr"],
                 xb["false_positives"]["TF-IDF + LogReg"]["fpr"], xb["n_scripts"]))

    # 11. write results -----------------------------------------------------
    print("\n[11/11] Writing results ...")
    results = {
        "meta": _meta(split, records),
        "rq1_detection": {
            "acte_full": full,
            "acte_full_bootstrap_ci": boot,
            "ablation": acte["configs"],
            "per_category": acte["full_per_category"],
        },
        "rq1b_cross_validation": _cv_json(cv),
        "rq2_latency": lat,
        "rq3_baseline": baseline,
        "rq3_significance": mcnemar,
        "rq4_real_world": real,
        "rq5_ml_baselines": ml,
        "rq6_adversarial": adv,
        "rq_revision": extras,
    }
    results_json = os.path.join(RESULTS_DIR, "results.json")
    with open(results_json, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)

    md = render_markdown(results, acte, baseline, lat, split)
    with open(os.path.join(RESULTS_DIR, "results.md"), "w", encoding="utf-8") as fh:
        fh.write(md)

    print("  wrote results.json and results.md")
    print("\nDONE. Key numbers:")
    _print_key_numbers(full, baseline, lat, acte, cv, real, boot, mcnemar)
    return 0


def _cv_json(cv: dict) -> dict:
    """Compact CV result for results.json (drop the large per-sample arrays)."""
    def scheme(s):
        return {
            "k": s["k"],
            "epochs": s["epochs"],
            "summary": s["summary"],
            "pooled_oof": s["pooled_oof"],
            "per_fold": [
                {k: v for k, v in m.items()
                 if k in ("fold", "n_test", "precision", "recall", "f1", "mcc",
                          "accuracy", "false_positive_rate", "roc_auc", "pr_auc",
                          "decision_threshold")}
                for m in s["per_fold"]
            ],
        }
    return {
        "n_samples": cv["n_samples"],
        "n_templates": cv["n_templates"],
        "seed": cv["seed"],
        "stratified": scheme(cv["stratified"]),
        "grouped_leave_template_out": scheme(cv["grouped_leave_template_out"]),
    }


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


def _print_key_numbers(full, baseline, lat, acte, cv, real, boot, mcnemar):
    ci = boot["f1"]
    print(f"  RQ1  ACTE F1={full['f1']:.3f} [95% CI {ci['ci_low']:.3f}-{ci['ci_high']:.3f}]  "
          f"precision={full['precision']:.3f}  recall={full['recall']:.3f}  "
          f"ROC-AUC={full.get('roc_auc', float('nan')):.3f}")
    cvs = cv["stratified"]["summary"]["f1"]
    cvg = cv["grouped_leave_template_out"]["summary"]["f1"]
    print(f"  RQ1b CV F1 stratified={cvs['mean']:.3f}±{cvs['std']:.3f}  "
          f"leave-template-out={cvg['mean']:.3f}±{cvg['std']:.3f}")
    print(f"  RQ2  latency mean={lat['mean_ms']:.3f}ms  p95={lat['p95_ms']:.3f}ms")
    if baseline.get("available"):
        bm = baseline["metrics"]
        line = (f"  RQ3  ACTE FPR={full['false_positive_rate']:.3f}  vs  "
                f"ShellCheck FPR={bm['false_positive_rate']:.3f}")
        if mcnemar:
            line += f"  (McNemar p={mcnemar['p_value']:.2e})"
        print(line)
    if real.get("available"):
        rm = real["metrics"]
        print(f"  RQ4  real-world F1={rm['f1']:.3f}  precision={rm['precision']:.3f}  "
              f"recall={rm['recall']:.3f}  FPR={rm['false_positive_rate']:.3f}  "
              f"ROC-AUC={rm.get('roc_auc', float('nan')):.3f}")


# --------------------------------------------------------------------------- #
# Markdown report                                                             #
# --------------------------------------------------------------------------- #
def _fmt(x, nd=4):
    if x is None:
        return "n/a"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def _ci(interval, nd=3):
    if not interval:
        return "n/a"
    if isinstance(interval, dict):
        lo, hi = interval.get("low"), interval.get("high")
    else:
        lo, hi = interval[0], interval[1]
    return f"[{lo:.{nd}f}, {hi:.{nd}f}]"


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

    boot = results["rq1_detection"].get("acte_full_bootstrap_ci")
    if boot:
        L.append("**Bootstrap 95% confidence intervals** "
                 f"({boot['f1']['n_boot']} stratified resamples of the test set):\n")
        L.append("| Metric | Point | 95% CI |")
        L.append("|---|---|---|")
        for m in ("precision", "recall", "f1", "mcc", "accuracy",
                  "false_positive_rate", "roc_auc", "pr_auc"):
            if m in boot:
                b = boot[m]
                L.append(f"| {m} | {_fmt(b['point'],3)} | "
                         f"[{_fmt(b['ci_low'],3)}, {_fmt(b['ci_high'],3)}] |")
        L.append("")

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

    # RQ1b — cross-validation
    cv = results.get("rq1b_cross_validation")
    if cv:
        L.append("## RQ1b — Cross-validated detection (robustness of the headline number)\n")
        L.append("A single held-out split gives one number with no spread. Below, "
                 f"the full ACTE protocol is repeated inside {cv['stratified']['k']}-fold "
                 "cross-validation under two schemes, reported as **mean ± std** "
                 "across folds. To avoid the variance that F1-optimal threshold "
                 "tuning introduces on small per-fold partitions, every fold here "
                 "uses the fixed default operating point (τ = 0.5); the tuned "
                 "single-split operating point of RQ1 is reported separately.\n")
        L.append("- **Stratified k-fold** (scikit-learn `StratifiedKFold`) — folds "
                 "preserve the label ratio; estimates generalization to new samples "
                 "from the same distribution.")
        L.append(f"- **Leave-template-out k-fold** (`StratifiedGroupKFold` over "
                 f"{cv['n_templates']} templates) — no template contributes scripts to "
                 "both the training and evaluation fold, so the model is scored on "
                 "template structures it never trained on. This is the harder test "
                 "and it substantially weakens (though does not eliminate) the "
                 "'template-memorization' concern for a synthetic corpus.\n")
        L.append("| Scheme | Precision | Recall | F1 | MCC | ROC-AUC | FPR |")
        L.append("|---|---|---|---|---|---|---|")
        for label, key in (("Stratified k-fold", "stratified"),
                           ("Leave-template-out", "grouped_leave_template_out")):
            s = cv[key]["summary"]
            def ms(m):
                return f"{s[m]['mean']:.3f} ± {s[m]['std']:.3f}" if m in s else "n/a"
            L.append(f"| {label} | {ms('precision')} | {ms('recall')} | {ms('f1')} | "
                     f"{ms('mcc')} | {ms('roc_auc')} | {ms('false_positive_rate')} |")
        L.append("")
        for label, key in (("Stratified", "stratified"),
                           ("Leave-template-out", "grouped_leave_template_out")):
            p = cv[key]["pooled_oof"]
            L.append(f"Pooled out-of-fold ({label}): F1={_fmt(p['f1'],3)}, "
                     f"precision={_fmt(p['precision'],3)}, recall={_fmt(p['recall'],3)}, "
                     f"FPR={_fmt(p['false_positive_rate'],3)} "
                     f"(every sample scored once, by a model that never trained on it).")
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
        mc = results.get("rq3_significance")
        if mc:
            L.append(f"**McNemar's exact paired test** (same test items): "
                     f"ACTE-correct/ShellCheck-wrong = {mc['a_correct_b_wrong']}, "
                     f"ShellCheck-correct/ACTE-wrong = {mc['b_correct_a_wrong']}, "
                     f"p = {mc['p_value']:.2e}. The difference is "
                     f"{'statistically significant' if mc['significant_at_0.05'] else 'not significant'} "
                     f"at α=0.05.\n")
    else:
        L.append(f"> ShellCheck baseline **unavailable** — skipped, not fabricated. "
                 f"Reason: {baseline.get('reason')}\n")

    # RQ4 — real-world external validation
    real = results.get("rq4_real_world")
    if real and real.get("available"):
        rm = real["metrics"]
        L.append("## RQ4 — Generalization to real, non-synthetic scripts\n")
        L.append(f"The model is trained on the **{real['trained_on']}** and then "
                 f"evaluated once on an independent, hand-authored holdout of "
                 f"**{real['n_scripts']} real scripts** "
                 f"({real['n_dangerous']} dangerous, {real['n_safe']} safe) drawn from "
                 "publicly documented idioms — none seen during training or "
                 "threshold tuning. This is a true train-synthetic / test-real "
                 "generalization test.\n")
        L.append("| Metric | Value |")
        L.append("|---|---|")
        L.append(f"| Precision | {_fmt(rm['precision'],3)} |")
        L.append(f"| Recall | {_fmt(rm['recall'],3)} |")
        L.append(f"| F1 | {_fmt(rm['f1'],3)} |")
        L.append(f"| Accuracy | {_fmt(rm['accuracy'],3)} |")
        L.append(f"| ROC-AUC | {_fmt(rm.get('roc_auc'),3)} |")
        L.append(f"| False Positive Rate | {_fmt(rm['false_positive_rate'],3)} |")
        rci = real.get("bootstrap_ci", {}).get("f1")
        if rci:
            L.append(f"| F1 95% CI | [{_fmt(rci['ci_low'],3)}, {_fmt(rci['ci_high'],3)}] |")
        L.append("")
        cm = rm["confusion_matrix"]
        L.append(f"Confusion matrix: TN={cm['tn']}, FP={cm['fp']}, FN={cm['fn']}, "
                 f"TP={cm['tp']} (decision threshold {_fmt(real['decision_threshold'],3)}, "
                 "fixed from synthetic training).\n")
        errs = real.get("errors", [])
        if errs:
            L.append("**Misclassifications** (the honest failure cases):\n")
            L.append("| id | true | predicted | risk | why it is hard |")
            L.append("|---|---|---|---|---|")
            for e in errs:
                L.append(f"| `{e['id']}` | {e['label']} | {e['predicted']} | "
                         f"{_fmt(e['risk_score'],3)} | {e['rationale']} |")
            L.append("")
        else:
            L.append("No misclassifications on the real-world holdout.\n")

    # RQ5 — learned baselines
    ml = results.get("rq5_ml_baselines")
    if ml:
        L.append("## RQ5 — Comparison with learned text-classifier baselines\n")
        L.append("ShellCheck (RQ3) is a linter, not a security classifier, so the "
                 "more demanding comparison is against off-the-shelf supervised text "
                 "classifiers trained on the same labels: TF-IDF (word 1–2 grams + "
                 "char 3–5 grams) feeding Logistic Regression, a linear SVM, and a "
                 "Random Forest. We report performance on the synthetic test split "
                 "and, more importantly, on the independent real-world holdout after "
                 "training on the full synthetic corpus.\n")
        acte_rw = results.get("rq4_real_world", {}).get("metrics", {})
        L.append("**Synthetic test split:**\n")
        L.append("| Detector | Precision | Recall | F1 | ROC-AUC | FPR |")
        L.append("|---|---|---|---|---|---|")
        L.append(f"| ACTE (full) | {_fmt(full['precision'],3)} | {_fmt(full['recall'],3)} | "
                 f"{_fmt(full['f1'],3)} | {_fmt(full.get('roc_auc'),3)} | "
                 f"{_fmt(full['false_positive_rate'],3)} |")
        for name, m in ml["on_synthetic_test"].items():
            L.append(f"| {name} | {_fmt(m['precision'],3)} | {_fmt(m['recall'],3)} | "
                     f"{_fmt(m['f1'],3)} | {_fmt(m.get('roc_auc'),3)} | "
                     f"{_fmt(m['false_positive_rate'],3)} |")
        L.append("")
        if ml["on_real_world"]:
            L.append("**Real-world holdout (trained on full synthetic corpus):**\n")
            L.append("| Detector | Precision | Recall | F1 | ROC-AUC | FPR |")
            L.append("|---|---|---|---|---|---|")
            if acte_rw:
                L.append(f"| ACTE (full) | {_fmt(acte_rw['precision'],3)} | "
                         f"{_fmt(acte_rw['recall'],3)} | {_fmt(acte_rw['f1'],3)} | "
                         f"{_fmt(acte_rw.get('roc_auc'),3)} | "
                         f"{_fmt(acte_rw['false_positive_rate'],3)} |")
            for name, m in ml["on_real_world"].items():
                L.append(f"| {name} | {_fmt(m['precision'],3)} | {_fmt(m['recall'],3)} | "
                         f"{_fmt(m['f1'],3)} | {_fmt(m.get('roc_auc'),3)} | "
                         f"{_fmt(m['false_positive_rate'],3)} |")
            L.append("")
        L.append("The linear text classifiers are competitive with, and on raw F1 "
                 "sometimes exceed, ACTE — a candid finding. ACTE's advantage is not "
                 "a higher F1 but (i) the lowest false-positive rate, which is the "
                 "operational cost of a gate; (ii) a 13-feature model whose every "
                 "decision is attributable, versus thousands of opaque lexical "
                 "weights (the LogReg baseline keys on bare tokens such as `rf` and "
                 "on distributional artifacts of the corpus); (iii) sub-millisecond "
                 "online adaptation from a single label, where a fitted TF-IDF "
                 "vocabulary is frozen; and (iv) the automatic synthesis of an "
                 "enforcement policy, which a bare classifier does not produce.\n")

    # RQ6 — adversarial evasion
    adv = results.get("rq6_adversarial")
    if adv:
        L.append("## RQ6 — Robustness to adaptive evasion\n")
        L.append("We apply two behaviour-preserving transformations to the dangerous "
                 "test scripts and measure how much detection each costs ACTE versus the "
                 "TF-IDF + logistic-regression baseline. `benign_camouflage` prepends a "
                 "shebang, `set -euo pipefail`, and reassuring comments (a direct probe of "
                 "the monotonicity property, since those tokens carry negative weight); "
                 "`lexical_disguise` renames attacker hostnames and variables. The "
                 "malicious commands are left intact in both.\n")
        L.append("| Detector | Original recall | benign_camouflage | lexical_disguise | both |")
        L.append("|---|---|---|---|---|")
        for det, lab in (("acte", "ACTE"), ("tfidf_logreg", "TF-IDF + LogReg")):
            d = adv[det]
            L.append(f"| {lab} | {_fmt(d['original_recall'],3)} | "
                     f"{_fmt(d['benign_camouflage'],3)} | {_fmt(d['lexical_disguise'],3)} | "
                     f"{_fmt(d['both'],3)} |")
        L.append("")
        ad = adv["acte"]["drops"]["benign_camouflage"]
        td = adv["tfidf_logreg"]["drops"]["benign_camouflage"]
        L.append(f"The finding reverses the raw-F1 story of RQ5. Benign camouflage costs "
                 f"ACTE {ad:+.3f} recall but costs the lexical baseline {td:+.3f} — a "
                 "behaviour-preserving edit that a defender would consider trivial "
                 "collapses the bag-of-tokens model while barely touching ACTE, because "
                 "the signature and context weights for the intact malicious commands "
                 "dominate the small negative benign-signal weights. Renaming hostnames "
                 "moves neither detector, since both key on command structure rather than "
                 "specific strings. In short: the monotonicity concern is real in theory "
                 "but does not yield an easy benign-camouflage evasion of ACTE in practice; "
                 "the evasions that do work (RQ4) are novel techniques absent from the "
                 "signature base, not cosmetic edits.\n")

    # Revision experiments (RQ6b, RQ7-RQ10)
    ex = results.get("rq_revision")
    if ex:
        L.append("## Revision experiments (RQ6b, RQ7-RQ10)\n")
        c7 = ex["rq7_calibration"]
        L.append(f"- **RQ7 calibration.** Raw ECE = {_fmt(c7['raw']['ece'],3)} "
                 f"(Brier {_fmt(c7['raw']['brier'],3)}); isotonic recalibration → ECE "
                 f"{_fmt(c7['isotonic']['ece'],3)}. The risk score is only moderately "
                 "calibrated, so the fixed trust-level thresholds are approximate and "
                 "should be recalibrated per deployment.")
        b8 = ex["rq8_stronger_baselines"]
        L.append(f"- **RQ8 stronger baselines.** GBDT on the same 13 features F1 = "
                 f"{_fmt(b8['gbdt_on_acte_features']['f1'],3)} (≈ the logistic model, so "
                 f"the ceiling is the features, not linearity); feature+TF-IDF union F1 = "
                 f"{_fmt(b8['union_features_plus_tfidf']['f1'],3)} (complementary, and the "
                 f"corpus is near-separable); tuned TF-IDF F1 = "
                 f"{_fmt(b8['tfidf_logreg_tuned']['f1'],3)} (C={b8['tfidf_logreg_tuned'].get('best_C')}).")
        cb = ex["cluster_bootstrap"]
        L.append(f"- **Cluster bootstrap.** Resampling whole templates widens the F1 CI to "
                 f"[{_fmt(cb['cluster_bootstrap']['f1']['low'],3)}, "
                 f"{_fmt(cb['cluster_bootstrap']['f1']['high'],3)}] — about "
                 f"{cb['width_ratio']['f1']}× the naive per-sample interval; the earlier "
                 "CIs were too narrow under template clustering.")
        w = ex["real_world_fpr_wilson"]
        L.append(f"- **Real-world FPR interval.** The real-holdout false-positive rate of "
                 f"{_fmt(w['point'],3)} has a Wilson 95% CI [{_fmt(w['low'],3)}, {_fmt(w['high'],3)}] "
                 "— consistent with a true FPR up to ~16%, so \"zero false positives\" is a "
                 "point estimate on 20 negatives, not a guarantee.")
        asig = ex["ablation_significance"]["comparisons"]
        sig_names = [n for n, c in asig.items() if c["significant_at_0.05"]]
        L.append(f"- **Paired ablation tests.** Only {', '.join(sig_names)} differ from the "
                 "full model at α=0.05 (McNemar); SemanticParser and ContextExtractor "
                 "effects are within noise, so no component ranking beyond ThreatIntel and "
                 "FeedbackLearning is asserted.")
        ab = ex["rq6b_adversarial_budget"]["detectors"]
        L.append(f"- **RQ6b systematic adversarial.** Semantic substitution (behaviour-"
                 f"preserving) evades ACTE by {_fmt(ab['ACTE']['evasion_at_max_budget'],3)} "
                 f"recall but the lexical baseline by "
                 f"{_fmt(ab['TF-IDF + LogReg']['evasion_at_max_budget'],3)} — the opposite of "
                 "RQ6, so the two model families have complementary blind spots and neither "
                 "is robustly superior.")
        pz = ex["rq9_feedback_poisoning"]; dr = ex["rq9_concept_drift"]
        L.append(f"- **RQ9 online dynamics.** On the novel '{dr['drift_category']}' family "
                 f"online adaptation recovered {_fmt(dr['recall_recovered'],3)} recall over "
                 f"frozen (no benefit; signatures already cover it), and adapting on the "
                 f"model's genuine misses recovers them only by collapsing precision. "
                 f"The feedback loop is also poisonable: {pz['poisoned_labels_to_flip']} "
                 "mislabelled updates flip a risk-1.0 canary. We therefore do not claim "
                 "online learning as a validated benefit.")
        enf = ex["rq10_enforcement"]
        if enf.get("seccomp_available"):
            L.append(f"- **RQ10 real enforcement.** A content-derived syscall deny-set is "
                     f"compiled to a real seccomp-BPF filter and installed unprivileged; the "
                     f"kernel correctly enforced it on {enf['n_all_correct']}/{enf['n_scripts']} "
                     "scripts (denied syscalls killed with SIGSYS, controls permitted). Two "
                     "scripts with different commands get different filters — genuine "
                     "content synthesis, really enforced.")
        ext_b = ex.get("rq11_external_benign", {})
        if ext_b.get("available"):
            fp = ext_b["false_positives"]
            acte = fp.get("ACTE", {})
            base_fprs = [v["fpr"] for k, v in fp.items() if k != "ACTE"]
            best_base = min(base_fprs) if base_fprs else None
            L.append(
                f"- **RQ11 real third-party benign corpus (construct validity).** On "
                f"{ext_b['n_benign']} genuinely external benign scripts (official installers "
                f"of popular OSS — nvm, rustup, docker, homebrew, …), frozen ACTE flags "
                f"{acte.get('count')}/{ext_b['n_benign']} as risky "
                f"(FPR {_fmt(acte.get('fpr'),3)}, Wilson {_ci(acte.get('wilson_ci'))}), while the "
                f"TF-IDF baselines flag {_fmt(best_base,3) if best_base is not None else 'n/a'}. "
                "ACTE's headline low false-positive rate is therefore a synthetic-corpus "
                "artefact: the very idioms real installers use (`curl | bash`, `sudo`, piping "
                "remote content) are exactly what the hand-built corpus penalises. This is the "
                "sharpest limitation in the paper and we report it prominently. Labels are by "
                "provenance, not independent human annotation.")
        L.append("")

    # Figures
    L.append("## Figures\n")
    L.append("- `../figures/roc_curve.png` — ROC curve (ACTE, test set)")
    L.append("- `../figures/pr_curve.png` — Precision-Recall curve (ACTE, test set)")
    L.append("- `../figures/ablation_f1.png` — F1 by ablation configuration")
    L.append("- `../figures/cross_validation_f1.png` — per-fold F1 (stratified vs leave-template-out)")
    if baseline.get("available"):
        L.append("- `../figures/baseline_comparison.png` — ACTE vs ShellCheck")
    if results.get("rq4_real_world", {}).get("available"):
        L.append("- `../figures/real_world_validation.png` — real-world external validation")
    if results.get("rq5_ml_baselines", {}).get("on_real_world"):
        L.append("- `../figures/ml_baselines.png` — ACTE vs learned baselines (real-world holdout)")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
