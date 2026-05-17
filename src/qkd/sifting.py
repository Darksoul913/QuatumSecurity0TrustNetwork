from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

def sift_keys(alice_bases, bob_bases, raw_bits):
    """
    Compare Alice's and Bob's bases.
    Keep the bits where they matched.
    """
    sifted_key = []
    
    for i in range(len(alice_bases)):
        if alice_bases[i] == bob_bases[i]:
            sifted_key.append(raw_bits[i])
            
    logger.info(f"Sifting complete: {len(sifted_key)} bits retained (expected ~half).")
    return sifted_key

def compute_qber(alice_sifted, bob_sifted):
    """Compare sifted keys to calculate the Quantum Bit Error Rate."""
    if len(alice_sifted) != len(bob_sifted):
        raise ValueError("Sifted keys must be the same length to compute QBER.")
        
    errors = sum(1 for a, b in zip(alice_sifted, bob_sifted) if a != b)
    qber = errors / len(alice_sifted) if alice_sifted else 0.0
    
    logger.info(f"QBER Computed: {qber:.4%} ({errors} errors out of {len(alice_sifted)} bits)")
    return qber
