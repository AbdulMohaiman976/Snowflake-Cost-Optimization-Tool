# api/session.py
# ─────────────────────────────────────────────────────────────────
# Session ID encryption using Fernet (symmetric AES-128-CBC + HMAC)
# Raw UUID is internal — client only ever sees the encrypted token.
# ─────────────────────────────────────────────────────────────────

import uuid
import os
import base64
from cryptography.fernet import Fernet
import logging

log = logging.getLogger("session")


def _get_fernet() -> Fernet:
    """Load the Fernet cipher from the SECRET_KEY env variable."""
    key = os.getenv("SESSION_SECRET_KEY")
    if not key:
        raise RuntimeError(
            "SESSION_SECRET_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def new_session() -> tuple[str, str]:
    """
    Create a new session.

    Returns:
        raw_id  (str) — internal UUID stored in MongoDB  (never sent to client)
        token   (str) — Fernet-encrypted token sent to the client as session_id
    """
    raw_id = str(uuid.uuid4())
    f = _get_fernet()
    token = f.encrypt(raw_id.encode()).decode()
    log.info(f"New session created: {raw_id[:8]}...")
    return raw_id, token


def generate_token(raw_id: str) -> str:
    """Encrypt an existing raw UUID into a session token."""
    f = _get_fernet()
    token = f.encrypt(raw_id.encode()).decode()
    return token


def decrypt_session(token: str) -> str:
    """
    Decrypt a client-supplied token back to the raw UUID.

    Raises:
        ValueError — if the token is invalid, expired, or tampered with.
    """
    try:
        f = _get_fernet()
        raw_id = f.decrypt(token.encode()).decode()
        return raw_id
    except Exception as e:
        log.warning(f"Invalid session token: {e}")
        raise ValueError("Invalid or expired session token")
