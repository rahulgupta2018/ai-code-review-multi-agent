"""
Core configuration management for ADK Multi-Agent Code Review MVP.

This module provides environment-based configuration with Pydantic validation
following industrial best practices for production systems.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings
import structlog

logger = structlog.get_logger(__name__)


class Environment(str, Enum):
    """Environment types for the application."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging level configuration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class GeminiModelConfig(BaseSettings):
    """Configuration for Gemini model integration."""
    
    # Model specifications
    model_name: str = Field(default="gemini-1.5-pro", description="Primary Gemini model")
    flash_model_name: str = Field(default="gemini-2.0-flash-exp", description="Fast analysis model")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(default=8192, ge=1, le=32768, description="Maximum output tokens")
    
    # API configuration
    api_key: str = Field(default="dummy-key", env="GEMINI_API_KEY", description="Gemini API key")
    api_base_url: str = Field(default="https://generativelanguage.googleapis.com", description="API base URL")
    timeout_seconds: int = Field(default=120, ge=10, le=600, description="API timeout")
    
    # Rate limiting
    max_requests_per_minute: int = Field(default=30, ge=1, le=1000, description="Rate limit per minute")
    max_concurrent_requests: int = Field(default=5, ge=1, le=20, description="Concurrent request limit")
    
    # Retry configuration
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay_seconds: float = Field(default=1.0, ge=0.1, le=60.0, description="Initial retry delay")
    exponential_backoff_factor: float = Field(default=2.0, ge=1.0, le=10.0, description="Backoff factor")

    model_config = {"env_prefix": "GEMINI_", "extra": "allow"}


class ADKConfig(BaseSettings):
    """Configuration for Google ADK integration."""
    
    # Session service configuration
    session_service_type: str = Field(default="InMemorySessionService", description="Session service implementation")
    session_timeout_minutes: int = Field(default=30, ge=1, le=1440, description="Session timeout")
    max_concurrent_sessions: int = Field(default=50, ge=1, le=1000, description="Maximum concurrent sessions")
    
    # Agent configuration
    agent_timeout_seconds: int = Field(default=300, ge=30, le=1800, description="Agent execution timeout")
    max_agent_retries: int = Field(default=2, ge=0, le=5, description="Agent retry attempts")
    
    # Workflow configuration
    workflow_timeout_seconds: int = Field(default=1200, ge=300, le=3600, description="Workflow timeout")
    enable_parallel_execution: bool = Field(default=False, description="Enable parallel agent execution")
    
    # Model Garden configuration
    enable_model_garden: bool = Field(default=True, description="Enable Model Garden integration")
    model_garden_project_id: Optional[str] = Field(default=None, env="GOOGLE_CLOUD_PROJECT_ID")
    
    model_config = {"env_prefix": "ADK_", "extra": "allow"}


class SecurityConfig(BaseSettings):
    """Security configuration for the application."""
    
    # API security
    api_key_required: bool = Field(default=True, description="Require API key authentication")
    api_keys: List[str] = Field(default_factory=list, env="API_KEYS", description="Valid API keys")
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"], description="CORS origins")
    
    # Input validation
    max_file_size_mb: int = Field(default=10, ge=1, le=100, description="Maximum file size")
    max_files_per_request: int = Field(default=50, ge=1, le=500, description="Maximum files per request")
    max_content_length_chars: int = Field(default=1000000, ge=1000, description="Maximum content length")
    
    # Rate limiting
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    requests_per_minute: int = Field(default=100, ge=1, le=10000, description="Requests per minute limit")
    
    # Content scanning
    scan_for_secrets: bool = Field(default=True, description="Scan for API keys/secrets")
    scan_for_malicious_patterns: bool = Field(default=True, description="Scan for malicious code patterns")
    
    model_config = {"env_prefix": "SECURITY_", "extra": "allow"}

    @field_validator('api_keys', mode='before')
    @classmethod
    def parse_api_keys(cls, v):
        """Parse comma-separated API keys from environment."""
        if isinstance(v, str):
            return [key.strip() for key in v.split(',') if key.strip()]
        return v


class DatabaseConfig(BaseSettings):
    """Database configuration (future extension)."""
    
    # SQLite configuration for local storage
    database_url: str = Field(default="sqlite:///./data/agentic_review.db", description="Database URL")
    enable_migrations: bool = Field(default=True, description="Enable database migrations")
    connection_pool_size: int = Field(default=5, ge=1, le=20, description="Connection pool size")
    
    model_config = {"env_prefix": "DATABASE_", "extra": "allow"}


class MonitoringConfig(BaseSettings):
    """Monitoring and observability configuration."""
    
    # Structured logging
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Application log level")
    log_format: str = Field(default="json", description="Log format (json/text)")
    enable_correlation_ids: bool = Field(default=True, description="Enable correlation ID tracking")
    
    # Performance monitoring
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, ge=1024, le=65535, description="Metrics server port")
    
    # Health checks
    health_check_interval_seconds: int = Field(default=30, ge=5, le=300, description="Health check interval")
    enable_detailed_health_checks: bool = Field(default=True, description="Enable detailed health status")
    
    # Alerting thresholds
    error_rate_threshold_percent: float = Field(default=5.0, ge=0.1, le=50.0, description="Error rate alert threshold")
    response_time_threshold_ms: float = Field(default=500.0, ge=10.0, le=10000.0, description="Response time threshold")
    memory_usage_threshold_percent: float = Field(default=80.0, ge=10.0, le=95.0, description="Memory usage threshold")
    
    model_config = {"env_prefix": "MONITORING_", "extra": "allow"}


class AppConfig(BaseSettings):
    """Main application configuration."""
    
    # Application metadata
    app_name: str = Field(default="ADK Multi-Agent Code Review", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Runtime environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1024, le=65535, description="Server port")
    workers: int = Field(default=1, ge=1, le=16, description="Number of worker processes")
    
    # Path configuration
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent, description="Base directory")
    config_dir: Optional[Path] = Field(default=None, description="Configuration directory")
    data_dir: Optional[Path] = Field(default=None, description="Data directory")
    logs_dir: Optional[Path] = Field(default=None, description="Logs directory")
    
    # Component configurations
    gemini: GeminiModelConfig = Field(default_factory=GeminiModelConfig)
    adk: ADKConfig = Field(default_factory=ADKConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow"
    }

    @model_validator(mode='before')
    @classmethod
    def set_default_paths(cls, values):
        """Set default paths based on base directory."""
        if isinstance(values, dict):
            base_dir = values.get('base_dir')
            if base_dir:
                base_path = Path(base_dir) if not isinstance(base_dir, Path) else base_dir
                if not values.get('config_dir'):
                    values['config_dir'] = str(base_path / "config")
                if not values.get('data_dir'):
                    values['data_dir'] = str(base_path / "data")
                if not values.get('logs_dir'):
                    values['logs_dir'] = str(base_path / "logs")
        return values

    @field_validator('environment', mode='before')
    @classmethod
    def validate_environment(cls, v):
        """Validate and parse environment value."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v

    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.config_dir or (self.base_dir / "config"),
            self.data_dir or (self.base_dir / "data"), 
            self.logs_dir or (self.base_dir / "logs")
        ]
        for directory in directories:
            if directory:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info("directory_ensured", path=str(directory))

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT

    def get_log_config(self) -> Dict:
        """Get logging configuration dictionary."""
        # Ensure logs directory exists
        logs_dir = self.logs_dir or (self.base_dir / "logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                },
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "level": self.monitoring.log_level.value,
                    "formatter": self.monitoring.log_format,
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "level": self.monitoring.log_level.value,
                    "formatter": "json",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": str(logs_dir / "app.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default", "file"],
                    "level": self.monitoring.log_level.value,
                    "propagate": False,
                }
            },
        }


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = AppConfig()
        _config.create_directories()
        logger.info(
            "configuration_loaded",
            environment=_config.environment.value,
            debug=_config.debug,
            app_version=_config.app_version
        )
    return _config


def reload_config() -> AppConfig:
    """Reload the configuration from environment variables."""
    global _config
    _config = None
    return get_config()


def validate_config() -> bool:
    """Validate the current configuration."""
    try:
        config = get_config()
        
        # Validate critical settings
        if not config.gemini.api_key:
            logger.error("configuration_error", error="GEMINI_API_KEY is required")
            return False
            
        if config.security.api_key_required and not config.security.api_keys:
            logger.error("configuration_error", error="API_KEYS is required when authentication is enabled")
            return False
            
        # Validate paths exist
        if not config.base_dir.exists():
            logger.error("configuration_error", error=f"Base directory does not exist: {config.base_dir}")
            return False
            
        logger.info("configuration_validated", environment=config.environment.value)
        return True
        
    except Exception as e:
        logger.error("configuration_validation_failed", error=str(e))
        return False


# Export commonly used configurations
__all__ = [
    "AppConfig",
    "GeminiModelConfig", 
    "ADKConfig",
    "SecurityConfig",
    "DatabaseConfig",
    "MonitoringConfig",
    "Environment",
    "LogLevel",
    "get_config",
    "get_settings",  # Alias for get_config for FastAPI compatibility
    "reload_config",
    "validate_config",
]

# Alias for FastAPI compatibility
get_settings = get_config
