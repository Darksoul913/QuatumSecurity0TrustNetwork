import os
import random
import numpy as np

# Ensure deterministic execution
RANDOM_SEED = 42

def apply_seed():
    """Apply the deterministic seed globally."""
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)


# Networking & Ports
HOST = "localhost"
CHANNEL_PORT = 8000
TLS_PORT = 8001

# QKD Parameters
NUM_QUBITS = 1000  # Number of qubits to transmit for key exchange
QBER_THRESHOLD = 0.05  # 5% acceptable error rate
WINDOW_SIZE = 100  # Window size for QBER statistical extraction (reduced for sim speed)
QBER_BURST_THRESHOLD = 0.08  # Threshold for considering a QBER spike

# Paths
BASE_DIR = "/Users/Siddhesh/My-Files/VIT/SY/Sem2/EDI/Implementation"
CERTS_DIR = os.path.join(BASE_DIR, "certs")
CA_CERT = os.path.join(CERTS_DIR, "ca_cert.pem")
ALICE_CERT = os.path.join(CERTS_DIR, "alice_cert.pem")
ALICE_KEY = os.path.join(CERTS_DIR, "alice_key.pem")
BOB_CERT = os.path.join(CERTS_DIR, "bob_cert.pem")
BOB_KEY = os.path.join(CERTS_DIR, "bob_key.pem")

# ML Paths
MODELS_DIR = os.path.join(BASE_DIR, "models")
WEIGHTS_FILE = os.path.join(MODELS_DIR, "qsvm_weights.npy")
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
MAX_TRAIN_SAMPLES = 500  # Limit for QSVM CPU tractability

# Simulation Mode Options (Can be overridden by simulate.py)
EVE_ACTIVE = os.getenv("QZTN_EVE_ACTIVE", "0") == "1"
ENV_NOISE_P = float(os.getenv("QZTN_ENV_NOISE_P", "0.0"))  # Environmental noise probability

# Configurable logging path
RUNTIME_LOG_PATH = os.path.join(BASE_DIR, "evaluation", "results", "runtime_events.jsonl")

# Ablation flags. These default to the full architecture and are intentionally
# controlled through environment variables so evaluation scripts can toggle
# components without rewriting source files.
USE_QKD = os.getenv("QZTN_USE_QKD", os.getenv("QZTN_ENABLE_QKD", "1")) == "1"
USE_QBER = os.getenv("QZTN_USE_QBER", os.getenv("QZTN_ENABLE_QBER_TELEMETRY", "1")) == "1"
USE_ML = os.getenv("QZTN_USE_ML", os.getenv("QZTN_ENABLE_ML_ENGINE", "1")) == "1"
USE_G2 = os.getenv("QZTN_USE_G2", os.getenv("QZTN_ENABLE_G2_TAMPER_SIGNAL", "1")) == "1"
USE_ADAPTIVE_POLICY = os.getenv("QZTN_USE_ADAPTIVE_POLICY", os.getenv("QZTN_ENABLE_ADAPTIVE_ENFORCEMENT", "1")) == "1"

# Backward compatibility aliases
ENABLE_QKD = USE_QKD
ENABLE_QBER_TELEMETRY = USE_QBER
ENABLE_ML_ENGINE = USE_ML
ENABLE_G2_TAMPER_SIGNAL = USE_G2
ENABLE_ADAPTIVE_ENFORCEMENT = USE_ADAPTIVE_POLICY

# Create directories if they don't exist
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
