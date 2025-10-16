"""
Type definitions for API components.

This module provides type definitions specific to API operations,
including request/response types, error handling, and metrics.
"""

from typing import Any, Dict, Optional, List, TypedDict
from enum import Enum

from ..common import CorrelationID, Timestamp, JSONType


class HTTPMethod(Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class APIRequest(TypedDict):
    """API request data."""
    method: str
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, str]
    body: Optional[JSONType]
    correlation_id: CorrelationID
    timestamp: Timestamp


class APIResponse(TypedDict):
    """API response data."""
    status_code: int
    headers: Dict[str, str]
    body: JSONType
    correlation_id: CorrelationID
    execution_time_seconds: float
    timestamp: Timestamp


class ErrorResponse(TypedDict):
    """Error response format."""
    success: bool
    error: Dict[str, Any]
    correlation_id: CorrelationID
    timestamp: Timestamp


class SuccessResponse(TypedDict):
    """Success response format."""
    success: bool
    data: JSONType
    correlation_id: CorrelationID
    timestamp: Timestamp


class PaginatedResponse(TypedDict):
    """Paginated response format."""
    success: bool
    data: List[JSONType]
    pagination: Dict[str, Any]
    correlation_id: CorrelationID
    timestamp: Timestamp


class ValidationErrorDetail(TypedDict):
    """Validation error detail."""
    field: str
    message: str
    invalid_value: Optional[Any]


class APIMetrics(TypedDict):
    """API performance metrics."""
    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    last_request: Optional[Timestamp]


class RateLimitInfo(TypedDict):
    """Rate limiting information."""
    limit: int
    remaining: int
    reset_time: Timestamp
    window_seconds: int


class RequestContext(TypedDict):
    """Request context information."""
    correlation_id: CorrelationID
    user_id: Optional[str]
    client_ip: str
    user_agent: str
    timestamp: Timestamp
    rate_limit_info: Optional[RateLimitInfo]