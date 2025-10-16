"""
Exception definitions for LLM (Large Language Model) components.

This module provides exception classes specific to LLM operations,
inheriting from the base exception classes in common.
"""

from typing import Optional, Dict, Any

from ..common import ADKCodeReviewError


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