from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

def build_telemetry_vector(qber_mean, qber_variance, threshold_crossings):
    """
    Constructs the 3-dimensional QBER feature vector.
    This strictly defines the interface between physical channel telemetry
    and the ML Risk Engine input.
    """
    vector = [qber_mean, qber_variance, threshold_crossings]
    logger.info(f"Final Telemetry Vector generated: {vector}")
    return vector
