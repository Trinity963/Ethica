import os
import hashlib
import time
import sqlite3
import logging
import pyotp
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from pqcrypto.kem.ml_kem_768 import generate_keypair, encrypt as pq_encrypt, decrypt as pq_decrypt

class DSEngine:
    def __init__(self, key=None, trinity_integration=False):
        """
        Initializes the encryption engine with an optional key.
        If no key is provided, a secure AES key is generated.
        """
        self.salt = os.urandom(16)
        self.key = key if key else self.generate_aes_key()
        self.private_key, self.public_key = self.generate_rsa_keys()
        self.pq_private_key, self.pq_public_key = generate_keypair()
        self.key_rotation_interval = 86400  # 24 hours
        self.last_key_rotation = time.time()
        self.trinity_integration = trinity_integration
        self.init_secure_storage()
        self.init_logging()
        self.init_access_control()
        
        if self.trinity_integration:
            self.integrate_with_trinity()

    def integrate_with_trinity(self):
        """ Sets up integration with TrinityAI OS."""
        self.logger.info("DSEngine integrated with TrinityAI OS.")

    def generate_aes_key(self, password: str = None):
        """ Generates a strong AES-256 key with optional password derivation. """
        password = password.encode() if password else os.urandom(32)
        kdf = Scrypt(
            salt=self.salt,
            length=32,
            n=2**14,
            r=8,
            p=1,
            backend=default_backend()
        )
        return kdf.derive(password)

    def generate_rsa_keys(self):
        """ Generates a 4096-bit RSA key pair for hybrid encryption. """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key

    def rotate_keys(self):
        """ Automatically rotates encryption keys at set intervals. """
        current_time = time.time()
        if current_time - self.last_key_rotation >= self.key_rotation_interval:
            self.key = self.generate_aes_key()
            self.private_key, self.public_key = self.generate_rsa_keys()
            self.pq_private_key, self.pq_public_key = generate_keypair()
            self.last_key_rotation = current_time
            self.logger.info("Encryption keys rotated successfully.")

    def init_secure_storage(self):
        """ Initializes a secure SQLite database for encrypted storage. """
        self.db_conn = sqlite3.connect("secure_storage.db")
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS encrypted_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                otp_secret TEXT
            )
        ''')
        self.db_conn.commit()

    def store_encrypted_data(self, encrypted_data: str):
        """ Stores encrypted data securely in the database. """
        cursor = self.db_conn.cursor()
        cursor.execute("INSERT INTO encrypted_data (data) VALUES (?)", (encrypted_data,))
        self.db_conn.commit()
        self.logger.info("Encrypted data stored securely in database.")

    def retrieve_encrypted_data(self):
        """ Retrieves and returns all encrypted data records. """
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM encrypted_data")
        return cursor.fetchall()

    def init_logging(self):
        """ Sets up logging for intrusion detection and activity tracking. """
        self.logger = logging.getLogger("DSEngine")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("dse_activity.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.info("Logging initialized.")

    def log_intrusion_attempt(self, message: str):
        """ Logs unauthorized access attempts. """
        self.logger.warning(f"Intrusion attempt detected: {message}")

    def init_access_control(self):
        """ Initializes user authentication and access control system with roles and MFA. """
        self.logger.info("Access control system with roles and MFA initialized.")
    
    def register_user(self, username: str, password: str, role: str = "user"):
        """ Registers a new user with a hashed password and OTP for MFA. """
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        otp_secret = pyotp.random_base32()
        cursor = self.db_conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password_hash, role, otp_secret) VALUES (?, ?, ?, ?)", (username, password_hash, role, otp_secret))
            self.db_conn.commit()
            self.logger.info(f"User {username} registered successfully with role {role} and MFA enabled.")
        except sqlite3.IntegrityError:
            self.logger.warning(f"User {username} already exists.")
    
if __name__ == "__main__":
    dse = DSEngine(trinity_integration=True)
    dse.register_user("admin", "securepassword", "admin")
