"""Generate self-signed TLS certificates for local development.

Run once:  python certs/generate_certs.py

Produces:
  certs/swift-ca.pem       — CA certificate (trust this in clients)
  certs/swift-server.pem   — Server certificate
  certs/swift-server-key.pem — Server private key
"""

import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

CERT_DIR = os.path.dirname(os.path.abspath(__file__))


def generate():
    # ── CA key + cert ─────────────────────────────────────────────
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    ca_name = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Swift AI Technologies"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Swift Dev CA"),
    ])
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )

    # ── Server key + cert ─────────────────────────────────────────
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_name = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Swift AI Technologies"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_name)
        .issuer_name(ca_name)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("*.swift.ai"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        )
        .add_extension(
            x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    # ── Write files ───────────────────────────────────────────────
    def write_pem(filename, data):
        path = os.path.join(CERT_DIR, filename)
        with open(path, "wb") as f:
            f.write(data)
        print(f"  Written: {path}")

    write_pem("swift-ca.pem", ca_cert.public_bytes(serialization.Encoding.PEM))
    write_pem(
        "swift-server-key.pem",
        server_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ),
    )
    write_pem("swift-server.pem", server_cert.public_bytes(serialization.Encoding.PEM))

    print("\n  TLS certificates generated successfully.")
    print("  For production, replace these with certificates from a real CA.")


if __name__ == "__main__":
    import ipaddress
    generate()
