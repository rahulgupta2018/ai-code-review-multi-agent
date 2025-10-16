"""
Common utilities and shared components for AI Code Review Multi-Agent System.

This package provides:
- Base exception classes
- Common type definitions  
- Shared utility functions
- Infrastructure components used across all domain modules
"""

# Base exceptions
from .exceptions import (
    ADKCodeReviewError,
    ADKError,
    ConfigurationError,
    ValidationError,
    SecurityError
)

# Common types
from .types import (
    CorrelationID,
    SessionID,
    AgentID,
    WorkflowID,
    RequestID,
    Timestamp,
    FilePath,
    JSONType,
    ConfigDict,
    Status,
    CallbackFunction,
    AsyncCallbackFunction,
    Result,
    Identifiable,
    Timestamped,
    BaseResponse,
    BaseEvent
)

# Utility functions
from .utils import (
    generate_correlation_id,
    generate_session_id,
    current_timestamp,
    safe_json_dumps,
    safe_json_loads,
    hash_string,
    hash_file,
    sanitize_filename,
    deep_merge,
    get_file_extension,
    ensure_directory
)

__all__ = [
    # Exceptions
    "ADKCodeReviewError",
    "ADKError", 
    "ConfigurationError",
    "ValidationError",
    "SecurityError",
    
    # Types
    "CorrelationID",
    "SessionID",
    "AgentID",
    "WorkflowID", 
    "RequestID",
    "Timestamp",
    "FilePath",
    "JSONType",
    "ConfigDict",
    "Status",
    "CallbackFunction",
    "AsyncCallbackFunction",
    "Result",
    "Identifiable",
    "Timestamped",
    "BaseResponse",
    "BaseEvent",
    
    # Utilities
    "generate_correlation_id",
    "generate_session_id",
    "current_timestamp",
    "safe_json_dumps",
    "safe_json_loads",
    "hash_string",
    "hash_file",
    "sanitize_filename",
    "deep_merge",
    "get_file_extension",
    "ensure_directory"
]