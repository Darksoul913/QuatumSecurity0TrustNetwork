"""
Ablation study for the hybrid quantum-classical architecture.

The runner evaluates component removals through a reproducible Monte Carlo
surrogate. It reports TPR, FPR, key agreement rate, decryption success, and
latency proxy metrics for each ablation ID.

Run:
    python evaluation/ablation.py
"""
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.infrastructure import config  # noqa: E402
from src.ml.feature_vector import normalize_features, scaler  # noqa: E402

RESULTS_DIR = ROOT / "evaluation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Ablation:
    ablation_id: str
    removed_component: str
    use_qkd: bool = True
    use_qber: bool = True
    use_ml: bool = True
    use_g2: bool = True
    use_adaptive: bool = True


ABLATIONS = [
    Ablation("A0", "Nothing (baseline)"),
    Ablation("A1", "QBER features", use_qber=False),
    Ablation("A2", "ML engine", use_ml=False),
    Ablation("A3", "G2 tamper signaling", use_g2=False),
    Ablation("A4", "Adaptive enforcement", use_adaptive=False),
    Ablation("A5", "QKD", use_qkd=False),
    Ablation("A6", "All quantum layers", use_qkd=False, use_qber=False, use_g2=False),
]


def load_model():
    X = np.load(Path(config.PROCESSED_DATA_DIR) / "X.npy").astype(np.float32)
    y = np.load(Path(config.PROCESSED_DATA_DIR) / "y.npy").astype(int)
    # Ensure CentralScaler parameters are loaded
    scaler.load()
    
    # Train classical RBF SVM surrogate
    model = SVC(kernel="rbf", random_state=config.RANDOM_SEED)
    model.fit(X, y)
    return X, y, model


def qber_features(scenario: str, rng: np.random.Generator) -> tuple[float, float, float]:
    if scenario == "attack":
        mean = max(0.0, rng.normal(0.18, 0.06))
        var = max(0.0, rng.normal(0.006, 0.003))
        crossings = rng.integers(5, 20)
    else:
        if rng.random() < 0.15:
            mean = max(0.0, rng.normal(0.08, 0.03))
            var = max(0.0, rng.normal(0.003, 0.001))
            crossings = rng.integers(0, 5)
        else:
            mean = max(0.0, rng.normal(0.02, 0.01))
            var = max(0.0, rng.normal(0.0002, 0.0001))
            crossings = rng.choice([0, 0, 0, 1])
    return mean, var, crossings


def tamper_signal(scenario: str, use_g2: bool, rng: np.random.Generator, k_ancilla: int) -> int:
    if not use_g2:
        return 0
    if scenario == "attack":
        return int(rng.random() < (1.0 - 0.5**k_ancilla))
    return int(rng.random() < 0.03)


def policy_decision(risk_score: int, tamper_signal: int, ablation: Ablation) -> bool:
    if not ablation.use_adaptive:
        return True
    if tamper_signal:
        return False
    if ablation.use_ml and risk_score >= 2:
        return False
    return True


def run(trials: int, k_ancilla: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(config.RANDOM_SEED)
    X, y, model = load_model()
    benign_idx = np.where(y == 0)[0]
    malicious_idx = np.where(y != 0)[0]
    rows = []

    for ablation in ABLATIONS:
        for _ in range(trials):
            scenario = "attack" if rng.random() < 0.5 else "clean"
            idx_pool = malicious_idx if scenario == "attack" and len(malicious_idx) else benign_idx
            idx = int(rng.choice(idx_pool))
            
            # Reconstruct raw features using CentralScaler
            raw_features = X[idx].copy() * scaler.scale + scaler.mean
            
            if not ablation.use_qber:
                raw_features[2:] = 0.0
            else:
                q_mean, q_var, q_cross = qber_features(scenario, rng)
                raw_features[2] = q_mean
                raw_features[3] = q_var
                raw_features[4] = q_cross
                
            # Re-normalize centrally
            features_scaled = normalize_features(raw_features)

            start = time.perf_counter()
            risk_score = int(model.predict(features_scaled.reshape(1, -1))[0]) if ablation.use_ml else 0
            t_signal = tamper_signal(scenario, ablation.use_g2, rng, k_ancilla)
            tamper_anomaly = bool(t_signal != 0)
            allow = policy_decision(risk_score, t_signal, ablation)
            latency_ms = (time.perf_counter() - start) * 1000.0

            attack_present = scenario == "attack"
            key_agreement = ablation.use_qkd and (not attack_present or rng.random() > 0.25)
            decryption_success = allow and (key_agreement or not ablation.use_qkd)

            rows.append(
                {
                    "ablation_id": ablation.ablation_id,
                    "removed_component": ablation.removed_component,
                    "scenario": scenario,
                    "attack_present": attack_present,
                    "blocked": not allow,
                    "risk_score": risk_score,
                    "tamper_signal": t_signal,
                    "tamper_anomaly": tamper_anomaly,
                    "key_agreement": key_agreement,
                    "decryption_success": decryption_success,
                    "latency_ms": latency_ms,
                    "use_qkd": ablation.use_qkd,
                    "use_qber": ablation.use_qber,
                    "use_ml": ablation.use_ml,
                    "use_g2": ablation.use_g2,
                    "use_adaptive": ablation.use_adaptive,
                }
            )

    detail = pd.DataFrame(rows)
    summary_rows = []
    for (ablation_id, removed), group in detail.groupby(["ablation_id", "removed_component"]):
        attacks = group[group["attack_present"]]
        clean = group[~group["attack_present"]]
        summary_rows.append(
            {
                "ablation_id": ablation_id,
                "removed_component": removed,
                "tpr": float(attacks["blocked"].mean()) if len(attacks) else 0.0,
                "fpr": float(clean["blocked"].mean()) if len(clean) else 0.0,
                "key_agreement_rate": float(group["key_agreement"].mean()),
                "decryption_success_rate": float(group["decryption_success"].mean()),
                "latency_ms_mean": float(group["latency_ms"].mean()),
                "trials": len(group),
                "k_ancilla": k_ancilla,
            }
        )
    return detail, pd.DataFrame(summary_rows).sort_values("ablation_id")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--k-ancilla", type=int, default=1)
    args = parser.parse_args()

    detail, summary = run(args.trials, args.k_ancilla)
    detail.to_csv(RESULTS_DIR / "ablation_trials.csv", index=False)
    summary.to_csv(RESULTS_DIR / "ablation_summary.csv", index=False)
    print(summary)
    print(f"\nWrote results to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
