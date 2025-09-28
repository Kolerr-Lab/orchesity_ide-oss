"""
Configuration settings for Orchesity IDE OSS
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "Orchesity IDE OSS"
    app_version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    grok_api_key: Optional[str] = None

    # Orchestration
    max_concurrent_requests: int = 5
    request_timeout: int = 30
    routing_strategy: str = (
        "load_balanced"  # load_balanced, round_robin, random, priority
    )

    # Database
    database_url: str = "postgresql://orchesity:orchesity@localhost:5432/orchesity_db"
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_max_connections: int = 10
    cache_expire_seconds: int = 3600  # 1 hour default

    # Optional: Monitoring
    sentry_dsn: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
