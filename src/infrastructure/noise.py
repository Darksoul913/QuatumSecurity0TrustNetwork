import numpy as np
from qiskit.quantum_info import Statevector
from src.infrastructure import config
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

class NoiseInjector:
    """
    Simulates quantum channel noise and adversarial interception.
    """
    def __init__(self, is_eve_active=False, env_noise_p=0.0):
        self.is_eve_active = is_eve_active
        self.env_noise_p = env_noise_p
        
        if self.is_eve_active:
            logger.warning("EVE IS ACTIVE! Intercept-and-resend attack enabled.")
            # Critical: Isolated PRNG so Eve doesn't magically sync with Alice's PRNG sequence
            self.eve_rng = np.random.default_rng(config.RANDOM_SEED + 999)
        if self.env_noise_p > 0:
            logger.info(f"Environmental noise enabled with p={self.env_noise_p}")
            self.env_rng = np.random.default_rng(config.RANDOM_SEED + 888)

    def apply_channel_effects(self, statevector: Statevector) -> Statevector:
        """Applies noise and/or Eve's interception to the flying qubit."""
        noisy_state = statevector

        # 1. Adversarial Interception (Eve)
        # Eve measures the qubit in a random basis and resends the collapsed state
        if self.is_eve_active:
            eve_basis = self.eve_rng.choice(['rect', 'diag'])
            # We don't need a full circuit, we can just collapse the Statevector mathematically.
            # However, since Statevector.measure() behaves as an ideal Z-measurement (computational basis):
            if eve_basis == 'rect':
                outcome, noisy_state = noisy_state.measure([0])
            else: # diagonal basis
                # Apply H, measure Z, apply H back
                noisy_state = noisy_state.evolve(np.array([[1, 1], [1, -1]]) / np.sqrt(2))
                outcome, noisy_state = noisy_state.measure([0])
                noisy_state = noisy_state.evolve(np.array([[1, 1], [1, -1]]) / np.sqrt(2))

        # 2. Environmental Noise 
        # Random bit flip (X) or phase flip (Z)
        if self.env_noise_p > 0:
            if np.random.rand() < self.env_noise_p:
                noise_type = np.random.choice(['X', 'Z', 'Y'])
                if noise_type == 'X':
                    noisy_state = noisy_state.evolve(np.array([[0, 1], [1, 0]]))
                elif noise_type == 'Z':
                    noisy_state = noisy_state.evolve(np.array([[1, 0], [0, -1]]))
                elif noise_type == 'Y':
                    noisy_state = noisy_state.evolve(np.array([[0, -1j], [1j, 0]]))

        return noisy_state
