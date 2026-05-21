from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

class ZeroTrustEnforcer:
    """
    G3: Zero Trust Policy Engine.
    Combines application-layer risk intelligence (QSVM output) with the G2
    physics-layer tamper signal to formulate a policy decision.

    G2 is treated as a probabilistic anomaly tripwire, not a replacement for
    AES-GCM integrity. A clean signal does not prove integrity; an anomaly is
    enough for a zero-trust block decision.
    """
    def __init__(self):
        # Maps QSVM numerical output to risk categories
        self.risk_mapping = {
            0: "LOW",
            1: "MEDIUM",
            2: "HIGH",
            3: "CRITICAL"
        }

    def evaluate(self, risk_score: int, tamper_signal: int) -> bool:
        """
        Evaluate transmission safety.
        risk_score: 0-3 from QSVM.
        tamper_signal: 0 (clean signal), 1 (tamper/noise signal) from G2.
        Returns:
            True if ALLOW
            False if BLOCK
        """
        risk_level = self.risk_mapping.get(risk_score, "UNKNOWN")
        logger.info(f"Policy Evaluation - Risk: {risk_level} ({risk_score}), G2 tamper signal: |{tamper_signal}⟩")
        
        # Fundamental Zero Trust Logic:
        # 1. Any out-of-band tamper signal -> IMMEDIATE BLOCK
        if tamper_signal != 0:
            logger.warning("[POLICY DECISION] BLOCK: G2 Tamper anomaly detected (state collapsed to |1⟩).")
            return False
            
        # 2. Unacceptable application-layer risk -> IMMEDIATE BLOCK
        if risk_score >= 2: # HIGH or CRITICAL
            logger.warning(f"[POLICY DECISION] BLOCK: Unacceptable behavioral risk level ({risk_level}).")
            return False
            
        # 3. Otherwise: ALLOW
        logger.info("[POLICY DECISION] ALLOW: Risk accepted and no G2 tamper signal observed.")
        return True

    def execute_action(self, decision: bool):
        """Perform side-effects based on decision."""
        if not decision:
            logger.error(">>> EXECUTING BLOCK ACTION: Destroying AES key, flagging sender, dropping payload. <<<")
            # In a real system, we'd trigger network switches or drop memory here
        else:
            logger.info(">>> EXECUTING ALLOW ACTION: Passing payload to destination application. <<<")
