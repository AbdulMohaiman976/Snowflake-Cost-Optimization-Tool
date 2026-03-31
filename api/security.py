# api/security.py
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

# We use a static key from environment or a default one
# IN PRODUCTION: Use a proper secrets manager
ENCRYPTION_KEY = os.getenv("FERNET_KEY")
if not ENCRYPTION_KEY:
    # Generate a temporary one if none exists (not recommended for persistent data)
    # But for this tool session-based encryption it's okay-ish if not restart-persistent
    ENCRYPTION_KEY = Fernet.generate_key().decode()

_cipher = Fernet(ENCRYPTION_KEY.encode())

def encrypt_password(password: str) -> str:
    if not password: return ""
    return _cipher.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    if not encrypted_password: return ""
    try:
        return _cipher.decrypt(encrypted_password.encode()).decode()
    except Exception:
        return ""
