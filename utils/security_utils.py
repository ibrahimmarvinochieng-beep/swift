"""Security utilities — passwords, JWT, field encryption, input sanitization.

Encryption at rest is managed by KeyManager which supports:
  - Raw Fernet keys (env var)
  - Password-derived keys (PBKDF2-HMAC-SHA256, 600k iterations)
  - Key rotation via MultiFernet
  - Pluggable backends (env / Vault / AWS Secrets Manager)

Key material is NEVER logged or returned in API responses.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from utils.config_loader import get_settings
from utils.key_manager import KeyManager
from utils.logger import logger

settings = get_settings()

# ── KeyManager singleton (supports rotation + KDF) ───────────────
_key_manager = KeyManager(
    backend_name=settings.key_backend,
    fernet_key=settings.fernet_key,
    fernet_key_password=settings.fernet_key_password,
    fernet_key_salt=settings.fernet_key_salt,
    fernet_keys_previous=settings.fernet_keys_previous,
)


def get_key_manager() -> KeyManager:
    """Expose the singleton for repository re-encryption and health checks."""
    return _key_manager


# ── Password hashing (bcrypt) ────────────────────────────────────

def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))


# ── JWT tokens (HMAC-SHA256) ─────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expiry_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return {}


# ── Field-level encryption (via KeyManager / MultiFernet) ─────────

def encrypt_field(plaintext: str) -> str:
    """Encrypt a string field for storage. Returns base64 ciphertext."""
    return _key_manager.encrypt(plaintext)


def decrypt_field(ciphertext: str) -> str:
    """Decrypt a previously encrypted field (tries all rotation keys)."""
    return _key_manager.decrypt(ciphertext)


def encrypt_event_fields(event: dict) -> dict:
    """Encrypt sensitive fields in an event dict before storage."""
    if not settings.encrypt_sensitive_fields:
        return event

    encrypted = event.copy()
    sensitive_keys = ["description", "raw_text"]
    for key in sensitive_keys:
        if key in encrypted and encrypted[key]:
            encrypted[key] = encrypt_field(encrypted[key])
    encrypted["_encrypted"] = True
    return encrypted


def decrypt_event_fields(event: dict) -> dict:
    """Decrypt sensitive fields when reading an event."""
    if not event.get("_encrypted"):
        return event

    decrypted = event.copy()
    sensitive_keys = ["description", "raw_text"]
    for key in sensitive_keys:
        if key in decrypted and decrypted[key]:
            decrypted[key] = decrypt_field(decrypted[key])
    decrypted.pop("_encrypted", None)
    return decrypted


# ── Input sanitization ───────────────────────────────────────────

def sanitize_input(text: str) -> str:
    if not text:
        return ""
    dangerous = ["<script>", "</script>", "javascript:", "onerror=", "onload=",
                 "onclick=", "onmouseover=", "onfocus=", "eval(", "document.cookie"]
    cleaned = text
    for pattern in dangerous:
        cleaned = cleaned.replace(pattern, "")
        cleaned = cleaned.replace(pattern.upper(), "")
    return cleaned.strip()
