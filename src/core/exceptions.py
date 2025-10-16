"""
Custom exception hierarchy for ADK Multi-Agent Code Review MVP.

This module defines a comprehensive exception hierarchy for different error types
with proper error context preservation and structured logging integration.
"""

from typing import Any, Dict, Optional, List
import structlog

logger = structlog.get_logger(__name__)


class ADKCodeReviewError(Exception):
    """Base exception for all ADK Code Review errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.correlation_id = correlation_id
        
        super().__init__(message)
        
        # Log the exception creation
        logger.error(
            "exception_created",
            error_type=self.__class__.__name__,
            error_code=self.error_code,
            message=self.message,
            details=self.details,
            correlation_id=self.correlation_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "correlation_id": self.correlation_id
        }


# Configuration Errors
class ConfigurationError(ADKCodeReviewError):
    """Raised when there are configuration issues."""
    pass


class ValidationError(ADKCodeReviewError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field_errors: Optional[List[Dict[str, Any]]] = None, **kwargs):
        self.field_errors = field_errors or []
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include field errors in dictionary representation."""
        result = super().to_dict()
        result["field_errors"] = self.field_errors
        return result


class SecurityError(ADKCodeReviewError):
    """Raised when security violations are detected."""
    pass


# LLM Integration Errors
class LLMError(ADKCodeReviewError):
    """Base exception for LLM-related errors."""
    pass


class LLMAPIError(LLMError):
    """Raised when LLM API calls fail."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        self.status_code = status_code
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include status code in dictionary representation."""
        result = super().to_dict()
        result["status_code"] = self.status_code
        return result


class LLMTimeoutError(LLMError):
    """Raised when LLM API calls timeout."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM API rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        self.retry_after = retry_after
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include retry information in dictionary representation."""
        result = super().to_dict()
        result["retry_after"] = self.retry_after
        return result


class LLMResponseParsingError(LLMError):
    """Raised when LLM responses cannot be parsed."""
    
    def __init__(self, message: str, raw_response: Optional[str] = None, **kwargs):
        self.raw_response = raw_response
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include raw response (truncated) in dictionary representation."""
        result = super().to_dict()
        if self.raw_response:
            # Truncate long responses for logging
            truncated_response = self.raw_response[:500] + "..." if len(self.raw_response) > 500 else self.raw_response
            result["raw_response_preview"] = truncated_response
        return result


# ADK Framework Errors
class ADKError(ADKCodeReviewError):
    """Base exception for ADK framework errors."""
    pass


class AgentError(ADKError):
    """Raised when agent execution fails."""
    
    def __init__(self, message: str, agent_name: Optional[str] = None, **kwargs):
        self.agent_name = agent_name
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include agent name in dictionary representation."""
        result = super().to_dict()
        result["agent_name"] = self.agent_name
        return result


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""
    pass


class WorkflowError(ADKError):
    """Raised when workflow execution fails."""
    
    def __init__(self, message: str, workflow_name: Optional[str] = None, step: Optional[str] = None, **kwargs):
        self.workflow_name = workflow_name
        self.step = step
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include workflow details in dictionary representation."""
        result = super().to_dict()
        result["workflow_name"] = self.workflow_name
        result["step"] = self.step
        return result


class SessionError(ADKError):
    """Raised when session management fails."""
    
    def __init__(self, message: str, session_id: Optional[str] = None, **kwargs):
        self.session_id = session_id
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include session ID in dictionary representation."""
        result = super().to_dict()
        result["session_id"] = self.session_id
        return result


class FunctionToolError(ADKError):
    """Raised when ADK FunctionTool execution fails."""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, **kwargs):
        self.tool_name = tool_name
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include tool name in dictionary representation."""
        result = super().to_dict()
        result["tool_name"] = self.tool_name
        return result


# Analysis Errors
class AnalysisError(ADKCodeReviewError):
    """Base exception for code analysis errors."""
    pass


class CodeParsingError(AnalysisError):
    """Raised when code parsing fails."""
    
    def __init__(self, message: str, filename: Optional[str] = None, line_number: Optional[int] = None, **kwargs):
        self.filename = filename
        self.line_number = line_number
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include parsing details in dictionary representation."""
        result = super().to_dict()
        result["filename"] = self.filename
        result["line_number"] = self.line_number
        return result


class TreeSitterError(AnalysisError):
    """Raised when Tree-sitter parsing fails."""
    
    def __init__(self, message: str, language: Optional[str] = None, **kwargs):
        self.language = language
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include language in dictionary representation."""
        result = super().to_dict()
        result["language"] = self.language
        return result


class ComplexityAnalysisError(AnalysisError):
    """Raised when complexity analysis fails."""
    pass


class SecurityAnalysisError(AnalysisError):
    """Raised when security analysis fails."""
    pass


class EngineeringPracticesAnalysisError(AnalysisError):
    """Raised when engineering practices analysis fails."""
    pass


# API Errors
class APIError(ADKCodeReviewError):
    """Base exception for API errors."""
    pass


class AuthenticationError(APIError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(APIError):
    """Raised when authorization fails."""
    pass


class RateLimitExceededError(APIError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, message: str, limit: Optional[int] = None, window_seconds: Optional[int] = None, **kwargs):
        self.limit = limit
        self.window_seconds = window_seconds
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include rate limit details in dictionary representation."""
        result = super().to_dict()
        result["limit"] = self.limit
        result["window_seconds"] = self.window_seconds
        return result


class RequestTooLargeError(APIError):
    """Raised when request payload is too large."""
    
    def __init__(self, message: str, size_bytes: Optional[int] = None, max_size_bytes: Optional[int] = None, **kwargs):
        self.size_bytes = size_bytes
        self.max_size_bytes = max_size_bytes
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include size details in dictionary representation."""
        result = super().to_dict()
        result["size_bytes"] = self.size_bytes
        result["max_size_bytes"] = self.max_size_bytes
        return result


# Resource Errors
class ResourceError(ADKCodeReviewError):
    """Base exception for resource-related errors."""
    pass


class MemoryError(ResourceError):
    """Raised when memory limits are exceeded."""
    pass


class DiskSpaceError(ResourceError):
    """Raised when disk space is insufficient."""
    pass


class NetworkError(ResourceError):
    """Raised when network operations fail."""
    pass


# Utility Functions
def handle_exception(
    exc: Exception,
    context: Dict[str, Any],
    correlation_id: Optional[str] = None,
    reraise: bool = True
) -> Optional[ADKCodeReviewError]:
    """
    Handle and convert exceptions to ADK Code Review exceptions.
    
    Args:
        exc: The original exception
        context: Additional context information
        correlation_id: Request correlation ID
        reraise: Whether to re-raise the exception
        
    Returns:
        The wrapped exception if not re-raising
    """
    # Convert common exceptions to our hierarchy
    if isinstance(exc, ValueError):
        wrapped_exc = ValidationError(
            message=str(exc),
            details=context,
            correlation_id=correlation_id
        )
    elif isinstance(exc, PermissionError):
        wrapped_exc = AuthorizationError(
            message=str(exc),
            details=context,
            correlation_id=correlation_id
        )
    elif isinstance(exc, TimeoutError):
        wrapped_exc = LLMTimeoutError(
            message=str(exc),
            details=context,
            correlation_id=correlation_id
        )
    elif isinstance(exc, ConnectionError):
        wrapped_exc = NetworkError(
            message=str(exc),
            details=context,
            correlation_id=correlation_id
        )
    elif isinstance(exc, ADKCodeReviewError):
        # Already our exception type
        wrapped_exc = exc
    else:
        # Generic wrapper for unknown exceptions
        wrapped_exc = ADKCodeReviewError(
            message=f"Unexpected error: {str(exc)}",
            error_code="UNKNOWN_ERROR",
            details={**context, "original_exception_type": exc.__class__.__name__},
            correlation_id=correlation_id
        )
    
    logger.error(
        "exception_handled",
        original_type=exc.__class__.__name__,
        wrapped_type=wrapped_exc.__class__.__name__,
        message=wrapped_exc.message,
        context=context,
        correlation_id=correlation_id
    )
    
    if reraise:
        raise wrapped_exc
    
    return wrapped_exc


def create_error_response(exc: ADKCodeReviewError, include_details: bool = False) -> Dict[str, Any]:
    """
    Create a standardized error response dictionary.
    
    Args:
        exc: The exception to convert
        include_details: Whether to include detailed error information
        
    Returns:
        Standardized error response dictionary
    """
    response = {
        "success": False,
        "error": {
            "type": exc.__class__.__name__,
            "code": exc.error_code,
            "message": exc.message,
        }
    }
    
    if include_details and exc.details:
        response["error"]["details"] = exc.details
    
    if exc.correlation_id:
        response["correlation_id"] = exc.correlation_id
    
    return response


# Export all exception classes and utilities
__all__ = [
    # Base exceptions
    "ADKCodeReviewError",
    "ConfigurationError",
    "ValidationError", 
    "SecurityError",
    
    # LLM exceptions
    "LLMError",
    "LLMAPIError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "LLMResponseParsingError",
    
    # ADK exceptions
    "ADKError",
    "AgentError",
    "AgentTimeoutError",
    "WorkflowError",
    "SessionError",
    "FunctionToolError",
    
    # Analysis exceptions
    "AnalysisError",
    "CodeParsingError",
    "TreeSitterError",
    "ComplexityAnalysisError",
    "SecurityAnalysisError",
    "EngineeringPracticesAnalysisError",
    
    # API exceptions
    "APIError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitExceededError",
    "RequestTooLargeError",
    
    # Resource exceptions
    "ResourceError",
    "MemoryError",
    "DiskSpaceError",
    "NetworkError",
    
    # Utility functions
    "handle_exception",
    "create_error_response",
]
