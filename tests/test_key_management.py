"""Tests for key management — derivation, rotation, encrypt/decrypt."""

import base64
import os
import pytest
from cryptography.fernet import Fernet

from utils.key_manager import KeyManager, derive_key_from_password


class TestKeyDerivation:
    def test_pbkdf2_derives_valid_fernet_key(self):
        salt = os.urandom(16)
        key = derive_key_from_password("my-strong-passphrase", salt)
        f = Fernet(key)
        ct = f.encrypt(b"hello")
        assert f.decrypt(ct) == b"hello"

    def test_same_password_and_salt_produce_same_key(self):
        salt = os.urandom(16)
        k1 = derive_key_from_password("pass123", salt)
        k2 = derive_key_from_password("pass123", salt)
        assert k1 == k2

    def test_different_salt_produces_different_key(self):
        k1 = derive_key_from_password("pass123", os.urandom(16))
        k2 = derive_key_from_password("pass123", os.urandom(16))
        assert k1 != k2

    def test_different_password_produces_different_key(self):
        salt = os.urandom(16)
        k1 = derive_key_from_password("alpha", salt)
        k2 = derive_key_from_password("bravo", salt)
        assert k1 != k2


class TestKeyManagerRawKey:
    def test_encrypt_decrypt_roundtrip(self):
        key = Fernet.generate_key().decode()
        km = KeyManager(fernet_key=key)
        ct = km.encrypt("secret data")
        assert ct != "secret data"
        assert km.decrypt(ct) == "secret data"

    def test_empty_string_passthrough(self):
        km = KeyManager(fernet_key=Fernet.generate_key().decode())
        assert km.encrypt("") == ""
        assert km.decrypt("") == ""


class TestKeyManagerPasswordDerived:
    def test_password_derived_roundtrip(self):
        salt = base64.b64encode(os.urandom(16)).decode()
        km = KeyManager(fernet_key_password="strong-password-2026", fernet_key_salt=salt)
        ct = km.encrypt("classified info")
        assert km.decrypt(ct) == "classified info"

    def test_missing_salt_raises(self):
        with pytest.raises(ValueError, match="FERNET_KEY_SALT is required"):
            KeyManager(fernet_key_password="some-password", fernet_key_salt="")


class TestKeyRotation:
    def test_old_key_can_still_decrypt(self):
        old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()

        km_old = KeyManager(fernet_key=old_key)
        ciphertext = km_old.encrypt("legacy data")

        km_new = KeyManager(fernet_key=new_key, fernet_keys_previous=old_key)
        assert km_new.decrypt(ciphertext) == "legacy data"

    def test_rotate_token_re_encrypts_with_current_key(self):
        old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()

        km_old = KeyManager(fernet_key=old_key)
        old_ct = km_old.encrypt("rotate me")

        km_new = KeyManager(fernet_key=new_key, fernet_keys_previous=old_key)
        rotated_ct = km_new.rotate_token(old_ct)

        assert rotated_ct != old_ct

        km_current_only = KeyManager(fernet_key=new_key)
        assert km_current_only.decrypt(rotated_ct) == "rotate me"

    def test_multiple_previous_keys(self):
        k1 = Fernet.generate_key().decode()
        k2 = Fernet.generate_key().decode()
        k3 = Fernet.generate_key().decode()

        ct_k1 = KeyManager(fernet_key=k1).encrypt("from k1")
        ct_k2 = KeyManager(fernet_key=k2).encrypt("from k2")

        km = KeyManager(fernet_key=k3, fernet_keys_previous=f"{k2},{k1}")
        assert km.decrypt(ct_k1) == "from k1"
        assert km.decrypt(ct_k2) == "from k2"
        assert km.key_count == 3

    def test_key_count(self):
        k1 = Fernet.generate_key().decode()
        k2 = Fernet.generate_key().decode()
        assert KeyManager(fernet_key=k1).key_count == 1
        assert KeyManager(fernet_key=k1, fernet_keys_previous=k2).key_count == 2


class TestRepositoryReEncrypt:
    def test_re_encrypt_all(self):
        from db.repository import EventRepository

        repo = EventRepository()
        repo.add_event({"event_id": "re-1", "event_type": "test",
                        "title": "T", "description": "secret info"})
        repo.add_event({"event_id": "re-2", "event_type": "test",
                        "title": "U", "description": "more secrets"})

        result = repo.re_encrypt_all()
        assert result["rotated"] >= 2
        assert result["failed"] == 0

        evt = repo.get_event("re-1")
        assert evt["description"] == "secret info"


class TestKeyManagerHelpers:
    def test_generate_key_is_valid(self):
        key = KeyManager.generate_key()
        assert len(key) == 44
        Fernet(key.encode())

    def test_generate_salt_is_base64(self):
        salt = KeyManager.generate_salt()
        decoded = base64.b64decode(salt.encode())
        assert len(decoded) == 16
