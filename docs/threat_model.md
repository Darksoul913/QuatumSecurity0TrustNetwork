# Threat Model

## System Boundary

The simulation models a hybrid quantum-classical zero-trust channel between
Alice and Bob. It combines mutual TLS, BB84-style QKD, QBER telemetry,
URL-feature risk scoring, AES-GCM payload protection, and G2 probabilistic
tamper signaling.

The implementation is a research simulation. It validates architecture and
control flow, not deployable quantum-hardware security.

## Adversary Classes

| Adversary | Capabilities | Covered? | Notes |
| :--- | :--- | :--- | :--- |
| Passive Eve | Observes classical traffic only | Partial | TLS and AES-GCM protect payload confidentiality. |
| Active Eve | Intercept-resend on quantum channel | Yes | BB84 disturbance increases QBER. |
| Quantum-capable Eve | Can run quantum attacks against classical crypto | Partial | BB84-derived keys remain information-theoretic under ideal assumptions; TLS certificates remain classical. |
| Application attacker | Sends malicious URLs or risky payload contexts | Yes | URL features feed the ML risk engine. |
| Insider or compromised Bob enclave | Can alter telemetry, model, or policy code | No | Outside current simulation scope. |

## Attack Taxonomy

| ID | Attack | Layer | Covered? | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| ATK-1 | Intercept-resend | Quantum | Yes | Raises QBER in the sifted key. |
| ATK-2 | Photon-number splitting | Quantum | Partial | Decoy states are not implemented. |
| ATK-3 | Classical MITM | TLS | Yes | Mutual TLS rejects unauthenticated peers. |
| ATK-4 | Malicious URL | Application | Yes | URL metadata contributes to risk classification. |
| ATK-5 | Ciphertext tampering | Payload | Yes | AES-GCM authenticates ciphertext; G2 adds an independent tamper signal. |
| ATK-6 | Model poisoning | Training | No | Training data provenance is not protected. |
| ATK-7 | Telemetry spoofing | Sensor/pipeline | No | See trusted telemetry assumption. |
| ATK-8 | Replay attack | Full path | Partial | Fresh keys and nonces help; full protocol transcript replay protection is not modeled. |

## Trusted Telemetry Assumption

This architecture assumes:

1. QBER measurements are performed by trusted hardware within Bob's enclave.
2. The telemetry pipeline from `QBERMonitor` to feature vector to classifier is untampered.
3. ML model weights loaded at runtime are the genuine trained weights.

The current implementation explicitly does not defend against:

- Telemetry spoofing, where an adversary injects false QBER readings.
- Sensor manipulation, where quantum detector hardware is compromised.
- Replayed telemetry, where old QBER readings are substituted for current ones.
- Policy poisoning, where the enforcer's decision logic is modified.

These are open problems in quantum-network security. A production design would
need trusted execution environments, model signing, hardware attestation, and
auditable telemetry provenance. Those controls are outside the scope of this
simulation.
