import socket
import pickle
import struct
from qiskit.quantum_info import Statevector
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

class QuantumChannel:
    """
    Simulates a quantum quantum channel using a classical socket.
    Transmits serialized Qiskit Statevector objects.
    """
    def __init__(self, host, port, is_server=False):
        self.host = host
        self.port = port
        self.is_server = is_server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None

    def connect(self):
        if self.is_server:
            self.sock.bind((self.host, self.port))
            self.sock.listen(1)
            logger.info(f"Quantum Channel listening on {self.host}:{self.port}...")
            self.conn, addr = self.sock.accept()
            logger.info(f"Quantum Channel connected to {addr}")
        else:
            logger.info(f"Connecting to Quantum Channel at {self.host}:{self.port}...")
            self.sock.connect((self.host, self.port))
            self.conn = self.sock

    def send_qubit(self, statevector: Statevector):
        """Send a Statevector object over the socket."""
        data = pickle.dumps(statevector)
        # Prefix each message with its 4-byte length
        length = struct.pack('!I', len(data))
        self.conn.sendall(length + data)

    def recv_qubit(self) -> Statevector:
        """Receive a Statevector object from the socket."""
        # Read the 4-byte length prefix
        length_bytes = self._recvall(4)
        if not length_bytes:
            return None
        length = struct.unpack('!I', length_bytes)[0]
        
        # Read the exact length of data
        data = self._recvall(length)
        if not data:
            return None
            
        return pickle.loads(data)
        
    def _recvall(self, n):
        """Helper to recv exactly n bytes."""
        data = bytearray()
        while len(data) < n:
            packet = self.conn.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def close(self):
        if self.conn and self.conn != self.sock:
            self.conn.close()
        self.sock.close()
        logger.info("Quantum Channel closed.")
