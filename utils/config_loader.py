from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = Field(default="postgresql://swift_user:pass@localhost:5432/swift_db")
    redis_url: str = Field(default="redis://localhost:6379/0")
    kafka_broker: str = Field(default="localhost:9092")

    jwt_secret: str = Field(default="CHANGE_THIS")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiry_minutes: int = Field(default=30)

    news_api_key: str = Field(default="")
    mapbox_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    twitter_bearer_token: str = Field(default="")
    weather_api_key: str = Field(default="")

    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")
    rate_limit: str = Field(default="100/minute")

    dedup_similarity_threshold: float = Field(default=0.85)
    event_confidence_threshold: float = Field(default=0.75)

    classifier_use_fast_model: bool = Field(default=True)
    classifier_multi_label: bool = Field(default=False)
    classifier_confidence_temperature: float = Field(default=1.0)
    classifier_finetuned_model_path: str = Field(
        default="",
        description="Path to fine-tuned news classifier (e.g. models/news_classifier). If set, used for news-style text.",
    )

    pipeline_autostart: bool = Field(default=True)
    pipeline_interval_seconds: int = Field(default=60)

    collector_max_retries: int = Field(default=3)
    collector_retry_base_delay: float = Field(default=1.0)
    collector_retry_max_delay: float = Field(default=60.0)
    ingestion_max_per_source_per_minute: int = Field(default=60)

    # ── TLS / Encryption ──────────────────────────────────────────
    tls_enabled: bool = Field(default=False)
    tls_cert_file: str = Field(default="certs/swift-server.pem")
    tls_key_file: str = Field(default="certs/swift-server-key.pem")
    tls_ca_file: str = Field(default="certs/swift-ca.pem")

    db_sslmode: str = Field(default="prefer")
    redis_ssl: bool = Field(default=False)
    redis_password: str = Field(default="")
    kafka_security_protocol: str = Field(default="PLAINTEXT")
    kafka_ssl_cafile: str = Field(default="")

    encrypt_sensitive_fields: bool = Field(default=True)

    # ── Persistence ───────────────────────────────────────────────
    # "memory" = pure RAM (tests), "sqlite" = file-backed (default)
    persistence_backend: str = Field(default="sqlite")
    sqlite_db_path: str = Field(default="data/swift.db")

    # ── Distributed rate limiter (Token Bucket) ───────────────────
    rate_limiter_enabled: bool = Field(default=True)
    rate_limiter_bucket_size: int = Field(default=100)
    rate_limiter_refill_rate: float = Field(default=10.0)
    rate_limiter_key_prefix: str = Field(default="rl")
    rate_limiter_use_redis: bool = Field(default=True)

    # ── Key management ────────────────────────────────────────────
    # Backend: "env" (default), "vault" (HashiCorp), "aws" (Secrets Manager)
    key_backend: str = Field(default="env")

    # Option A: raw Fernet key (base64, 44 chars) from env var
    fernet_key: str = Field(default="")

    # Option B: derive key from password via PBKDF2-HMAC-SHA256
    fernet_key_password: str = Field(default="")
    fernet_key_salt: str = Field(default="")

    # Key rotation: comma-separated list of previous Fernet keys
    fernet_keys_previous: str = Field(default="")

    # ── OpenClaw integration ───────────────────────────────────────
    openclaw_alert_key: str = Field(
        default="",
        description="API key for /api/v1/alerts endpoint (OpenClaw bridge). If set, enables alerts API.",
    )
    openclaw_webhook_url: str = Field(
        default="",
        description="OpenClaw webhook URL (e.g. http://127.0.0.1:18789/hooks/agent). Push events here.",
    )
    openclaw_webhook_token: str = Field(default="", description="Bearer token for OpenClaw webhook.")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
