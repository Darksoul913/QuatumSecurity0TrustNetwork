"""
Generates the processed dataset for the Quantum ML Risk Engine.
Reads the Malicious URL CSV, extracts URL features, attaches synthetic QBER 
telemetry, and saves to .npy files.

Run standalone: python data/generate_dataset.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np
from src.infrastructure import config
from src.infrastructure.logger import get_logger
from src.ml.feature_engineering import extract_url_features

# Apply deterministic seed
config.apply_seed()

logger = get_logger(__name__)

RAW_DATA_PATH = os.path.join(config.DATA_DIR, "raw", "dataset.csv")

def synthetic_qber_for_label(label: int):
    """
    Generate synthetic QBER telemetry with realistic class overlap.

    The simulation intentionally avoids perfectly separable telemetry. Some
    benign sessions experience environmental drift, while some attacks have a
    low physical footprint. This forces the classifier to use both URL features
    and QBER telemetry instead of learning a trivial "high QBER means attack"
    rule.

    Labels: 0 (benign), 1 (defacement), 2 (phishing), 3 (malware)
    """
    if label == 0:  # Benign
        if np.random.rand() < 0.15:
            # Noisy but non-adversarial channel conditions.
            mean = max(0.0, np.random.normal(0.08, 0.03))
            var = max(0.0, np.random.normal(0.003, 0.001))
            crossings = np.random.randint(0, 5)
        else:
            mean = max(0.0, np.random.normal(0.02, 0.01))
            var = max(0.0, np.random.normal(0.0002, 0.0001))
            crossings = np.random.choice([0, 0, 0, 1])
    else:  # Attack
        if np.random.rand() < 0.10:
            # Stealthy or partial attacks with weak physical-layer evidence.
            mean = max(0.0, np.random.normal(0.06, 0.02))
            var = max(0.0, np.random.normal(0.001, 0.0005))
            crossings = np.random.randint(0, 3)
        else:
            mean = max(0.0, np.random.normal(0.12, 0.05))
            var = max(0.0, np.random.normal(0.005, 0.003))
            crossings = np.random.randint(2, 15)
        
    return mean, var, crossings

def generate():
    if not os.path.exists(RAW_DATA_PATH):
        logger.error(f"Cannot find raw dataset at {RAW_DATA_PATH}")
        logger.info("Please ensure the URL dataset is available at data/raw/dataset.csv")
        return
        
    logger.info("Loading raw URL dataset...")
    # Load just a subset for simulation speed, stratify by label if possible, but taking head is faster
    # To get a good mix of 0,1,2,3 we shuffle a chunk
    # The dataset has 650k rows. We'll read the first 10,000, shuffle, and take what we need.
    df = pd.read_csv(RAW_DATA_PATH, nrows=10000)
    df = df.sample(frac=1, random_state=config.RANDOM_SEED).reset_index(drop=True)
    
    # We only need MAX_TRAIN_SAMPLES + some testing set
    # Let's generate 1000 samples total
    n_samples = min(1000, len(df))
    df = df.head(n_samples)
    
    logger.info(f"Extracting features for {n_samples} URLs...")
    
    X_list = []
    y_list = []
    
    for _, row in df.iterrows():
        url = str(row['url'])
        label = int(row['label'])  # 0 to 3
        
        # App features
        length, entropy = extract_url_features(url)
        
        # Channel features
        qmean, qvar, qcross = synthetic_qber_for_label(label)
        
        # 5-dimensional feature vector
        features = [length, entropy, qmean, qvar, qcross]
        
        X_list.append(features)
        y_list.append(label)
        
    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    
    # Normalize X (MinMax scaling) to fit into [0, 1] range for Qiskit feature map
    # We do simple min-max scaling across each column
    for col in range(X.shape[1]):
        col_min = X[:, col].min()
        col_max = X[:, col].max()
        if col_max > col_min:
            X[:, col] = (X[:, col] - col_min) / (col_max - col_min)
        else:
            X[:, col] = 0.0

    logger.info("Features normalized. Saving to data/processed/ ...")
    np.save(os.path.join(config.PROCESSED_DATA_DIR, "X.npy"), X)
    np.save(os.path.join(config.PROCESSED_DATA_DIR, "y.npy"), y)
    logger.info(f"Generated {len(X)} processed samples successfully.")

if __name__ == "__main__":
    generate()
