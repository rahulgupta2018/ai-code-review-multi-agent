"""
Consolidated exception hierarchy for AI Code Review Multi-Agent System.

This module defines all exceptions used across the application,
organized by functional area for better maintainability.
"""

from typing import Any, Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# BASE EXCEPTIONS
# =============================================================================

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
            f"Exception created: {self.__class__.__name__} - {message}",
            extra={
                "error_type": self.__class__.__name__,
                "error_code": self.error_code,
                "details": self.details,
                "correlation_id": self.correlation_id
            }
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


class ADKError(ADKCodeReviewError):
    """Base exception for ADK platform errors."""
    pass


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


# =============================================================================
# AGENT EXCEPTIONS
# =============================================================================

class AgentError(ADKError):
    """Base exception for agent-related errors."""
    
    def __init__(self, message: str, agent_id: Optional[str] = None, **kwargs):
        self.agent_id = agent_id
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include agent_id in dictionary representation."""
        result = super().to_dict()
        result["agent_id"] = self.agent_id
        return result


class AgentConfigurationError(AgentError):
    """Raised when agent configuration is invalid."""
    pass


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""
    pass


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""
    pass


class AgentValidationError(AgentError):
    """Raised when agent input/output validation fails."""
    pass


class WorkflowError(ADKError):
    """Base exception for workflow-related errors."""
    
    def __init__(self, message: str, workflow_id: Optional[str] = None, **kwargs):
        self.workflow_id = workflow_id
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include workflow_id in dictionary representation."""
        result = super().to_dict()
        result["workflow_id"] = self.workflow_id
        return result


class WorkflowConfigurationError(WorkflowError):
    """Raised when workflow configuration is invalid."""
    pass


class WorkflowExecutionError(WorkflowError):
    """Raised when workflow execution fails."""
    pass


class SessionError(ADKError):
    """Base exception for session-related errors."""
    
    def __init__(self, message: str, session_id: Optional[str] = None, **kwargs):
        self.session_id = session_id
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include session_id in dictionary representation."""
        result = super().to_dict()
        result["session_id"] = self.session_id
        return result


class SessionConfigurationError(SessionError):
    """Raised when session configuration is invalid."""
    pass


class SessionExecutionError(SessionError):
    """Raised when session execution fails."""
    pass


class FunctionToolError(ADKError):
    """Base exception for function tool errors."""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, **kwargs):
        self.tool_name = tool_name
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include tool_name in dictionary representation."""
        result = super().to_dict()
        result["tool_name"] = self.tool_name
        return result


class ToolConfigurationError(FunctionToolError):
    """Raised when tool configuration is invalid."""
    pass


class ToolExecutionError(FunctionToolError):
    """Raised when tool execution fails."""
    pass


# =============================================================================
# API EXCEPTIONS
# =============================================================================

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


# =============================================================================
# LLM EXCEPTIONS
# =============================================================================

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
        """Include retry_after in dictionary representation."""
        result = super().to_dict()
        result["retry_after"] = self.retry_after
        return result


class LLMResponseParsingError(LLMError):
    """Raised when LLM response cannot be parsed."""
    
    def __init__(self, message: str, raw_response: Optional[str] = None, **kwargs):
        self.raw_response = raw_response
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include raw response in dictionary representation."""
        result = super().to_dict()
        if self.raw_response:
            # Truncate long responses for logging
            result["raw_response"] = (
                self.raw_response[:500] + "..." 
                if len(self.raw_response) > 500 
                else self.raw_response
            )
        return result


class LLMProviderError(LLMError):
    """Raised when there are issues with LLM provider configuration."""
    pass


class LLMModelError(LLMError):
    """Raised when there are issues with specific models."""
    pass


class LLMAuthenticationError(LLMError):
    """Raised when LLM API authentication fails."""
    pass


class LLMQuotaExceededError(LLMError):
    """Raised when LLM API quota is exceeded."""
    pass