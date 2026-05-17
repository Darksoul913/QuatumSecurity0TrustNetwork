import socket
import ssl
from src.infrastructure import config
from src.infrastructure.logger import get_logger

logger = get_logger(__name__)

class TLSServer:
    """Mutual TLS 1.3 Server for authenticated classical communication."""
    def __init__(self, host=config.HOST, port=config.TLS_PORT):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Configure TLS context for mutual authentication
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.verify_mode = ssl.CERT_REQUIRED
        self.context.load_cert_chain(certfile=config.BOB_CERT, keyfile=config.BOB_KEY)
        self.context.load_verify_locations(cafile=config.CA_CERT)
        self.context.minimum_version = ssl.TLSVersion.TLSv1_3

    def start(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        logger.info(f"TLS Server listening on {self.host}:{self.port}...")
        
        conn, addr = self.sock.accept()
        secure_conn = self.context.wrap_socket(conn, server_side=True)
        peer_cert = secure_conn.getpeercert()
        
        logger.info(f"TLS Handshake successful with client: {addr}")
        logger.debug(f"Client Certificate Subject: {peer_cert.get('subject')}")
        return secure_conn
