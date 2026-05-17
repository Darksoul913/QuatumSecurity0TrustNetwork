import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from src.infrastructure.logger import get_logger
from src.integrity.g1_sender import compute_hash_angle

logger = get_logger(__name__)

def verify_g2_state(received_ancilla: Statevector, received_ciphertext: bytes) -> int:
    """
    G2: Receiver evaluates the quantum-assisted tamper signal.

    The receiver computes angle φ from the received ciphertext, then applies
    Ry(-φ) to the ancilla. A measurement of |0⟩ is a clean signal; |1⟩ is a
    probabilistic out-of-band anomaly signal. This complements AES-GCM rather
    than replacing its authenticated integrity guarantee.

    Applies inverse rotation Ry(-φ) directly to the received ancilla Statevector.
    Measures the resulting state.
    Outcome '0' -> no tamper signal observed.
    Outcome '1' -> tamper/noise signal observed.
    """
    # 1. Compute expected rotation
    phi = compute_hash_angle(received_ciphertext)
    logger.debug(f"G2 Receiver computed expected φ = {phi:.4f} rad")
    
    # 2. Apply inverse rotation to received quantum state
    # We evolve the state by Ry(-phi) operator matrix
    # Ry(angle) = [[cos(angle/2), -sin(angle/2)], [sin(angle/2), cos(angle/2)]]
    angle = -phi
    ry_matrix = np.array([
        [np.cos(angle/2), -np.sin(angle/2)],
        [np.sin(angle/2),  np.cos(angle/2)]
    ])
    
    recovered_sv = received_ancilla.evolve(ry_matrix)
    
    # 3. Measure
    outcome, _ = recovered_sv.measure([0])
    result = int(outcome)
    
    if result == 0:
        logger.info("G2 tamper signal: clean (returned to |0⟩)")
    else:
        logger.warning("G2 tamper signal: anomaly observed (collapsed to |1⟩)")
        
    return result
