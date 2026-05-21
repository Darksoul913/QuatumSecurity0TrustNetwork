import argparse
import sys
import time
import os
import random
import pandas as pd
import numpy as np
import logging

# Disable imported logger noise to keep the terminal dashboard clean
logging.disable(logging.INFO)

from src.infrastructure import config
from src.ml.feature_engineering import extract_url_features
from src.ml.feature_vector import build_feature_vector, normalize_features
from src.ml import model_loader
from src.policy.enforcer import ZeroTrustEnforcer

# Set up ANSI escape sequences for text colors and formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def format_col(text, width, color=None, bold=False):
    """Pads a string first, then wraps it in ANSI escape colors to maintain alignment."""
    padded = f"{text:<{width}}"
    if color:
        res = color + padded + RESET
        if bold:
            res = BOLD + res
        return res
    return padded

def main():
    parser = argparse.ArgumentParser(description="Live Streaming Traffic Simulator with Quantum ZTNA")
    parser.add_argument("--max-requests", type=int, default=20, help="Number of requests to simulate")
    parser.add_argument("--delay", type=float, default=1.2, help="Delay in seconds between requests")
    args = parser.parse_args()

    # Apply deterministic seed for base initialization
    config.apply_seed()
    
    # Reset seeds to None (system entropy) so that each simulation run is completely randomized
    random.seed(None)
    np.random.seed(None)

    print(f"\n{BOLD}{CYAN}========================================================================================{RESET}")
    print(f"{BOLD}{CYAN}          QUANTUM-SECURE ZERO-TRUST NETWORK STREAMING SIMULATOR (SOC DASHBOARD)          {RESET}")
    print(f"{BOLD}{CYAN}========================================================================================{RESET}")
    print("Initializing components...")

    # Load URL database
    csv_path = os.path.join("data", "raw", "dataset.csv")
    if not os.path.exists(csv_path):
        print(f"{RED}Error: Raw dataset not found at {csv_path}. Please make sure raw data is generated.{RESET}")
        sys.exit(1)

    print("Loading URLs from dataset...")
    try:
        # Load a larger chunk and sample from it randomly
        df = pd.read_csv(csv_path, nrows=50000)
        df_samples = df.sample(n=args.max_requests).reset_index(drop=True)
    except Exception as e:
        print(f"{RED}Failed to load dataset: {e}{RESET}")
        sys.exit(1)

    # Load model
    classifier = model_loader.load_model()
    policy_enforcer = ZeroTrustEnforcer()

    # Map labels to threat names
    threat_names = {
        0: "Benign",
        1: "Defacement",
        2: "Phishing",
        3: "Malware"
    }

    print(f"Loaded {len(df_samples)} URL samples. Starting live stream...\n")
    time.sleep(1)

    # Table Header Design
    col_widths = {
        "no": 3,
        "url": 25,
        "type": 12,
        "channel": 18,
        "qber": 9,
        "risk": 8,
        "g2": 12,
        "decision": 8
    }

    # Print Table Header
    no_hdr = format_col("No.", col_widths["no"], BOLD + CYAN)
    url_hdr = format_col("Requested URL", col_widths["url"], BOLD + CYAN)
    type_hdr = format_col("Traffic Type", col_widths["type"], BOLD + CYAN)
    chan_hdr = format_col("Channel State", col_widths["channel"], BOLD + CYAN)
    qber_hdr = format_col("QBER Mean", col_widths["qber"], BOLD + CYAN)
    risk_hdr = format_col("Risk Lvl", col_widths["risk"], BOLD + CYAN)
    g2_hdr = format_col("G2 Qubit", col_widths["g2"], BOLD + CYAN)
    dec_hdr = format_col("Decision", col_widths["decision"], BOLD + CYAN)

    header = f"| {no_hdr} | {url_hdr} | {type_hdr} | {chan_hdr} | {qber_hdr} | {risk_hdr} | {g2_hdr} | {dec_hdr} |"
    divider = "+" + "+".join(["-" * (w + 2) for w in col_widths.values()]) + "+"
    
    print(divider)
    print(header)
    print(divider)

    for i, row in df_samples.iterrows():
        url = str(row['url'])
        label = int(row['label'])
        
        # Display URL (truncated to fit)
        url_disp = url
        if len(url_disp) > col_widths["url"]:
            url_disp = url_disp[:col_widths["url"]-3] + "..."
            
        # Simulate physical channel conditions dynamically
        # 70% clean, 15% noisy, 15% attack
        channel_roll = random.random()
        
        # If the traffic is an attack (label > 0), higher probability of active eavesdropping (Eve)
        if label > 0 and random.random() < 0.60:
            channel_roll = 0.90 # Force Eavesdropped state to align threat vectors

        if channel_roll < 0.70:
            # Clean channel
            channel_name = "Clean"
            channel_color = GREEN
            qber_mean = max(0.0, np.random.normal(0.018, 0.005))
            qber_var = max(0.0, np.random.normal(0.0002, 0.0001))
            qber_crossings = np.random.choice([0, 1])
            tamper_signal = 0
        elif channel_roll < 0.85:
            # Noisy channel (e.g. fiber drift)
            channel_name = "Noisy (Drift)"
            channel_color = YELLOW
            qber_mean = max(0.0, np.random.normal(0.065, 0.015))
            qber_var = max(0.0, np.random.normal(0.001, 0.0005))
            qber_crossings = np.random.randint(1, 4)
            tamper_signal = 0
        else:
            # Eavesdropped channel (Eve active)
            channel_name = "Eavesdropped"
            channel_color = RED
            qber_mean = max(0.0, np.random.normal(0.255, 0.03))
            qber_var = max(0.0, np.random.normal(0.005, 0.002))
            qber_crossings = np.random.randint(4, 12)
            tamper_signal = 1  # State collapse due to Eve measurement

        # Extract features and scale
        length, entropy = extract_url_features(url)
        features = build_feature_vector(length, entropy, qber_mean, qber_var, qber_crossings)
        X_scaled = normalize_features(features).reshape(1, -1)
        
        # Predict Risk
        prediction = np.squeeze(classifier.predict(X_scaled))
        if prediction.ndim > 0 and len(np.atleast_1d(prediction)) > 1:
            risk_score = int(np.argmax(prediction))
        else:
            risk_score = int(np.atleast_1d(prediction)[0])

        # Evaluate Zero-Trust policy decision logic
        # 1. Tamper signal is a hard BLOCK
        # 2. Risk score >= 2 (HIGH/CRITICAL) is a BLOCK
        # 3. Otherwise ALLOW
        decision = (tamper_signal == 0) and (risk_score < 2)
        
        # Format elements with appropriate color padding
        no_str = format_col(str(i+1), col_widths["no"])
        url_str = format_col(url_disp, col_widths["url"])
        
        type_color = GREEN if label == 0 else RED
        type_str = format_col(threat_names.get(label, "Unknown"), col_widths["type"], type_color)
        
        chan_str = format_col(channel_name, col_widths["channel"], channel_color, bold=(channel_name == "Eavesdropped"))
        
        qber_val_str = f"{qber_mean*100:5.2f}%"
        qber_color = RED if qber_mean >= 0.15 else (YELLOW if qber_mean >= 0.05 else GREEN)
        qber_str = format_col(qber_val_str, col_widths["qber"], qber_color)
        
        risk_levels = {0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "CRITICAL"}
        risk_color = GREEN if risk_score == 0 else (YELLOW if risk_score == 1 else RED)
        risk_str = format_col(risk_levels.get(risk_score, "UNKNOWN"), col_widths["risk"], risk_color)
        
        g2_val = "|0⟩ (Clean)" if tamper_signal == 0 else "|1⟩ (Tamper)"
        g2_color = GREEN if tamper_signal == 0 else RED
        g2_str = format_col(g2_val, col_widths["g2"], g2_color)
        
        dec_val = "ALLOW" if decision else "BLOCK"
        dec_color = GREEN if decision else RED
        dec_str = format_col(dec_val, col_widths["decision"], dec_color, bold=True)
        
        # Print table row
        print(f"| {no_str} | {url_str} | {type_str} | {chan_str} | {qber_str} | {risk_str} | {g2_str} | {dec_str} |")
        
        time.sleep(args.delay)

    print(divider)
    print(f"\n{BOLD}{GREEN}Live Stream Simulation Complete!{RESET}")
    print(f"Total requests processed: {args.max_requests}")
    print(f"Zero-Trust Dashboard shutting down successfully.\n")

if __name__ == "__main__":
    main()
