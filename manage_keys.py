"""CLI tool for Fernet encryption key management.

Usage:
  python manage_keys.py generate          — generate a new random Fernet key
  python manage_keys.py generate-salt     — generate a PBKDF2 salt
  python manage_keys.py derive            — derive a key from a password + salt
  python manage_keys.py verify            — verify the current key can encrypt/decrypt
  python manage_keys.py rotate-env        — print .env snippet for rotating to a new key

Never logs or prints existing key material from the environment.
"""

import sys
import getpass


def cmd_generate():
    from utils.key_manager import KeyManager
    key = KeyManager.generate_key()
    print("\n  New Fernet key (set as FERNET_KEY in .env or secrets manager):\n")
    print(f"  FERNET_KEY={key}\n")


def cmd_generate_salt():
    from utils.key_manager import KeyManager
    salt = KeyManager.generate_salt()
    print("\n  New PBKDF2 salt (set as FERNET_KEY_SALT in .env):\n")
    print(f"  FERNET_KEY_SALT={salt}\n")


def cmd_derive():
    from utils.key_manager import KeyManager, derive_key_from_password
    import base64

    password = getpass.getpass("  Enter encryption password: ")
    if not password:
        print("  Error: password cannot be empty.")
        sys.exit(1)

    salt_input = input("  Enter FERNET_KEY_SALT (leave blank to generate new): ").strip()
    if not salt_input:
        salt_input = KeyManager.generate_salt()
        print(f"  Generated salt: {salt_input}")

    salt_bytes = base64.b64decode(salt_input.encode("utf-8"))
    derived = derive_key_from_password(password, salt_bytes)

    print("\n  Derived key (set as FERNET_KEY in .env):\n")
    print(f"  FERNET_KEY={derived.decode('utf-8')}")
    print(f"  FERNET_KEY_SALT={salt_input}")
    print(f"  # Remove FERNET_KEY_PASSWORD if using pre-derived key\n")


def cmd_verify():
    from utils.key_manager import KeyManager
    from utils.config_loader import get_settings
    settings = get_settings()

    km = KeyManager(
        backend_name=settings.key_backend,
        fernet_key=settings.fernet_key,
        fernet_key_password=settings.fernet_key_password,
        fernet_key_salt=settings.fernet_key_salt,
        fernet_keys_previous=settings.fernet_keys_previous,
    )

    test_data = "swift_encryption_health_check"
    encrypted = km.encrypt(test_data)
    decrypted = km.decrypt(encrypted)

    if decrypted == test_data:
        print(f"\n  Key verification: PASSED")
        print(f"  Active keys in chain: {km.key_count}")
        if km.key_count > 1:
            print(f"  Rotation pending: call POST /api/v1/admin/rotate-keys")
        print()
    else:
        print("\n  Key verification: FAILED — decrypt did not match.\n")
        sys.exit(1)


def cmd_rotate_env():
    from utils.key_manager import KeyManager
    new_key = KeyManager.generate_key()

    print("\n  Key Rotation Instructions")
    print("  " + "=" * 50)
    print()
    print("  1. Copy your current FERNET_KEY value")
    print("  2. Update .env with these values:\n")
    print(f"     FERNET_KEY={new_key}")
    print(f"     FERNET_KEYS_PREVIOUS=<your-old-key-here>")
    print()
    print("  3. Restart the Swift service")
    print("  4. Call the rotation endpoint:")
    print("     POST /api/v1/admin/rotate-keys")
    print("  5. After confirming all data re-encrypted,")
    print("     remove FERNET_KEYS_PREVIOUS from .env\n")


COMMANDS = {
    "generate": cmd_generate,
    "generate-salt": cmd_generate_salt,
    "derive": cmd_derive,
    "verify": cmd_verify,
    "rotate-env": cmd_rotate_env,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("\n  Swift Key Management CLI")
        print("  " + "-" * 40)
        for name in COMMANDS:
            print(f"    python manage_keys.py {name}")
        print()
        sys.exit(0)

    COMMANDS[sys.argv[1]]()


if __name__ == "__main__":
    main()
