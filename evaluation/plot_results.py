"""
Generate publication-style charts from evaluation CSV outputs.

Run the comparison scripts first, then:
    python evaluation/plot_results.py
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def require_matplotlib():
    os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/qztn-matplotlib")
    os.environ.setdefault("XDG_CACHE_HOME", "/private/tmp/qztn-cache")
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("matplotlib is required for plotting. Install requirements.txt first.") from exc
    return plt


def plot_classifier_summary(plt) -> None:
    path = RESULTS_DIR / "classifier_comparison.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    summary = df.groupby("model")["f1_macro"].mean().sort_values()
    ax = summary.plot(kind="barh", color="#2f6f73", figsize=(7, 4))
    ax.set_title("Classifier Macro-F1 Comparison")
    ax.set_xlabel("Macro-F1")
    ax.set_ylabel("")
    ax.set_xlim(0, 1)
    ax.figure.tight_layout()
    ax.figure.savefig(RESULTS_DIR / "classifier_f1.png", dpi=200)
    plt.close(ax.figure)


def plot_trust_summary(plt) -> None:
    path = RESULTS_DIR / "trust_model_summary.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    pivot = df.pivot(index="variant", columns="scenario", values="block_rate")
    ax = pivot.plot(kind="bar", figsize=(8, 4), color=["#4c78a8", "#c44e52", "#72b7b2"])
    ax.set_title("Trust Model Block Rate by Scenario")
    ax.set_xlabel("")
    ax.set_ylabel("Block Rate")
    ax.set_ylim(0, 1)
    ax.legend(title="Scenario")
    ax.figure.tight_layout()
    ax.figure.savefig(RESULTS_DIR / "trust_model_block_rate.png", dpi=200)
    plt.close(ax.figure)


def plot_ablation_summary(plt) -> None:
    path = RESULTS_DIR / "ablation_summary.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    ax = df.plot(x="ablation_id", y=["tpr", "fpr"], kind="bar", figsize=(8, 4), color=["#2f6f73", "#c44e52"])
    ax.set_title("Ablation Detection Tradeoff")
    ax.set_xlabel("Ablation")
    ax.set_ylabel("Rate")
    ax.set_ylim(0, 1)
    ax.figure.tight_layout()
    ax.figure.savefig(RESULTS_DIR / "ablation_tpr_fpr.png", dpi=200)
    plt.close(ax.figure)


def main() -> None:
    plt = require_matplotlib()
    plot_classifier_summary(plt)
    plot_trust_summary(plt)
    plot_ablation_summary(plt)
    print(f"Wrote charts to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
