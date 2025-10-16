"""
Centralized structured logging for ADK Multi-Agent Code Review MVP.

This module provides structured JSON logging with correlation IDs, performance
monitoring, and comprehensive observability for production systems.
"""

import json
import logging
import logging.config
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional, Union
from pathlib import Path

import structlog
from pythonjsonlogger import jsonlogger

from ..core.config import get_config
from ..core.constants import CORRELATION_ID_HEADER, REQUEST_ID_HEADER

# Context variables for tracking request-specific data
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


class CorrelationIDProcessor:
    """Structlog processor to inject correlation ID into log records."""
    
    def __call__(self, logger, method_name, event_dict):
        """Add correlation and request IDs to log events."""
        correlation_id = correlation_id_var.get()
        request_id = request_id_var.get()
        session_id = session_id_var.get()
        
        if correlation_id:
            event_dict['correlation_id'] = correlation_id
        if request_id:
            event_dict['request_id'] = request_id
        if session_id:
            event_dict['session_id'] = session_id
            
        return event_dict


class TimestampProcessor:
    """Structlog processor to add timestamps."""
    
    def __call__(self, logger, method_name, event_dict):
        """Add timestamp to log events."""
        event_dict['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        return event_dict


class SanitizationProcessor:
    """Structlog processor to sanitize sensitive data from logs."""
    
    SENSITIVE_KEYS = {
        'password', 'token', 'api_key', 'secret', 'authorization',
        'cookie', 'session', 'private_key', 'access_key', 'refresh_token'
    }
    
    def __call__(self, logger, method_name, event_dict):
        """Sanitize sensitive information from log events."""
        return self._sanitize_dict(event_dict)
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary data."""
        sanitized = {}
        for key, value in data.items():
            if isinstance(key, str) and any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value
        return sanitized


class PerformanceProcessor:
    """Structlog processor to add performance metadata."""
    
    def __call__(self, logger, method_name, event_dict):
        """Add performance metadata to log events."""
        event_dict['level'] = method_name.upper()
        event_dict['logger_name'] = logger.name
        return event_dict


class CustomJSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to log records."""
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add process/thread info
        log_record['process_id'] = record.process
        log_record['thread_id'] = record.thread
        
        # Ensure timestamp is present
        if 'timestamp' not in log_record:
            log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'


def configure_logging() -> None:
    """Configure application logging with structured JSON output."""
    config = get_config()
    
    # Create logs directory if it doesn't exist
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure standard logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": CustomJSONFormatter,
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": config.monitoring.log_level.value,
                "formatter": "json" if config.monitoring.log_format == "json" else "standard",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": config.monitoring.log_level.value,
                "formatter": "json",
                "filename": str(config.logs_dir / "app.log"),
                "maxBytes": 50 * 1024 * 1024,  # 50MB
                "backupCount": 10
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": str(config.logs_dir / "error.log"),
                "maxBytes": 50 * 1024 * 1024,  # 50MB
                "backupCount": 5
            }
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": config.monitoring.log_level.value,
                "propagate": False
            },
            "adk_code_review": {
                "handlers": ["console", "file", "error_file"],
                "level": config.monitoring.log_level.value,
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        TimestampProcessor(),
        CorrelationIDProcessor(),
        SanitizationProcessor(),
        PerformanceProcessor(),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if config.monitoring.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (defaults to calling module)
        
    Returns:
        Configured structlog logger instance
    """
    if name is None:
        # Get the caller's module name
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get('__name__', 'unknown')
    
    return structlog.get_logger(name)


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get correlation ID from current context."""
    return correlation_id_var.get()


def set_request_id(request_id: str) -> None:
    """Set request ID for current context."""
    request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    """Get request ID from current context."""
    return request_id_var.get()


def set_session_id(session_id: str) -> None:
    """Set session ID for current context."""
    session_id_var.set(session_id)


def get_session_id() -> Optional[str]:
    """Get session ID from current context."""
    return session_id_var.get()


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def generate_request_id() -> str:
    """Generate a new request ID."""
    return str(uuid.uuid4())


class LoggingContextManager:
    """Context manager for setting logging context."""
    
    def __init__(
        self,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **extra_context
    ):
        self.correlation_id = correlation_id or generate_correlation_id()
        self.request_id = request_id or generate_request_id()
        self.session_id = session_id
        self.extra_context = extra_context
        
        # Store previous values for restoration
        self.prev_correlation_id = None
        self.prev_request_id = None
        self.prev_session_id = None
    
    def __enter__(self):
        """Enter logging context."""
        # Store previous values
        self.prev_correlation_id = correlation_id_var.get()
        self.prev_request_id = request_id_var.get()
        self.prev_session_id = session_id_var.get()
        
        # Set new values
        correlation_id_var.set(self.correlation_id)
        request_id_var.set(self.request_id)
        if self.session_id:
            session_id_var.set(self.session_id)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit logging context."""
        # Restore previous values
        correlation_id_var.set(self.prev_correlation_id)
        request_id_var.set(self.prev_request_id)
        session_id_var.set(self.prev_session_id)


def with_logging_context(
    correlation_id: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **extra_context
):
    """Decorator to set logging context for a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with LoggingContextManager(
                correlation_id=correlation_id,
                request_id=request_id,
                session_id=session_id,
                **extra_context
            ):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def log_function_call(
    logger: Optional[structlog.BoundLogger] = None,
    log_args: bool = False,
    log_result: bool = False,
    log_duration: bool = True
):
    """Decorator to log function calls with performance metrics."""
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        def wrapper(*args, **kwargs):
            import time
            
            func_name = func.__name__
            start_time = time.time()
            
            log_data = {
                "function": func_name,
                "event": "function_call_started"
            }
            
            if log_args:
                log_data["args"] = args
                log_data["kwargs"] = kwargs
            
            logger.info(**log_data)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                success_data = {
                    "function": func_name,
                    "event": "function_call_completed",
                }
                
                if log_duration:
                    success_data["duration_seconds"] = duration
                
                if log_result:
                    success_data["result"] = result
                
                logger.info(**success_data)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "function_call_failed",
                    function=func_name,
                    duration_seconds=duration,
                    error=str(e),
                    error_type=e.__class__.__name__
                )
                raise
        
        return wrapper
    return decorator


# Performance logging utilities
def log_performance_metrics(
    operation: str,
    duration_seconds: float,
    metadata: Optional[Dict[str, Any]] = None,
    logger: Optional[structlog.BoundLogger] = None
) -> None:
    """Log performance metrics for an operation."""
    if logger is None:
        logger = get_logger("performance")
    
    log_data = {
        "event": "performance_metrics",
        "operation": operation,
        "duration_seconds": duration_seconds,
        "duration_ms": duration_seconds * 1000
    }
    
    if metadata:
        log_data.update(metadata)
    
    logger.info(**log_data)


def log_memory_usage(
    operation: str,
    memory_mb: float,
    metadata: Optional[Dict[str, Any]] = None,
    logger: Optional[structlog.BoundLogger] = None
) -> None:
    """Log memory usage for an operation."""
    if logger is None:
        logger = get_logger("memory")
    
    log_data = {
        "event": "memory_usage",
        "operation": operation,
        "memory_mb": memory_mb
    }
    
    if metadata:
        log_data.update(metadata)
    
    logger.info(**log_data)


def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
    request_size_bytes: Optional[int] = None,
    response_size_bytes: Optional[int] = None,
    logger: Optional[structlog.BoundLogger] = None
) -> None:
    """Log API request metrics."""
    if logger is None:
        logger = get_logger("api")
    
    log_data = {
        "event": "api_request",
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_seconds": duration_seconds,
        "duration_ms": duration_seconds * 1000
    }
    
    if request_size_bytes is not None:
        log_data["request_size_bytes"] = request_size_bytes
    if response_size_bytes is not None:
        log_data["response_size_bytes"] = response_size_bytes
    
    # Log level based on status code
    if status_code >= 500:
        logger.error(**log_data)
    elif status_code >= 400:
        logger.warning(**log_data)
    else:
        logger.info(**log_data)


# Initialize logging on module import
try:
    configure_logging()
    _logger = get_logger(__name__)
    _logger.info("logging_configured", module=__name__)
except Exception as e:
    # Fallback to basic logging if configuration fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    logging.error(f"Failed to configure structured logging: {e}")


# Export public interface
__all__ = [
    "configure_logging",
    "get_logger",
    "set_correlation_id",
    "get_correlation_id",
    "set_request_id", 
    "get_request_id",
    "set_session_id",
    "get_session_id",
    "generate_correlation_id",
    "generate_request_id",
    "LoggingContextManager",
    "with_logging_context",
    "log_function_call",
    "log_performance_metrics",
    "log_memory_usage",
    "log_api_request",
]
