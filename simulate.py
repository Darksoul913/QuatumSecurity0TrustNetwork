import argparse
import os
import subprocess
import time
import sys
from src.infrastructure import config
from src.infrastructure.logger import get_logger

logger = get_logger("SimulateController")

def main():
    parser = argparse.ArgumentParser(description="Quantum-Secure Zero-Trust Simulation Controller")
    parser.add_argument("--eve", action="store_true", help="Enable adversarial eavesdropping (Intercept & Resend)")
    parser.add_argument("--noise", type=float, default=0.0, help="Environmental noise probability (e.g. 0.05)")
    parser.add_argument("--payload", type=str, default="Top_Secret_Launch_Codes", help="Payload to transmit")
    args = parser.parse_args()
    
    logger.info("=====================================================")
    logger.info(" QUANTUM-SECURE ZERO-TRUST NETWORK SIMULATION STARTED")
    logger.info("=====================================================\n")
    
    if args.eve:
        logger.warning(">>> ADVERSARIAL EVE IS ACTIVE <<<")
    if args.noise > 0:
        logger.info(f">>> CHANNEL NOISE ENABLED (p={args.noise}) <<<")
        
    logger.info(f"Payload to send: {args.payload}\n")
    
    child_env = os.environ.copy()
    child_env["QZTN_EVE_ACTIVE"] = "1" if args.eve else "0"
    child_env["QZTN_ENV_NOISE_P"] = str(args.noise)
    
    try:
        # 1. Start Bob (Receiver)
        logger.info("[CONTROLLER] Starting Bob Node in background...")
        # We redirect stderr to stdout to interleave logs beautifully
        bob_proc = subprocess.Popen([sys.executable, "bob_node.py"], 
                                   stdout=sys.stdout,
                                   stderr=sys.stderr,
                                   env=child_env)
                                   
        # Give Bob time to spin up sockets (TLS + Quantum)
        time.sleep(2)
        
        # 2. Start Alice (Transmitter)
        logger.info("[CONTROLLER] Starting Alice Node...")
        alice_proc = subprocess.Popen([sys.executable, "alice_node.py", "--payload", args.payload],
                                     stdout=sys.stdout, 
                                     stderr=sys.stderr,
                                     env=child_env)
                                     
        # Wait for processes to exit
        alice_proc.wait()
        bob_proc.wait()
        
    finally:
        pass
            
    logger.info("\n=====================================================")
    logger.info(" SIMULATION COMPLETE")
    logger.info("=====================================================")

if __name__ == "__main__":
    main()
