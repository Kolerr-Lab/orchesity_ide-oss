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

    # Optional: Database
    database_url: Optional[str] = None

    # Optional: Redis
    redis_url: Optional[str] = None

    # Optional: Monitoring
    sentry_dsn: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
