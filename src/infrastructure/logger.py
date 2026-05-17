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
