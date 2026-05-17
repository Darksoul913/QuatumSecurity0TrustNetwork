"""
Alice Node - The Transmitter.
"""
import time
import json
import pickle
import struct
import argparse
import hashlib
from src.infrastructure import config
from src.infrastructure.logger import get_logger
from src.infrastructure.channel import QuantumChannel
from src.auth.tls_client import TLSClient
from src.qkd import alice, sifting, reconciliation, privacy_amplification
from src.crypto import aes_gcm
from src.integrity import g1_sender

logger = get_logger("AliceNode") # Named logger for clarity in logs

def _recv_exact(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def run_alice(payload_text="Top Secret Quantum Data"):
    config.apply_seed()
    logger.info("Starting Alice Node...")
    
    # --- PHASE 2: Authentication ---
    tls = TLSClient()
    secure_conn = tls.connect()
    
    # --- PHASE 1: Infrastructure ---
    # Give Bob a moment to start his quantum listener
    time.sleep(1)
    q_channel = QuantumChannel(config.HOST, config.CHANNEL_PORT, is_server=False)
    q_channel.connect()
    
    # --- PHASE 3: BB84 QKD ---
    bits, bases = alice.generate_random_bits_and_bases()
    alice.transmit_states(q_channel, bits, bases)
    
    # Sifting
    alice.send_basis_to_bob(secure_conn, bases)
    
    len_bytes = _recv_exact(secure_conn, 4)
    length = int.from_bytes(len_bytes, 'big')
    bob_bases_msg = _recv_exact(secure_conn, length)
    bob_bases = json.loads(bob_bases_msg.decode())['data']
    
    alice_sifted = sifting.sift_keys(bases, bob_bases, bits)
    
    # Reconciliation (Cascade)
    # Bob sends his sifted key to Alice so Alice can see if there are errors? 
    # Usually Alice sends parities. For simplicity here, we simulate it by Alice just proceeding.
    # In bob_node.py, Bob corrects his key to match Alice's (simulated oracle).
    # Since Bob does the work, Alice just takes her sifted key.
    
    # Privacy Amplification or classical-key ablation
    if config.ENABLE_QKD:
        aes_key = privacy_amplification.apply_hash(alice_sifted)
    else:
        logger.warning("QKD ablation enabled: using fixed classical demo key.")
        aes_key = hashlib.sha256(b"classical-demo-key").digest()
    
    # --- PHASE 7: Payload Transmission ---
    # Dummy URL for Bob's ML engine extraction (since Alice is sending data to a URL context conceptually)
    # The URL represents the request Alice made to Bob's server
    dummy_url = "https://bob-secure-server.com/api/data?req=123"
    payload_bytes = payload_text.encode('utf-8')
    nonce, ciphertext, tag = aes_gcm.encrypt_payload(aes_key, payload_bytes)
    
    # --- PHASE 8: Quantum-assisted tamper signaling ---
    g1_sv = g1_sender.compute_g1_state(ciphertext)
    
    # Send classical payload data + classical URL over TLS
    payload_msg = pickle.dumps({
        "url": dummy_url,
        "nonce": nonce,
        "ciphertext": ciphertext,
        "tag": tag
    })
    secure_conn.sendall(len(payload_msg).to_bytes(4, 'big') + payload_msg)
    
    # Send G1 tamper-signaling state over quantum socket.
    # Wait for Bob to be ready for the state.
    time.sleep(1)
    q_channel.send_qubit(g1_sv)
    
    logger.info("Alice Pipeline Complete. Shutting down.")
    q_channel.close()
    secure_conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", default="Hello Quantum World")
    args = parser.parse_args()
    
    try:
        run_alice(args.payload)
    except Exception as e:
        logger.exception("Alice Node Crashed:")
