"""
Monte Carlo comparison of trust-model variants.

This is an evaluation surrogate over the processed feature dataset and
stochastic channel/tamper models. It is intentionally faster and more
repeatable than launching the full socket simulation 600 times.

Run:
    python evaluation/compare_trust_models.py
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.infrastructure import config  # noqa: E402

RESULTS_DIR = ROOT / "evaluation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class TrustVariant:
    name: str
    use_ml: bool
    use_qber: bool
    use_g2: bool
    adaptive: bool
    description: str


VARIANTS = [
    TrustVariant("Full System", True, True, True, True, "QSVM slot + G2 + adaptive enforcer"),
    TrustVariant("Static Trust", False, False, False, False, "Always ALLOW after TLS"),
    TrustVariant("No QBER Telemetry", True, False, True, True, "URL features only; G2 retained"),
    TrustVariant("Classical-Only", True, False, False, False, "Classical ML/static trust without G2"),
]


def load_processed() -> tuple[np.ndarray, np.ndarray]:
    X = np.load(Path(config.PROCESSED_DATA_DIR) / "X.npy").astype(np.float32)
    y = np.load(Path(config.PROCESSED_DATA_DIR) / "y.npy").astype(int)
    return X, y


def train_risk_model(X: np.ndarray, y: np.ndarray):
    model = SVC(kernel="rbf", probability=False, random_state=config.RANDOM_SEED)
    model.fit(X, y)
    return model


def scenario_feature(base: np.ndarray, scenario: str, use_qber: bool, rng: np.random.Generator) -> np.ndarray:
    x = base.copy()
    if not use_qber:
        x[2:] = 0.0
        return x

    if scenario == "clean":
        q_mean = max(0.0, rng.normal(0.02, 0.01))
        q_var = max(0.0, rng.normal(0.0002, 0.0001))
        crossings = rng.choice([0, 0, 0, 1])
    elif scenario == "eve":
        q_mean = max(0.0, rng.normal(0.25, 0.04))
        q_var = max(0.0, rng.normal(0.006, 0.002))
        crossings = rng.integers(8, 20)
    else:  # environmental noise
        q_mean = max(0.0, rng.normal(0.08, 0.03))
        q_var = max(0.0, rng.normal(0.003, 0.001))
        crossings = rng.integers(0, 6)

    x[2] = min(1.0, q_mean / 0.30)
    x[3] = min(1.0, q_var / 0.02)
    x[4] = min(1.0, crossings / 20.0)
    return x


def g2_signal(scenario: str, use_g2: bool, rng: np.random.Generator, k_ancilla: int) -> int:
    if not use_g2:
        return 0
    if scenario == "eve":
        detect_p = 1.0 - (0.5 ** k_ancilla)
        return int(rng.random() < detect_p)
    if scenario == "noise":
        return int(rng.random() < 0.05)
    return 0


def decide(variant: TrustVariant, risk_score: int, tamper_signal: int) -> bool:
    if not variant.adaptive:
        return True
    if tamper_signal:
        return False
    if variant.use_ml and risk_score >= 2:
        return False
    return True


def run_trials(trials: int, k_ancilla: int) -> pd.DataFrame:
    rng = np.random.default_rng(config.RANDOM_SEED)
    X, y = load_processed()
    model = train_risk_model(X, y)
    benign_idx = np.where(y == 0)[0]
    malicious_idx = np.where(y != 0)[0]

    rows = []
    for variant in VARIANTS:
        for scenario in ("clean", "eve", "noise"):
            y_true = []
            y_pred = []
            for _ in range(trials):
                if scenario == "clean":
                    idx = int(rng.choice(benign_idx))
                    attack_present = False
                elif scenario == "eve":
                    idx = int(rng.choice(benign_idx))
                    attack_present = True
                else:
                    idx = int(rng.choice(benign_idx if len(benign_idx) else malicious_idx))
                    attack_present = False

                features = scenario_feature(X[idx], scenario, variant.use_qber, rng)
                risk_score = int(model.predict(features.reshape(1, -1))[0]) if variant.use_ml else 0
                tamper_signal = g2_signal(scenario, variant.use_g2, rng, k_ancilla)
                allow = decide(variant, risk_score, tamper_signal)

                y_true.append(int(attack_present))
                y_pred.append(int(not allow))

                rows.append(
                    {
                        "variant": variant.name,
                        "description": variant.description,
                        "scenario": scenario,
                        "attack_present": attack_present,
                        "risk_score": risk_score,
                        "g2_tamper_signal": tamper_signal,
                        "decision": "ALLOW" if allow else "BLOCK",
                    }
                )

            summary = {
                "variant": variant.name,
                "description": variant.description,
                "scenario": scenario,
                "accuracy": accuracy_score(y_true, y_pred),
                "precision": precision_score(y_true, y_pred, zero_division=0),
                "recall": recall_score(y_true, y_pred, zero_division=0),
                "f1": f1_score(y_true, y_pred, zero_division=0),
                "block_rate": float(np.mean(y_pred)),
                "trials": trials,
                "k_ancilla": k_ancilla,
            }
            rows.append(summary | {"record_type": "summary"})

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=50)
    parser.add_argument("--k-ancilla", type=int, default=1, help="Independent G2 ancilla qubits for detection amplification.")
    args = parser.parse_args()

    df = run_trials(args.trials, args.k_ancilla)
    if "record_type" not in df.columns:
        df["record_type"] = pd.NA

    trial_df = df[df["record_type"].isna()].copy()
    summary_df = df[df["record_type"].eq("summary")].copy()

    trial_df.to_csv(RESULTS_DIR / "trust_model_trials.csv", index=False)
    summary_df.to_csv(RESULTS_DIR / "trust_model_summary.csv", index=False)
    if summary_df.empty:
        print("No summary rows were generated.")
    else:
        print(summary_df[["variant", "scenario", "accuracy", "precision", "recall", "f1", "block_rate"]])
    print(f"\nWrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
