import socket
import ssl
from src.infrastructure import config
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

class TLSClient:
    """Mutual TLS 1.3 Client for authenticated classical communication."""
    def __init__(self, host=config.HOST, port=config.TLS_PORT):
        self.host = host
        self.port = port
        
        # Configure TLS context for mutual authentication
        self.context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=config.CA_CERT)
        self.context.load_cert_chain(certfile=config.ALICE_CERT, keyfile=config.ALICE_KEY)
        self.context.check_hostname = False # Useful for localhost self-signed certs
        self.context.minimum_version = ssl.TLSVersion.TLSv1_3

    def connect(self):
        logger.info(f"Connecting to TLS Server at {self.host}:{self.port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        secure_conn = self.context.wrap_socket(sock, server_hostname=self.host)
        secure_conn.connect((self.host, self.port))
        
        peer_cert = secure_conn.getpeercert()
        logger.info("TLS Handshake successful.")
        logger.debug(f"Server Certificate Subject: {peer_cert.get('subject')}")
        return secure_conn
