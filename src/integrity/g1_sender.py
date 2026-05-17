import hashlib
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

def compute_hash_angle(data: bytes) -> float:
    """Compute SHA256 of data, map it to a rotation angle θ in [0, 2π]."""
    hasher = hashlib.sha256()
    hasher.update(data)
    digest = hasher.digest()
    
    # Convert first 8 bytes of hash into an integer, then map to an angle
    val = int.from_bytes(digest[:8], 'big')
    # modulo some large number, normalize to [0, 1] then multiply by 2pi
    theta = (val % 10000) / 10000.0 * 2 * np.pi
    return theta

def compute_g1_state(ciphertext: bytes) -> Statevector:
    """
    G1: Sender prepares a quantum-assisted probabilistic tamper signal.

    The ciphertext hash is mapped to angle θ and encoded as Ry(θ)|0⟩ on an
    ancilla qubit. This is not an integrity guarantee; AES-GCM provides the
    authenticated classical integrity check. G1/G2 adds an independent,
    physics-layer tripwire that is outside the attacker's classical
    computational domain.
    """
    theta = compute_hash_angle(ciphertext)
    logger.debug(f"G1 Sender computed θ = {theta:.4f} rad")
    
    qc = QuantumCircuit(1)
    qc.ry(theta, 0)
    
    sv = Statevector(qc)
    logger.info("G1 tamper-signaling ancilla Statevector prepared.")
    
    return sv
