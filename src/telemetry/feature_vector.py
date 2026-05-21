import warnings
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

# Deprecated: use src.ml.feature_vector instead
warnings.warn(
    "src.telemetry.feature_vector is deprecated. Use src.ml.feature_vector instead.",
    DeprecationWarning,
    stacklevel=2
)

def build_telemetry_vector(qber_mean, qber_variance, threshold_crossings):
    """
    Deprecated: use src.ml.feature_vector instead.
    Constructs the 3-dimensional QBER feature vector.
    """
    logger.warning("build_telemetry_vector is deprecated. Consider using src.ml.feature_vector instead.")
    vector = [qber_mean, qber_variance, threshold_crossings]
    logger.info(f"Final Telemetry Vector generated (deprecated): {vector}")
    return vector
