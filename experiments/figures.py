"""Render ROC and Precision-Recall curves to PNG with matplotlib.

Uses the non-interactive 'Agg' backend so the harness runs headless. The
plotted points come straight from the measured test-set scores; nothing is
synthesized.
"""

from __future__ import annotations

import os
from typing import List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from experiments.metrics import pr_points, roc_points  # noqa: E402


def plot_roc(
    y_true: List[int],
    y_score: List[float],
    out_path: str,
    auc_value: float,
    title: str = "ACTE ROC Curve (test set)",
) -> str:
    fpr, tpr, _ = roc_points(y_true, y_score)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color="#1f77b4", lw=2, label=f"ACTE (AUC = {auc_value:.3f})")
    ax.plot([0, 1], [0, 1], color="grey", lw=1, linestyle="--", label="Random")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(title)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_pr(
    y_true: List[int],
    y_score: List[float],
    out_path: str,
    auc_value: float,
    title: str = "ACTE Precision-Recall Curve (test set)",
) -> str:
    precision, recall, _ = pr_points(y_true, y_score)
    baseline = sum(y_true) / len(y_true) if y_true else 0.0
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(recall, precision, color="#d62728", lw=2, label=f"ACTE (AUC = {auc_value:.3f})")
    ax.axhline(baseline, color="grey", lw=1, linestyle="--",
               label=f"No-skill ({baseline:.2f})")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title(title)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.legend(loc="lower left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_ablation_bar(
    labels: List[str],
    f1_scores: List[float],
    out_path: str,
    title: str = "Ablation: F1 by configuration (test set)",
) -> str:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = ["#2ca02c"] + ["#ff7f0e"] * (len(labels) - 1)
    bars = ax.bar(labels, f1_scores, color=colors)
    ax.set_ylabel("F1 score")
    ax.set_title(title)
    ax.set_ylim(0, 1.05)
    for b, v in zip(bars, f1_scores):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.3f}",
                ha="center", va="bottom", fontsize=9)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_cv_box(
    stratified_f1: List[float],
    grouped_f1: List[float],
    out_path: str,
    title: str = "Cross-validated F1 (per fold)",
) -> str:
    """Box/scatter of per-fold F1 for the two CV schemes."""
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    data = [stratified_f1, grouped_f1]
    labels = ["Stratified\nk-fold", "Leave-template-out\nk-fold"]
    bp = ax.boxplot(data, patch_artist=True, widths=0.5, showmeans=True)
    ax.set_xticks([1, 2])
    ax.set_xticklabels(labels)
    for patch, color in zip(bp["boxes"], ["#2ca02c", "#ff7f0e"]):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)
    # Overlay the individual fold points.
    import numpy as np
    for i, vals in enumerate(data, start=1):
        xs = np.random.default_rng(0).normal(i, 0.04, size=len(vals))
        ax.scatter(xs, vals, color="black", zorder=3, s=18, alpha=0.8)
    ax.set_ylabel("F1 score")
    ax.set_title(title)
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_real_world(
    metrics: dict,
    out_path: str,
    title: str = "Real-world external validation (train synthetic → test real)",
) -> str:
    """Bar chart of the headline metrics on the real-world holdout."""
    names = ["Precision", "Recall", "F1", "Accuracy", "FPR"]
    vals = [metrics["precision"], metrics["recall"], metrics["f1"],
            metrics["accuracy"], metrics["false_positive_rate"]]
    colors = ["#1f77b4", "#2ca02c", "#9467bd", "#17becf", "#d62728"]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    bars = ax.bar(names, vals, color=colors)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.3f}",
                ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, 1.08)
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_baseline_comparison(
    detectors: List[str],
    precision: List[float],
    recall: List[float],
    fpr: List[float],
    out_path: str,
    title: str = "ACTE vs ShellCheck baseline (test set)",
) -> str:
    import numpy as np

    x = np.arange(len(detectors))
    width = 0.25
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(x - width, precision, width, label="Precision", color="#1f77b4")
    ax.bar(x, recall, width, label="Recall", color="#2ca02c")
    ax.bar(x + width, fpr, width, label="False Positive Rate", color="#d62728")
    ax.set_xticks(x)
    ax.set_xticklabels(detectors)
    ax.set_ylim(0, 1.05)
    ax.set_title(title)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path
