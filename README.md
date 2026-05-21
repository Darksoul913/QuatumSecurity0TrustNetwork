# Quantum-Secure Zero-Trust Network Simulation

This repository implements a 9-phase hybrid quantum-classical security architecture. It demonstrates:
1. Quantum Key Distribution (BB84)
2. Cross-layer security telemetry fusion (QBER feature engineering)
3. Quantum-aware zero-trust policy enforcement (QSVM + G2 probabilistic tamper signaling)

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate Certificates**
   Phase 2 (Mutual TLS Authentication) requires certificates.
   ```bash
   bash scripts/gen_certs.sh
   ```

3. **Data Generation & Training**
   The ML Risk Engine requires processed URL/QBER features and a trained QSVM.
   ```bash
   python data/generate_dataset.py
   python -m src.ml.train
   ```

4. **Evaluation**
   ```bash
   python evaluation/compare_classifiers.py --skip-qsvm
   python evaluation/compare_trust_models.py
   python evaluation/run_ablation.py
   python evaluation/plot_results.py
   ```

## Research Framing

G2 is a quantum-assisted probabilistic tamper signal, not an integrity
guarantee. AES-GCM provides classical authenticated integrity; G2 adds an
independent physics-layer tripwire. See `docs/formalization.md` and
`docs/threat_model.md` for the assumptions, limitations, and "why not
classical-only?" argument.

## Running the Simulation

Use the simulation controller to test different scenarios:

**1. Clean Channel (Expected: ALLOW)**
```bash
python simulate.py --payload "Attack at dawn"
```

**2. Adversarial Interception (Expected: BLOCK)**
```bash
python simulate.py --eve --payload "Attack at dawn"
```

**3. Environmental Noise (Expected: ALLOW or BLOCK depending on severity)**
```bash
python simulate.py --noise 0.05
```

**4. Live Streaming SOC Dashboard (Randomized)**
Simulates a continuous stream of traffic from the dataset, dynamically rolling random channel states (Clean, Noisy, Eavesdropped) per request, and displaying a real-time Security Operations Center (SOC) dashboard:
```bash
python stream_simulation.py --max-requests 20 --delay 1.2
```
* `--max-requests`: The number of requests to stream (default: `20`).
* `--delay`: Time delay in seconds between requests (default: `1.2`).
