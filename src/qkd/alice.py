import numpy as np
import json
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from src.infrastructure import config
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

def generate_random_bits_and_bases(num_qubits=config.NUM_QUBITS):
    """Generate random bits (0, 1) and bases ('rect', 'diag')."""
    bits = np.random.randint(2, size=num_qubits)
    bases = np.random.choice(['rect', 'diag'], size=num_qubits)
    return bits.tolist(), bases.tolist()

def encode_qubit(bit, basis) -> Statevector:
    """Encode a bit in the specified basis into a Statevector."""
    qc = QuantumCircuit(1)
    
    if bit == 1:
        qc.x(0)
        
    if basis == 'diag':
        qc.h(0)
        
    return Statevector(qc)

def transmit_states(channel, bits, bases):
    """Encode and send qubits over the quantum channel."""
    logger.info(f"Alice transmitting {len(bits)} qubits...")
    for bit, basis in zip(bits, bases):
        sv = encode_qubit(bit, basis)
        channel.send_qubit(sv)
    logger.info("Alice finished transmitting qubits.")
    
def send_basis_to_bob(tls_conn, bases):
    """Alice sends her prepared bases to Bob over TLS for sifting."""
    msg = json.dumps({"type": "bases", "data": bases}).encode()
    tls_conn.sendall(len(msg).to_bytes(4, 'big') + msg)
    logger.info("Alice sent bases to Bob.")
