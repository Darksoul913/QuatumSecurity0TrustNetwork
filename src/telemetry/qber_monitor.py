import numpy as np
import collections
from src.infrastructure import config
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

class QBERMonitor:
    """Tracks QBER over a sliding window and computes statistical features."""
    def __init__(self, window_size=config.WINDOW_SIZE):
        self.window_size = window_size
        self.qber_history = collections.deque(maxlen=window_size)
        
    def add_qber_sample(self, qber_value: float):
        """Add a single QBER reading (e.g. from one block reconciliation)."""
        self.qber_history.append(qber_value)
        
    def get_statistics(self):
        """Compute mean, variance, and threshold crossings from the window."""
        if not self.qber_history:
            return 0.0, 0.0, 0
            
        mean = np.mean(self.qber_history)
        variance = np.var(self.qber_history)
        
        # Count how many times QBER exceeded the burst threshold
        threshold_crossings = sum(1 for x in self.qber_history if x > config.QBER_BURST_THRESHOLD)
        
        logger.debug(f"Telemetry Extracted - Mean: {mean:.4f}, Var: {variance:.4f}, Crossings: {threshold_crossings}")
        return float(mean), float(variance), int(threshold_crossings)
