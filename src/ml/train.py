"""
Standalone ML Training Pipeline.
Loads processed data, trains the QSVM, and saves the weights.
"""
import numpy as np
from src.infrastructure import config
from src.infrastructure.logger import get_logger
from src.ml.dataset import load_processed_data
from src.ml.qsvm import create_qsvm

logger = get_logger(__name__)

def train_model():
    """Orchestrates model training and saves weights."""
    config.apply_seed()
    
    logger.info("Starting Phase 6 ML Training Pipeline...")
    X, y = load_processed_data()
    
    vqc = create_qsvm()
    
    logger.info("Training VQC on CPU (This may take several minutes)...")
    vqc.fit(X, y)
    
    # Qiskit VQC doesn't have a simple '.save()' method in this version combo perfectly sometimes,
    # but we can save the optimized weights of the ansatz directly.
    weights = vqc.weights
    
    np.save(config.WEIGHTS_FILE, weights)
    logger.info(f"Training complete. Weights saved to {config.WEIGHTS_FILE}")
    
    score = vqc.score(X, y)
    logger.info(f"Train Accuracy: {score:.2f}")

if __name__ == "__main__":
    train_model()
