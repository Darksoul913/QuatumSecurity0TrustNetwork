import hashlib
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

def apply_hash(reconciled_key_bits) -> bytes:
    """
    Privacy amplification via Cryptographic Hashing.
    Takes the reconciled bitstring and compresses it into a uniform 256-bit AES key.
    This destroys Eve's partial mutual information.
    """
    # Convert bit list to bytes
    # e.g., [1, 0, 1, 1] -> '1011' -> encode to bytes
    bit_string = "".join(str(b) for b in reconciled_key_bits)
    
    # Hash to produce exactly 256 bits (32 bytes)
    hasher = hashlib.sha256()
    hasher.update(bit_string.encode('utf-8'))
    final_key = hasher.digest()
    
    logger.info(f"Privacy amplification complete. Generated 256-bit AES key: {final_key.hex()[:16]}...")
    return final_key
