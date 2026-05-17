"""
Compare classical baselines against the QSVM/VQC on identical processed data.

Outputs:
- evaluation/results/classifier_comparison.csv
- evaluation/results/classifier_comparison_summary.md

Run:
    python evaluation/compare_classifiers.py
    python evaluation/compare_classifiers.py --skip-qsvm
"""
from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.infrastructure import config  # noqa: E402

RESULTS_DIR = ROOT / "evaluation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_data(max_samples: int | None) -> tuple[np.ndarray, np.ndarray]:
    X = np.load(Path(config.PROCESSED_DATA_DIR) / "X.npy")
    y = np.load(Path(config.PROCESSED_DATA_DIR) / "y.npy")
    if max_samples and len(X) > max_samples:
        X = X[:max_samples]
        y = y[:max_samples]
    return X.astype(np.float32), y.astype(int)


def safe_auc(y_true: np.ndarray, scores: np.ndarray, labels: np.ndarray) -> float:
    try:
        return float(roc_auc_score(y_true, scores, labels=labels, multi_class="ovr", average="macro"))
    except Exception:
        return math.nan


def evaluate_estimator(name: str, estimator, X: np.ndarray, y: np.ndarray, folds: int) -> list[dict]:
    labels = np.unique(y)
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=config.RANDOM_SEED)
    rows: list[dict] = []

    for fold, (train_idx, test_idx) in enumerate(splitter.split(X, y), start=1):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        train_start = time.perf_counter()
        estimator.fit(X_train, y_train)
        train_seconds = time.perf_counter() - train_start

        infer_start = time.perf_counter()
        y_pred = estimator.predict(X_test)
        inference_seconds = time.perf_counter() - infer_start

        if hasattr(estimator, "predict_proba"):
            scores = estimator.predict_proba(X_test)
            roc_auc = safe_auc(y_test, scores, labels)
        else:
            roc_auc = math.nan

        rows.append(
            {
                "model": name,
                "fold": fold,
                "accuracy": accuracy_score(y_test, y_pred),
                "precision_macro": precision_score(y_test, y_pred, average="macro", zero_division=0),
                "recall_macro": recall_score(y_test, y_pred, average="macro", zero_division=0),
                "f1_macro": f1_score(y_test, y_pred, average="macro", zero_division=0),
                "roc_auc_macro_ovr": roc_auc,
                "train_seconds": train_seconds,
                "inference_seconds": inference_seconds,
            }
        )
    return rows


class VQCEstimator:
    """Small sklearn-like adapter around the project VQC factory."""

    def __init__(self):
        self.model = None

    def fit(self, X, y):
        from src.ml.qsvm import create_qsvm

        self.model = create_qsvm()
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return np.asarray(self.model.predict(X)).astype(int)


def summarize(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    metric_cols = [
        "accuracy",
        "precision_macro",
        "recall_macro",
        "f1_macro",
        "roc_auc_macro_ovr",
        "train_seconds",
        "inference_seconds",
    ]
    return df.groupby("model")[metric_cols].agg(["mean", "std"]).round(4)


def write_summary(summary: pd.DataFrame, args) -> None:
    out = RESULTS_DIR / "classifier_comparison_summary.md"
    lines = [
        "# Classifier Comparison Summary",
        "",
        f"- Samples evaluated: `{args.max_samples}`",
        f"- CV folds: `{args.folds}`",
        f"- QSVM skipped: `{args.skip_qsvm}`",
        "",
        "## Metrics",
        "",
        "```text",
        summary.to_string(),
        "```",
        "",
        "## QSVM Justification",
        "",
        "The QSVM/VQC uses `ZZFeatureMap`, whose pairwise ZZ terms encode interactions between URL metadata and QBER telemetry. In this project, those interactions include URL entropy with QBER mean, URL length with QBER burst crossings, and QBER variance with application-layer risk labels.",
        "",
        "A classical Random Forest or RBF SVM may outperform QSVM on the current small dataset. That should be reported honestly: at 200 samples and five features, quantum advantage is not expected. The contribution is a backend-agnostic architecture where classical models are practical baselines today and quantum kernels can be swapped in as feature dimensionality and hardware scale improve.",
        "",
        "The synthetic QBER generator now includes benign high-noise edge cases and stealthy low-QBER attacks, so strong results are less likely to come from a trivial QBER-only rule.",
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-samples", type=int, default=config.MAX_TRAIN_SAMPLES)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--skip-qsvm", action="store_true", help="Skip slow VQC folds while keeping the QSVM justification in the report.")
    args = parser.parse_args()

    X, y = load_data(args.max_samples)
    rows: list[dict] = []

    estimators = [
        ("Classical SVM (RBF)", SVC(kernel="rbf", probability=True, random_state=config.RANDOM_SEED)),
        ("Random Forest", RandomForestClassifier(n_estimators=100, random_state=config.RANDOM_SEED)),
    ]
    if not args.skip_qsvm:
        estimators.append(("QSVM/VQC", VQCEstimator()))

    for name, estimator in estimators:
        print(f"Evaluating {name}...")
        rows.extend(evaluate_estimator(name, estimator, X, y, args.folds))

    detail_df = pd.DataFrame(rows)
    detail_df.to_csv(RESULTS_DIR / "classifier_comparison.csv", index=False)
    summary = summarize(rows)
    write_summary(summary, args)
    print(summary)
    print(f"\nWrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
