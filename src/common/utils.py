"""
Common utility functions for AI Code Review Multi-Agent System.

This module provides utility functions that are used across all domain modules.
Domain-specific utilities should be defined in their respective modules.
"""

import uuid
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from .types import CorrelationID, JSONType


def generate_correlation_id() -> CorrelationID:
    """Generate a unique correlation ID for tracking requests."""
    return str(uuid.uuid4())


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())


def current_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.utcnow()


def safe_json_dumps(obj: Any, indent: Optional[int] = None) -> str:
    """Safely serialize object to JSON string."""
    try:
        return json.dumps(obj, indent=indent, default=str)
    except (TypeError, ValueError) as e:
        return f"{{\"error\": \"JSON serialization failed: {str(e)}\"}}"


def safe_json_loads(data: str) -> Optional[JSONType]:
    """Safely deserialize JSON string to object."""
    try:
        return json.loads(data)
    except (TypeError, ValueError):
        return None


def hash_string(text: str) -> str:
    """Generate SHA-256 hash of a string."""
    return hashlib.sha256(text.encode()).hexdigest()


def hash_file(file_path: Path) -> str:
    """Generate SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem operations."""
    import re
    # Replace any character that's not alphanumeric, dot, dash, or underscore
    return re.sub(r'[^a-zA-Z0-9._-]', '_', filename)


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def get_file_extension(file_path: Path) -> str:
    """Get file extension from path."""
    return file_path.suffix.lower().lstrip('.')


def ensure_directory(directory: Path) -> None:
    """Ensure directory exists, create if it doesn't."""
    directory.mkdir(parents=True, exist_ok=True)