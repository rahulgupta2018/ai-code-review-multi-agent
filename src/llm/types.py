"""
Type definitions for LLM (Large Language Model) components.

This module provides type definitions specific to LLM operations,
including request/response types, model configurations, and provider types.
"""

from typing import Any, Dict, Optional, List, TypedDict
from enum import Enum

from ..common import CorrelationID, Timestamp, JSONType


class LLMProvider(Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ModelConfig(TypedDict):
    """LLM model configuration."""
    name: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    provider: str
    api_key: Optional[str]


class LLMRequest(TypedDict):
    """Request to LLM."""
    model: str
    prompt: str
    system_prompt: Optional[str]
    temperature: float
    max_tokens: int
    timeout_seconds: int
    metadata: Dict[str, Any]


class LLMResponse(TypedDict):
    """Response from LLM."""
    content: str
    model: str
    usage: Dict[str, int]
    response_time_seconds: float
    metadata: Dict[str, Any]


class LLMUsage(TypedDict):
    """Token usage information from LLM."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ModelCapabilities(TypedDict):
    """Model capabilities and limitations."""
    max_context_length: int
    supports_system_prompts: bool
    supports_function_calling: bool
    supports_streaming: bool
    cost_per_1k_tokens: float


class ProviderConfig(TypedDict):
    """Configuration for an LLM provider."""
    provider: str
    api_key: Optional[str]
    base_url: Optional[str]
    models: Dict[str, ModelConfig]
    rate_limits: Dict[str, int]
    default_model: str


class LLMMetrics(TypedDict):
    """Metrics for LLM operations."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    total_tokens_used: int
    total_cost: float