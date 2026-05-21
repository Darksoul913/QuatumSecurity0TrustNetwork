import numpy as np
import os
from src.infrastructure import config
from src.infrastructure.logger import get_logger
from src.ml.qsvm import create_qsvm

logger = get_logger(__name__)

class FrozenClassifier:
    """Wrapper to load weights into a VQC without retraining it."""
    def __init__(self, vqc, weights):
        self.vqc = vqc
        self.weights = weights
        # We manually patch the weights so `predict` works without calling `fit`
        self.vqc._fit_result = type('DummyFitResult', (), {'x': weights})
        
    def predict(self, X):
        """Perform inference using the frozen model."""
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
            
        # Due to how Qiskit VQC inference works, we might need a workaround if predict fails
        # A simpler way in pure Qiskit-ML if predict fails on a bypassed fit is to just run the neural network wrapper directly:
        try:
            return self.vqc.predict(X)
        except Exception as e:
            logger.debug(f"Native VQC predict failed, falling back to neural network forward pass: {e}")
            # Ensure X is 2D
            forward_pass = self.vqc.neural_network.forward(X, self.weights)
            # forward_pass returns probability distributions of shape (n_samples, n_classes)
            # Predict the class with the highest probability
            return np.argmax(forward_pass, axis=1)

class ClassicalFallbackClassifier:
    """Fallback classifier trained on-the-fly when QSVM weights are unavailable."""
    def __init__(self):
        from sklearn.svm import SVC
        from src.ml.dataset import load_processed_data
        
        logger.warning("Initializing Classical Fallback Classifier (RBF SVM)...")
        try:
            X, y = load_processed_data()
            self.model = SVC(kernel="rbf", probability=False, random_state=config.RANDOM_SEED)
            self.model.fit(X, y)
            logger.info("Classical Fallback Classifier trained successfully.")
        except Exception as e:
            logger.error(f"Failed to train Classical Fallback Classifier: {e}")
            self.model = None

    def predict(self, X):
        if self.model is not None:
            return self.model.predict(X)
        else:
            logger.error("No fallback model available. Predicting default LOW risk (0).")
            # If shape is (N, D), return (N,)
            return np.zeros(X.shape[0], dtype=np.int32)

def load_model():
    """Loads the pre-trained QSVM weights for runtime inference, with classical fallback."""
    try:
        if not os.path.exists(config.WEIGHTS_FILE):
            logger.warning(f"Model weights file not found at {config.WEIGHTS_FILE}. Falling back to classical baseline.")
            return ClassicalFallbackClassifier()
            
        logger.info(f"Loading pre-trained QSVM weights from {config.WEIGHTS_FILE}...")
        weights = np.load(config.WEIGHTS_FILE)
        
        vqc = create_qsvm()
        return FrozenClassifier(vqc, weights)
    except Exception as e:
        logger.warning(f"Failed to load QSVM model weights ({e}). Falling back to classical baseline.")
        return ClassicalFallbackClassifier()
