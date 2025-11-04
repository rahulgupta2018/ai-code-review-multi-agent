"""
Common utility functions for AI Code Review Multi-Agent System.

This module provides basic utility functions that are used across all domain modules.
Domain-specific utilities should be in their specialized utility modules.
"""

import uuid
import json
import hashlib
import time
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional, List, Callable, Awaitable
from pathlib import Path
import logging

from .types import CorrelationID, JSONType

logger = logging.getLogger(__name__)


# ==============================================================================
# ID GENERATION UTILITIES
# ==============================================================================

def generate_correlation_id() -> CorrelationID:
    """Generate a unique correlation ID for tracking requests."""
    return str(uuid.uuid4())


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())


def generate_agent_id(agent_type: str, prefix: str = "agent") -> str:
    """Generate a unique agent ID."""
    return f"{prefix}_{agent_type}_{uuid.uuid4().hex[:8]}"


def generate_workflow_id(prefix: str = "workflow") -> str:
    """Generate a unique workflow ID."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}_{int(time.time())}"


# ==============================================================================
# TIME UTILITIES
# ==============================================================================

def current_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.utcnow()


def timestamp_to_string(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S UTC") -> str:
    """Convert timestamp to formatted string."""
    return timestamp.strftime(format_str)


def string_to_timestamp(timestamp_str: str, format_str: str = "%Y-%m-%d %H:%M:%S UTC") -> Optional[datetime]:
    """Convert formatted string to timestamp."""
    try:
        return datetime.strptime(timestamp_str, format_str)
    except ValueError:
        return None


def time_ago(timestamp: datetime) -> str:
    """Get human-readable time difference."""
    now = current_timestamp()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hours ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minutes ago"
    else:
        return "just now"


# ==============================================================================
# JSON UTILITIES
# ==============================================================================

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


def prettify_json(obj: Any) -> str:
    """Pretty-print JSON with indentation."""
    return safe_json_dumps(obj, indent=2)


# ==============================================================================
# HASHING UTILITIES
# ==============================================================================

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


def hash_dict(data: Dict[str, Any]) -> str:
    """Generate consistent hash of a dictionary."""
    # Sort keys to ensure consistent hashing
    sorted_json = json.dumps(data, sort_keys=True, default=str)
    return hash_string(sorted_json)


# ==============================================================================
# FILE SYSTEM UTILITIES
# ==============================================================================

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem operations."""
    import re
    # Replace any character that's not alphanumeric, dot, dash, or underscore
    return re.sub(r'[^a-zA-Z0-9._-]', '_', filename)


def get_file_extension(file_path: Path) -> str:
    """Get file extension from path."""
    return file_path.suffix.lower().lstrip('.')


def ensure_directory(directory: Path) -> None:
    """Ensure directory exists, create if it doesn't."""
    directory.mkdir(parents=True, exist_ok=True)


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return file_path.stat().st_size if file_path.exists() else 0


def is_file_readable(file_path: Path) -> bool:
    """Check if file exists and is readable."""
    return file_path.exists() and file_path.is_file() and file_path.stat().st_size > 0


# ==============================================================================
# DICTIONARY UTILITIES
# ==============================================================================

def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """Flatten nested dictionary using separator."""
    def _flatten(obj: Any, parent_key: str = "") -> Dict[str, Any]:
        items = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{parent_key}{separator}{key}" if parent_key else key
                items.extend(_flatten(value, new_key).items())
        else:
            return {parent_key: obj}
        return dict(items)
    
    return _flatten(data)


def filter_dict(data: Dict[str, Any], allowed_keys: List[str]) -> Dict[str, Any]:
    """Filter dictionary to only include allowed keys."""
    return {k: v for k, v in data.items() if k in allowed_keys}


def remove_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove keys with None values from dictionary."""
    return {k: v for k, v in data.items() if v is not None}


# ==============================================================================
# VALIDATION UTILITIES
# ==============================================================================

def is_valid_uuid(uuid_string: str) -> bool:
    """Check if string is a valid UUID."""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def is_valid_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_json(json_string: str) -> bool:
    """Check if string is valid JSON."""
    try:
        json.loads(json_string)
        return True
    except (TypeError, ValueError):
        return False


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate that required fields are present in data."""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    return missing_fields


# ==============================================================================
# ASYNC UTILITIES
# ==============================================================================

async def run_with_timeout(coro: Awaitable[Any], timeout_seconds: float) -> Any:
    """Run coroutine with timeout."""
    return await asyncio.wait_for(coro, timeout=timeout_seconds)


async def gather_with_concurrency(tasks: List[Awaitable[Any]], max_concurrency: int = 10) -> List[Any]:
    """Run tasks with limited concurrency."""
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def run_task(task: Awaitable[Any]) -> Any:
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[run_task(task) for task in tasks])


# ==============================================================================
# STRING UTILITIES
# ==============================================================================

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text."""
    import re
    return re.sub(r'\s+', ' ', text.strip())


def camel_to_snake(camel_str: str) -> str:
    """Convert CamelCase to snake_case."""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(snake_str: str) -> str:
    """Convert snake_case to CamelCase."""
    components = snake_str.split('_')
    return ''.join(word.capitalize() for word in components)


# ==============================================================================
# ERROR HANDLING UTILITIES
# ==============================================================================

def safe_execute(func: Callable, default_value: Any = None, log_errors: bool = True) -> Any:
    """Safely execute function with error handling."""
    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.error(f"Error in safe_execute: {e}")
        return default_value


async def safe_async_execute(coro: Awaitable[Any], default_value: Any = None, log_errors: bool = True) -> Any:
    """Safely execute coroutine with error handling."""
    try:
        return await coro
    except Exception as e:
        if log_errors:
            logger.error(f"Error in safe_async_execute: {e}")
        return default_value


def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0
) -> Callable:
    """Decorator for retry with exponential backoff."""
    def wrapper(*args, **kwargs):
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == max_attempts - 1:
                    break
                
                delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
        
        logger.error(f"All {max_attempts} attempts failed")
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"All {max_attempts} attempts failed with no recorded exception")
    
    return wrapper