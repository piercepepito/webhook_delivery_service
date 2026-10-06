from cryptography.fernet import Fernet

from dotenv import load_dotenv
import os
load_dotenv()
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if ENCRYPTION_KEY is None:
    raise RuntimeError("Encryption key not found")


f = Fernet(ENCRYPTION_KEY)


def encrypt_keys(token: str) -> str:
    """
    Encrypts the secret and api keys
    """
    return f.encrypt(token.encode()).decode()


def decrypt_keys(token: str) -> str:
    """
    Decrypts the secret and api keys
    """
    return f.decrypt(token).decode()

