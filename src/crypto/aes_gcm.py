import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

def encrypt_payload(key: bytes, plaintext: bytes):
    """
    Encrypt data using AES-256-GCM.
    Produces ciphertext + authentication tag.
    """
    logger.info("Encrypting payload with BB84-derived AES key...")
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce required for GCM
    
    # encrypt() method returns ciphertext || tag appended together
    ct_and_tag = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    
    # Extract ciphertext and the last 16 bytes as the auth tag
    ciphertext = ct_and_tag[:-16]
    tag = ct_and_tag[-16:]
    
    logger.debug(f"Encryption successful. Ciphertext len: {len(ciphertext)} bytes")
    return nonce, ciphertext, tag

def decrypt_payload(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes) -> bytes:
    """
    Decrypt data using AES-256-GCM.
    Verifies authenticity/integrity automatically before decrypting.
    """
    logger.info("Decrypting received payload...")
    aesgcm = AESGCM(key)
    
    # Reconstruct ct || tag for decryption method
    ct_and_tag = ciphertext + tag
    
    try:
        plaintext = aesgcm.decrypt(nonce, ct_and_tag, associated_data=None)
        logger.info("Decryption and AES-GCM Integrity Verification Successful.")
        return plaintext
    except Exception as e:
        logger.error(f"Decryption or GCM Verification Failed! {e}")
        raise ValueError("Invalid Key, Corrupt Data, or Tampering Detected by AES-GCM.")
