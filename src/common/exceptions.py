"""
Base exception hierarchy for AI Code Review Multi-Agent System.

This module defines base exceptions that are shared across all domain modules.
Domain-specific exceptions inherit from these base classes.
"""

from typing import Any, Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


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


class ADKError(ADKCodeReviewError):
    """Base exception for ADK platform errors."""
    pass