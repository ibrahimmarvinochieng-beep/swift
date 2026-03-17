"""Graph Service configuration."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment."""

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 300

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_graph_updates_topic: str = "graph.updates"
    kafka_events_topic: str = "events.graph_modifications"

    api_key_header: str = "X-API-Key"
    api_key: str = ""  # If set, require for API access
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    rate_limit_per_minute: int = 60

    max_traversal_depth: int = 10
    default_query_limit: int = 100

    class Config:
        env_file = ".env"
        env_prefix = "GRAPH_"


@lru_cache
def get_settings() -> Settings:
    return Settings()
