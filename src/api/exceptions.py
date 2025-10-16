"""
Exception definitions for API components.

This module provides exception classes specific to API operations,
inheriting from the base exception classes in common.
"""

from typing import Optional, Dict, Any, List

from ..common import ADKCodeReviewError, ValidationError


class APIError(ADKCodeReviewError):
    """Base exception for API-related errors."""
    
    def __init__(self, message: str, status_code: int = 500, **kwargs):
        self.status_code = status_code
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include status code in dictionary representation."""
        result = super().to_dict()
        result["status_code"] = self.status_code
        return result


class BadRequestError(APIError):
    """Raised when request is malformed (400)."""
    
    def __init__(self, message: str = "Bad Request", **kwargs):
        super().__init__(message, status_code=400, **kwargs)


class UnauthorizedError(APIError):
    """Raised when authentication is required or failed (401)."""
    
    def __init__(self, message: str = "Unauthorized", **kwargs):
        super().__init__(message, status_code=401, **kwargs)


class ForbiddenError(APIError):
    """Raised when access is forbidden (403)."""
    
    def __init__(self, message: str = "Forbidden", **kwargs):
        super().__init__(message, status_code=403, **kwargs)


class NotFoundError(APIError):
    """Raised when resource is not found (404)."""
    
    def __init__(self, message: str = "Not Found", **kwargs):
        super().__init__(message, status_code=404, **kwargs)


class MethodNotAllowedError(APIError):
    """Raised when HTTP method is not allowed (405)."""
    
    def __init__(self, message: str = "Method Not Allowed", **kwargs):
        super().__init__(message, status_code=405, **kwargs)


class ConflictError(APIError):
    """Raised when there's a conflict with current state (409)."""
    
    def __init__(self, message: str = "Conflict", **kwargs):
        super().__init__(message, status_code=409, **kwargs)


class UnprocessableEntityError(APIError):
    """Raised when request is well-formed but semantically incorrect (422)."""
    
    def __init__(self, message: str = "Unprocessable Entity", **kwargs):
        super().__init__(message, status_code=422, **kwargs)


class TooManyRequestsError(APIError):
    """Raised when rate limit is exceeded (429)."""
    
    def __init__(self, message: str = "Too Many Requests", retry_after: Optional[int] = None, **kwargs):
        self.retry_after = retry_after
        super().__init__(message, status_code=429, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include retry_after in dictionary representation."""
        result = super().to_dict()
        result["retry_after"] = self.retry_after
        return result


class InternalServerError(APIError):
    """Raised when there's an internal server error (500)."""
    
    def __init__(self, message: str = "Internal Server Error", **kwargs):
        super().__init__(message, status_code=500, **kwargs)


class BadGatewayError(APIError):
    """Raised when upstream service is unavailable (502)."""
    
    def __init__(self, message: str = "Bad Gateway", **kwargs):
        super().__init__(message, status_code=502, **kwargs)


class ServiceUnavailableError(APIError):
    """Raised when service is temporarily unavailable (503)."""
    
    def __init__(self, message: str = "Service Unavailable", **kwargs):
        super().__init__(message, status_code=503, **kwargs)


class GatewayTimeoutError(APIError):
    """Raised when upstream service times out (504)."""
    
    def __init__(self, message: str = "Gateway Timeout", **kwargs):
        super().__init__(message, status_code=504, **kwargs)


class APIValidationError(ValidationError):
    """Raised when API request validation fails."""
    
    def __init__(self, message: str, field_errors: Optional[List[Dict[str, Any]]] = None, **kwargs):
        super().__init__(message, field_errors=field_errors, **kwargs)
        self.status_code = 422


class APITimeoutError(APIError):
    """Raised when API request times out."""
    
    def __init__(self, message: str = "Request Timeout", **kwargs):
        super().__init__(message, status_code=408, **kwargs)