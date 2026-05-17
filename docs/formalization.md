# Formalization Notes

## G2 Tamper Signaling

G1 maps a ciphertext hash to an angle theta and prepares an ancilla qubit:

```text
|psi_G1> = Ry(theta)|0>
```

G2 recomputes phi from the received ciphertext and applies the inverse rotation:

```text
|psi_G2> = Ry(-phi)|psi_G1>
```

If the ciphertext and ancilla are consistent, theta equals phi and the expected
state returns to `|0>`. If tampering creates an angular mismatch delta, the
single-qubit anomaly probability is:

```text
Pr[detect] = sin^2(delta / 2)
```

This is a probabilistic out-of-band tamper signal, not an integrity guarantee.
AES-GCM remains the authenticated integrity mechanism for the ciphertext.

## Multi-Qubit Scaling Path

For `k` independent ancilla qubits with the same mismatch model:

```text
Pr[detect] = 1 - cos^(2k)(delta / 2)
```

At the common worst-case intuition point where a single qubit detects with
probability about `0.5`, independent repetition amplifies detection:

| k | Detection Probability |
| :--- | :--- |
| 1 | ~50% |
| 5 | ~97% |
| 10 | ~99.9% |

The current implementation uses `k = 1` as a proof of concept. Hardware scaling
to `k = 10` is the future path for cryptographic-grade tamper signaling.

## QSVM Feature-Space Rationale

The `ZZFeatureMap` embeds the five-dimensional feature vector:

```text
[url_length, url_entropy, qber_mean, qber_variance, qber_crossings]
```

Its pairwise ZZ terms implicitly encode feature interactions such as
URL-entropy times QBER drift or URL length times burst crossings. A classical
SVM can approximate these interactions through kernels, and a Random Forest may
perform better on this small synthetic dataset. That result would not invalidate
the architecture; it would show that the ML component should remain
backend-agnostic until larger feature spaces or stronger quantum hardware make
quantum kernels operationally useful.

## Why Not Classical Only?

Quantum telemetry adds value specifically when:

1. Physical-layer observability is needed. Classical IDS operates at L3-L7,
   while QBER telemetry observes photon-layer disturbance. No software-only
   system can directly observe whether a photon was intercepted mid-flight.
2. The adversary model includes quantum-capable attackers. Against a
   classical-only adversary, classical crypto may suffice. Against
   quantum-capable attackers, BB84-style key exchange targets
   information-theoretic security under ideal assumptions.
3. Defense in depth requires domain separation. A failure in the classical
   stack, such as certificate compromise or a TLS implementation bug, does not
   automatically compromise the quantum telemetry layer.

Quantum telemetry does not add value when:

- The physical channel is already trusted and monitored.
- Deployment cost exceeds the threat model's expected loss.
- The adversary is purely application-layer, such as phishing or SQL injection.

Operational costs are significant: QKD hardware, fiber infrastructure,
detectors, calibration, and trained operators. This repository validates the
software architecture independently of those deployment costs.
