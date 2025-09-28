"""
Configuration management for Orchesity IDE OSS
Enhanced with validation, environment-specific settings, and proper typing
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any
from pathlib import Path
import os
import secrets
from enum import Enum


class Environment(str, Enum):
    """Application environment"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class RoutingStrategy(str, Enum):
    """LLM routing strategies"""

    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    RANDOM = "random"
    PRIORITY = "priority"


class Settings(BaseSettings):
    """Application settings with validation and environment-specific configuration"""

    # Application
    app_name: str = Field(default="Orchesity IDE OSS", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT, description="Deployment environment"
    )
    debug: bool = Field(default=True, description="Enable debug mode")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for encryption",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")

    # LLM Providers
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API key"
    )
    gemini_api_key: Optional[str] = Field(
        default=None, description="Google Gemini API key"
    )
    grok_api_key: Optional[str] = Field(default=None, description="xAI Grok API key")

    # Orchestration
    max_concurrent_requests: int = Field(
        default=5, ge=1, le=100, description="Max concurrent requests"
    )
    request_timeout: int = Field(
        default=30, ge=1, le=300, description="Request timeout in seconds"
    )
    routing_strategy: RoutingStrategy = Field(
        default=RoutingStrategy.LOAD_BALANCED, description="Provider routing strategy"
    )

    # Database
    database_url: str = Field(
        default="postgresql://orchesity:orchesity@localhost:5432/orchesity_db",
        description="PostgreSQL connection URL",
    )
    database_echo: bool = Field(default=False, description="Enable SQL query logging")
    database_pool_size: int = Field(
        default=10, ge=1, le=100, description="Connection pool size"
    )
    database_max_overflow: int = Field(
        default=20, ge=0, le=100, description="Max overflow connections"
    )
    database_pool_timeout: int = Field(
        default=30, ge=1, le=300, description="Pool timeout in seconds"
    )
    database_pool_recycle: int = Field(
        default=3600, ge=60, le=86400, description="Pool recycle time in seconds"
    )

    # Redis Cache
    enable_caching: bool = Field(default=True, description="Enable Redis caching")
    redis_url: str = Field(
        default="redis://localhost:6379", description="Redis connection URL"
    )
    redis_db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    redis_max_connections: int = Field(
        default=10, ge=1, le=100, description="Max Redis connections"
    )
    redis_socket_timeout: int = Field(
        default=5, ge=1, le=60, description="Redis socket timeout"
    )
    redis_socket_connect_timeout: int = Field(
        default=5, ge=1, le=60, description="Redis connect timeout"
    )
    cache_expire_seconds: int = Field(
        default=3600, ge=60, le=86400, description="Default cache expiration"
    )

    # Monitoring & Observability
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(
        default=9090, ge=1, le=65535, description="Metrics server port"
    )
    enable_health_checks: bool = Field(default=True, description="Enable health checks")
    health_check_interval: int = Field(
        default=30, ge=5, le=300, description="Health check interval"
    )

    # Security
    cors_origins: List[str] = Field(
        default_factory=lambda: ["*"], description="CORS allowed origins"
    )
    cors_allow_credentials: bool = Field(
        default=True, description="Allow CORS credentials"
    )
    cors_allow_methods: List[str] = Field(
        default_factory=lambda: ["*"], description="CORS allowed methods"
    )
    cors_allow_headers: List[str] = Field(
        default_factory=lambda: ["*"], description="CORS allowed headers"
    )

    # Rate Limiting
    enable_rate_limiting: bool = Field(
        default=False, description="Enable rate limiting"
    )
    rate_limit_requests: int = Field(
        default=100, ge=1, le=10000, description="Requests per window"
    )
    rate_limit_window: int = Field(
        default=60, ge=1, le=3600, description="Rate limit window in seconds"
    )

    # Optional Services
    sentry_dsn: Optional[str] = Field(
        default=None, description="Sentry DSN for error tracking"
    )
    prometheus_gateway: Optional[str] = Field(
        default=None, description="Prometheus push gateway URL"
    )

    # Feature Flags
    lightweight_mode: bool = Field(
        default=False, description="Run in lightweight mode (no DB/Redis)"
    )
    enable_caching: bool = Field(default=True, description="Enable response caching")
    enable_analytics: bool = Field(default=True, description="Enable usage analytics")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        use_enum_values = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v.startswith(
            (
                "postgresql://",
                "postgresql+asyncpg://",
                "sqlite://",
                "sqlite+aiosqlite://",
            )
        ):
            raise ValueError(
                "Database URL must be a valid PostgreSQL or SQLite connection string"
            )
        return v

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v):
        """Validate Redis URL format"""
        if not v.startswith(("redis://", "rediss://", "unix://")):
            raise ValueError("Redis URL must be a valid Redis connection string")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT

    @property
    def configured_providers(self) -> List[str]:
        """Get list of configured LLM providers"""
        providers = []
        if self.openai_api_key:
            providers.append("openai")
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.gemini_api_key:
            providers.append("gemini")
        if self.grok_api_key:
            providers.append("grok")
        return providers

    def get_provider_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider"""
        key_map = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "gemini": self.gemini_api_key,
            "grok": self.grok_api_key,
        }
        return key_map.get(provider)


# Global settings instance
settings = Settings()
