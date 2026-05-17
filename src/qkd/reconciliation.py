from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

def simple_reconciliation(alice_sifted, bob_sifted, block_size=10):
    """
    A simplified 1-pass Cascade-like protocol for Information Reconciliation.
    Usually both sides exchange parities over public auth channel.
    Here we simulate it directly by correcting Bob's key to match Alice's
    if a block parity mismatch is detected.
    In real life: Bob sends parity, Alice replies with parity.
    If mismatch, they do binary search to find the error and flip it.
    """
    logger.info(f"Starting reconciliation with block size {block_size}...")
    reconciled_bob = list(bob_sifted)
    corrections = 0
    
    for i in range(0, len(alice_sifted), block_size):
        block_a = alice_sifted[i:i+block_size]
        block_b = reconciled_bob[i:i+block_size]
        
        parity_a = sum(block_a) % 2
        parity_b = sum(block_b) % 2
        
        if parity_a != parity_b:
            # We know an odd number of errors exist. Assume 1 error.
            # In real Cascade, we binary search. Here, for simulation, we'll
            # just oracle-correct the first difference in the block to keep it simple.
            for j in range(len(block_a)):
                if block_a[j] != block_b[j]:
                    reconciled_bob[i+j] = 1 - reconciled_bob[i+j] # flip bit
                    corrections += 1
                    break
                    
    # The keys might still not be identical if >1 error occurred in a block,
    # but for our synthetic environment at low QBER (<5%), this is sufficient.
    mismatches_left = sum(1 for a, b in zip(alice_sifted, reconciled_bob) if a != b)
    logger.info(f"Reconciliation complete. Made {corrections} corrections. Uncorrected errors: {mismatches_left}")
    
    return reconciled_bob
