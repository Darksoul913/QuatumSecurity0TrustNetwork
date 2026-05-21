import os
import json
import numpy as np
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

class CentralScaler:
    def __init__(self):
        self.mean = np.zeros(5, dtype=np.float32)
        self.scale = np.ones(5, dtype=np.float32)
        self.params_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "models", "scaler_params.json"
        )
        self._loaded = False

    def fit(self, X):
        X_arr = np.array(X, dtype=np.float32)
        self.mean = np.mean(X_arr, axis=0)
        self.scale = np.std(X_arr, axis=0)
        # Avoid division by zero
        self.scale[self.scale == 0] = 1.0
        self.save()
        self._loaded = True

    def transform(self, X):
        if not self._loaded:
            self.load()
        X_arr = np.array(X, dtype=np.float32)
        return (X_arr - self.mean) / self.scale

    def save(self):
        os.makedirs(os.path.dirname(self.params_file), exist_ok=True)
        data = {
            "mean": self.mean.tolist(),
            "scale": self.scale.tolist()
        }
        with open(self.params_file, "w") as f:
            json.dump(data, f, indent=4)
        logger.info(f"CentralScaler params saved to {self.params_file}")

    def load(self):
        if os.path.exists(self.params_file):
            try:
                with open(self.params_file, "r") as f:
                    data = json.load(f)
                self.mean = np.array(data["mean"], dtype=np.float32)
                self.scale = np.array(data["scale"], dtype=np.float32)
                self._loaded = True
                logger.info(f"CentralScaler params loaded from {self.params_file}")
            except Exception as e:
                logger.warning(f"Failed to load CentralScaler params: {e}. Using defaults.")
        else:
            logger.warning(f"CentralScaler params file not found at {self.params_file}. Using default (unscaled) parameters.")

# Singleton instance
scaler = CentralScaler()

def build_feature_vector(url_length, url_entropy, qber_mean, qber_variance, qber_crossings):
    """
    Fuses application-layer (URL features) and physical-layer (QBER telemetry) features.
    Returns:
        List of 5 features representing [url_length, url_entropy, qber_mean, qber_variance, qber_crossings].
    """
    return [url_length, url_entropy, qber_mean, qber_variance, qber_crossings]

def normalize_features(features):
    """
    Applies the central standard scaling to a feature vector or array of vectors.
    """
    return scaler.transform(features)
