import numpy as np
import json
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from src.infrastructure import config
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

def generate_random_bases(num_qubits=config.NUM_QUBITS):
    """Bob generates random measurement bases."""
    return np.random.choice(['rect', 'diag'], size=num_qubits).tolist()

def measure_state(statevector: Statevector, basis: str) -> int:
    """Bob measures the received statevector in the chosen basis."""
    qc = QuantumCircuit(1)
    
    # Statevector measurement simulates an ideal measurement in computational (Z) basis.
    # To measure in diagonal (X) basis, we must apply H to rotate back before measuring.
    if basis == 'diag':
        statevector = statevector.evolve(np.array([[1, 1], [1, -1]]) / np.sqrt(2))
        
    # Measure the 0th (and only) qubit
    outcome, _ = statevector.measure([0])
    
    # Statevector.measure returns outcome as a string ('0' or '1')
    return int(outcome)

def receive_states(channel, bases, noise_injector=None):
    """Bob receives qubits, applying noise, and measuring them."""
    measured_bits = []
    logger.info(f"Bob receiving and measuring {len(bases)} qubits...")
    
    for basis in bases:
        sv = channel.recv_qubit()
        if sv is None:
            logger.error("Connection closed prematurely during qubit reception.")
            break
            
        if noise_injector:
            sv = noise_injector.apply_channel_effects(sv)
            
        bit = measure_state(sv, basis)
        measured_bits.append(bit)
        
    logger.info("Bob finished receiving qubits.")
    return measured_bits
