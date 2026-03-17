"""Centralized encryption key management.

Supports:
  1. Raw Fernet keys from environment variables (FERNET_KEY)
  2. Password-derived keys via PBKDF2-HMAC-SHA256 (FERNET_KEY_PASSWORD + FERNET_KEY_SALT)
  3. Key rotation via MultiFernet (FERNET_KEYS_PREVIOUS — comma-separated old keys)
  4. Pluggable backend interface for Vault / AWS Secrets Manager (future)

Security invariants:
  - Key material is NEVER logged, printed, or returned in API responses
  - Keys are loaded once at startup and held only in memory
  - Password-derived keys use 600 000 PBKDF2 iterations (OWASP 2024 recommendation)
"""

import base64
import os
from typing import List, Optional

from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from utils.logger import logger


PBKDF2_ITERATIONS = 600_000
PBKDF2_KEY_LENGTH = 32


# ── Key derivation ────────────────────────────────────────────────────

def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Derive a 32-byte Fernet-compatible key from a password using PBKDF2-HMAC-SHA256.

    Returns a URL-safe base64-encoded key suitable for Fernet.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=PBKDF2_KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    raw = kdf.derive(password.encode("utf-8"))
    return base64.urlsafe_b64encode(raw)


def _mask_key(key_bytes: bytes) -> str:
    """Return a safe representation for logging (first 4 chars + masked)."""
    text = key_bytes.decode("utf-8") if isinstance(key_bytes, bytes) else str(key_bytes)
    if len(text) <= 8:
        return "****"
    return text[:4] + "****" + text[-4:]


# ── Backend interface ─────────────────────────────────────────────────

class KeyBackend:
    """Base class for secret backends. Override `fetch_secret` for Vault / AWS / GCP."""

    def fetch_secret(self, key_name: str) -> Optional[str]:
        raise NotImplementedError


class EnvBackend(KeyBackend):
    """Load secrets from environment variables (default for local/dev)."""

    def fetch_secret(self, key_name: str) -> Optional[str]:
        return os.environ.get(key_name) or None


class VaultBackend(KeyBackend):
    """Placeholder for HashiCorp Vault integration.

    Production usage:
      pip install hvac
      Set VAULT_ADDR and VAULT_TOKEN environment variables.
    """

    def fetch_secret(self, key_name: str) -> Optional[str]:
        try:
            import hvac  # type: ignore[import-untyped]
            client = hvac.Client(
                url=os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200"),
                token=os.environ.get("VAULT_TOKEN", ""),
            )
            resp = client.secrets.kv.v2.read_secret_version(path="swift/encryption")
            return resp["data"]["data"].get(key_name)
        except Exception as exc:
            logger.error("vault_fetch_failed", key=key_name, error=str(exc))
            return None


class AWSSecretsBackend(KeyBackend):
    """Placeholder for AWS Secrets Manager integration.

    Production usage:
      pip install boto3
      Ensure IAM role or AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY are set.
    """

    def fetch_secret(self, key_name: str) -> Optional[str]:
        try:
            import boto3  # type: ignore[import-untyped]
            client = boto3.client("secretsmanager", region_name=os.environ.get("AWS_REGION", "us-east-1"))
            resp = client.get_secret_value(SecretId=f"swift/{key_name}")
            return resp.get("SecretString")
        except Exception as exc:
            logger.error("aws_sm_fetch_failed", key=key_name, error=str(exc))
            return None


_BACKENDS = {
    "env": EnvBackend,
    "vault": VaultBackend,
    "aws": AWSSecretsBackend,
}


# ── KeyManager ────────────────────────────────────────────────────────

class KeyManager:
    """Manages Fernet encryption keys with rotation support.

    Resolution order:
      1. FERNET_KEY (raw base64 Fernet key)          — fastest, recommended for prod
      2. FERNET_KEY_PASSWORD + FERNET_KEY_SALT        — derives key via PBKDF2
      3. Auto-generate an ephemeral key (dev only)    — warns loudly

    For rotation, set FERNET_KEYS_PREVIOUS to a comma-separated list of old keys.
    MultiFernet will encrypt with the current key and decrypt with any key in the chain.
    """

    def __init__(
        self,
        backend_name: str = "env",
        fernet_key: str = "",
        fernet_key_password: str = "",
        fernet_key_salt: str = "",
        fernet_keys_previous: str = "",
    ):
        backend = _BACKENDS.get(backend_name, EnvBackend)()

        current_key = self._resolve_current_key(
            backend, fernet_key, fernet_key_password, fernet_key_salt
        )
        previous_keys = self._resolve_previous_keys(backend, fernet_keys_previous)

        all_fernets: List[Fernet] = [Fernet(current_key)]
        for pk in previous_keys:
            all_fernets.append(Fernet(pk))

        self._multi = MultiFernet(all_fernets)
        self._current = all_fernets[0]
        self._key_count = len(all_fernets)

        logger.info(
            "key_manager_initialized",
            backend=backend_name,
            active_keys=self._key_count,
            current_key_fingerprint=_mask_key(current_key),
        )

    # ── Key resolution (private) ──────────────────────────────────

    def _resolve_current_key(
        self,
        backend: KeyBackend,
        raw_key: str,
        password: str,
        salt: str,
    ) -> bytes:
        # 1) Try raw Fernet key from config or backend
        key_str = raw_key or backend.fetch_secret("FERNET_KEY")
        if key_str:
            return key_str.encode("utf-8")

        # 2) Try password-based derivation
        pwd = password or backend.fetch_secret("FERNET_KEY_PASSWORD")
        if pwd:
            salt_str = salt or backend.fetch_secret("FERNET_KEY_SALT")
            if not salt_str:
                raise ValueError(
                    "FERNET_KEY_SALT is required when using FERNET_KEY_PASSWORD. "
                    "Generate one with: python -c \"import os, base64; print(base64.b64encode(os.urandom(16)).decode())\""
                )
            salt_bytes = base64.b64decode(salt_str.encode("utf-8"))
            logger.info("key_derived_from_password", kdf="PBKDF2-HMAC-SHA256",
                        iterations=PBKDF2_ITERATIONS)
            return derive_key_from_password(pwd, salt_bytes)

        # 3) Auto-generate ephemeral key (development only)
        logger.warning(
            "fernet_key_ephemeral",
            hint="Data encrypted in this session CANNOT be decrypted after restart. "
                 "Set FERNET_KEY or FERNET_KEY_PASSWORD in your environment.",
        )
        return Fernet.generate_key()

    def _resolve_previous_keys(self, backend: KeyBackend, csv_keys: str) -> List[bytes]:
        raw = csv_keys or backend.fetch_secret("FERNET_KEYS_PREVIOUS") or ""
        if not raw.strip():
            return []
        keys = [k.strip().encode("utf-8") for k in raw.split(",") if k.strip()]
        logger.info("previous_rotation_keys_loaded", count=len(keys))
        return keys

    # ── Public API ────────────────────────────────────────────────

    def encrypt(self, plaintext: str) -> str:
        """Encrypt with the current (newest) key."""
        if not plaintext:
            return plaintext
        return self._multi.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt trying all keys in the rotation chain."""
        if not ciphertext:
            return ciphertext
        try:
            return self._multi.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            return ciphertext

    def rotate_token(self, ciphertext: str) -> str:
        """Re-encrypt a token with the current key (used during key rotation)."""
        if not ciphertext:
            return ciphertext
        try:
            return self._multi.rotate(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            return ciphertext

    @property
    def key_count(self) -> int:
        return self._key_count

    @staticmethod
    def generate_key() -> str:
        """Generate a new random Fernet key (for provisioning / rotation)."""
        return Fernet.generate_key().decode("utf-8")

    @staticmethod
    def generate_salt() -> str:
        """Generate a random 16-byte salt (base64) for password derivation."""
        return base64.b64encode(os.urandom(16)).decode("utf-8")
