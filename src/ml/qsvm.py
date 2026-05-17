from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
from qiskit_machine_learning.algorithms import VQC
from qiskit_algorithms.optimizers import COBYLA
from src.infrastructure.logger import get_logger
from src.infrastructure import config

logger = get_logger(__name__)

# Feature vector is [length, entropy, qber_mean, qber_var, qber_crossings] -> 5 features
NUM_FEATURES = 5

def create_qsvm():
    """
    Creates an un-initialized Qiskit Variational Quantum Classifier (VQC).

    The ZZFeatureMap is intentionally used for feature interaction modeling:
    URL metadata and QBER telemetry can interact in ways that are not visible
    to either feature family alone. On this small simulation dataset, classical
    baselines may outperform the VQC; that is expected and should be reported
    honestly in evaluation.
    """
    logger.info(f"Initializing QSVM (VQC) with {NUM_FEATURES} features...")
    
    # 1. Feature Map: Embeds classical data into quantum state
    feature_map = ZZFeatureMap(feature_dimension=NUM_FEATURES, reps=2, entanglement='linear')
    
    # 2. Ansatz: Parameterized circuit to learn
    ansatz = RealAmplitudes(num_qubits=NUM_FEATURES, reps=2)
    
    # 3. Optimizer
    optimizer = COBYLA(maxiter=100) # Keep maxiter low for simulation speed
    
    # Construct VQC
    vqc = VQC(
        feature_map=feature_map,
        ansatz=ansatz,
        optimizer=optimizer,
    )
    
    return vqc
