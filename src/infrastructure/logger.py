"""
Structured logging setup for the entire simulation.
"""
import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger with standard stream formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Create console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s', datefmt='%H:%M:%S')
        ch.setFormatter(formatter)
        
        logger.addHandler(ch)
        
    return logger

def log_structured_event(session_id: str, trial_id: str, scenario: str, qber_mean: float, risk_score: int, tamper_signal: int, tamper_anomaly: bool, decision: bool):
    """
    Appends a structured JSON event to config.RUNTIME_LOG_PATH with timestamp,
    schema version, and evaluation parameters.
    """
    import json
    import time
    import os
    from src.infrastructure import config
    
    event = {
        "schema_version": "1.0",
        "timestamp": time.time(),
        "session_id": session_id,
        "trial_id": trial_id,
        "scenario": scenario,
        "qber_mean": float(qber_mean),
        "risk_score": int(risk_score),
        "tamper_signal": int(tamper_signal),
        "tamper_anomaly": bool(tamper_anomaly),
        "decision": "ALLOW" if decision else "BLOCK"
    }
    
    # Ensure results directory exists
    log_dir = os.path.dirname(config.RUNTIME_LOG_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        
    try:
        with open(config.RUNTIME_LOG_PATH, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        sys.stderr.write(f"Failed to write structured log event: {e}\n")
