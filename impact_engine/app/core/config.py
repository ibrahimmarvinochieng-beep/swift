"""Impact Engine configuration."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    graph_service_url: str = "http://localhost:8000"
    graph_timeout_seconds: float = 10.0
    graph_retry_attempts: int = 3

    redis_url: str = "redis://localhost:6379/1"
    simulation_cache_ttl: int = 600
    aggregation_mode: str = "max"  # "max" or "weighted_sum"
    time_decay_scale_factor: float = 24.0
    max_propagation_depth: int = 3
    max_paths_per_request: int = 5000

    api_key: str = ""
    rate_limit_per_minute: int = 30

    class Config:
        env_file = ".env"
        env_prefix = "IMPACT_"


@lru_cache
def get_settings() -> Settings:
    return Settings()
