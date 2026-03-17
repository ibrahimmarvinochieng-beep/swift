"""Single entry-point to run the entire Swift platform locally.

    python run_local.py          — HTTP  (default)
    python run_local.py --tls    — HTTPS with self-signed certs

Starts:
  - FastAPI server on http(s)://localhost:8000
  - Background pipeline loop (collectors + detection)
  - Swagger docs at http(s)://localhost:8000/docs

No Docker, Kafka, or PostgreSQL required.  Everything runs in-process.
"""

import os
import sys
import uvicorn


def main():
    tls = "--tls" in sys.argv or os.getenv("TLS_ENABLED", "false").lower() == "true"
    scheme = "https" if tls else "http"

    print()
    print("=" * 60)
    print("  Swift Event Intelligence Platform")
    print("=" * 60)
    print()
    print(f"  API + Swagger:  {scheme}://localhost:8000/docs")
    print(f"  Health check:   {scheme}://localhost:8000/health")
    print(f"  Metrics:        {scheme}://localhost:8000/metrics")
    print()
    print("  Default login:  admin / SwiftAdmin2026!")
    print()
    if tls:
        print("  TLS:            ENABLED (self-signed certs)")
    else:
        print("  TLS:            disabled  (use --tls to enable)")
    print()
    print("  The pipeline will seed events on startup,")
    print("  then run a collection cycle every 60 seconds.")
    print("=" * 60)
    print()

    uv_kwargs = dict(
        app="api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        access_log=True,
    )

    if tls:
        cert = os.getenv("TLS_CERT_FILE", "certs/swift-server.pem")
        key = os.getenv("TLS_KEY_FILE", "certs/swift-server-key.pem")
        if not os.path.exists(cert) or not os.path.exists(key):
            print("  [!] TLS certs not found — generating...")
            from certs.generate_certs import generate
            generate()
        uv_kwargs["ssl_certfile"] = cert
        uv_kwargs["ssl_keyfile"] = key

    uvicorn.run(**uv_kwargs)


if __name__ == "__main__":
    main()
