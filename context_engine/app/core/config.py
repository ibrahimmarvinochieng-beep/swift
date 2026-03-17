"""Personal Context Engine configuration."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./context.db"
    redis_url: str = "redis://localhost:6379/2"
    feed_cache_ttl: int = 300
    impact_engine_url: str = "http://localhost:8001"
    graph_service_url: str = "http://localhost:8000"
    location_match_weight: float = 0.3
    industry_match_weight: float = 0.3
    interest_match_weight: float = 0.2
    behavioral_weight: float = 0.2
    api_key: str = ""
    rate_limit_per_minute: int = 60

    class Config:
        env_file = ".env"
        env_prefix = "CONTEXT_"


@lru_cache
def get_settings():
    return Settings()
