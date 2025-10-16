"""
Common type definitions for AI Code Review Multi-Agent System.

This module provides fundamental type definitions that are used across all domain modules.
Domain-specific types should be defined in their respective modules.
"""

from typing import (
    Any, Dict, List, Optional, Union, Tuple, Callable, Awaitable,
    TypeVar, Generic, Protocol, runtime_checkable
)
from datetime import datetime
from pathlib import Path

# Basic type aliases (truly shared across all domains)
CorrelationID = str
SessionID = str
AgentID = str
WorkflowID = str
RequestID = str
Timestamp = datetime
FilePath = Union[str, Path]
JSONType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]

# Generic type variables
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

# Configuration dictionary type (used by config modules)
ConfigDict = Dict[str, Any]

# Status type (used across domains)
Status = str

# Generic callback type
CallbackFunction = Callable[..., Any]
AsyncCallbackFunction = Callable[..., Awaitable[Any]]

# Generic result type
Result = Union[T, Exception]


@runtime_checkable
class Identifiable(Protocol):
    """Protocol for objects that have an ID."""
    id: str


@runtime_checkable
class Timestamped(Protocol):
    """Protocol for objects that have timestamps."""
    created_at: datetime
    updated_at: Optional[datetime]


# Base data structure for API responses
class BaseResponse(Dict[str, Any]):
    """Base response structure for API endpoints."""
    pass


# Base event type for system events
class BaseEvent(Dict[str, Any]):
    """Base event structure for system events."""
    pass