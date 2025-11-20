"""
Generic LLM wrapper with rate limiting and error handling

Works with any LLM provider (Gemini, Ollama, OpenAI, etc.) through ADK's unified interface.
Provides transparent rate limiting, error handling, and monitoring.
"""

import asyncio
import logging
from typing import Any, Optional, Protocol
from util.rate_limiter import get_rate_limiter, RateLimitConfig

logger = logging.getLogger(__name__)


# Protocol for any ADK-compatible LLM model
class LLMProtocol(Protocol):
    """Protocol defining the interface for LLM models in ADK"""
    async def generate_content_async(self, *args, **kwargs) -> Any:
        """Generate content asynchronously"""
        ...


class UniversalLLMWrapper:
    """
    Generic wrapper for any LLM provider that adds rate limiting and monitoring.
    
    Works with:
    - google.adk.models.Gemini (Google Gemini models)
    - google.adk.models.lite_llm.LiteLlm (Ollama, OpenAI, etc. via LiteLLM)
    - Any ADK-compatible model implementing generate_content_async()
    
    Usage:
        wrapper = UniversalLLMWrapper(rate_limit_config=config)
        
        # In agent execution (ADK handles this internally)
        # No code changes needed - rate limiting applied via sequential execution
    """
    
    def __init__(
        self,
        rate_limit_config: Optional[RateLimitConfig] = None,
        provider_name: str = "LLM"
    ):
        """
        Initialize the universal LLM wrapper.
        
        Args:
            rate_limit_config: Optional rate limiting configuration
            provider_name: Human-readable provider name for logging (e.g., "Gemini", "Ollama")
        """
        self.provider_name = provider_name
        self.rate_limiter = get_rate_limiter()
        
        # Configure rate limiter if provided
        if rate_limit_config:
            from util.rate_limiter import configure_rate_limiter
            configure_rate_limiter(rate_limit_config)
            self.rate_limiter = get_rate_limiter()
        
        logger.info(f"🔧 UniversalLLMWrapper initialized for {provider_name}")
    
    async def generate_with_rate_limit(
        self,
        llm: LLMProtocol,
        *args,
        **kwargs
    ) -> Any:
        """
        Generate content with rate limiting for any LLM provider.
        
        Args:
            llm: Any ADK-compatible LLM instance (Gemini, LiteLlm, etc.)
            *args: Positional arguments for generate_content_async()
            **kwargs: Keyword arguments for generate_content_async()
            
        Returns:
            Response from the LLM (format depends on provider)
            
        Raises:
            RuntimeError: If rate limit timeout exceeded
            Exception: Any provider-specific errors
        """
        # Acquire rate limit token
        acquired = await self.rate_limiter.acquire(timeout=60.0)
        if not acquired:
            raise RuntimeError(
                f"Rate limit timeout for {self.provider_name}: Could not acquire token within 60s"
            )
        
        try:
            # Make the actual API call
            logger.info(f"🚦 Rate limiter: Token acquired for {self.provider_name}, making API call")
            
            # Check if streaming
            if kwargs.get('stream', False):
                # For streaming, return async iterator
                async def rate_limited_stream():
                    try:
                        async for chunk in llm.generate_content_async(*args, **kwargs):
                            yield chunk
                    except Exception as e:
                        self._handle_provider_error(e)
                        raise
                return rate_limited_stream()
            else:
                # For non-streaming, return response directly
                response = await llm.generate_content_async(*args, **kwargs)
                return response
                
        except Exception as e:
            self._handle_provider_error(e)
            raise
    
    def _handle_provider_error(self, error: Exception):
        """
        Handle provider-specific errors and update rate limiter state.
        
        Detects rate limit and availability errors across different providers:
        - Gemini: 429 RESOURCE_EXHAUSTED, 503 UNAVAILABLE
        - OpenAI: 429 rate_limit_exceeded, 503 service_unavailable
        - Ollama: Connection errors, timeout errors
        
        Args:
            error: The exception raised by the provider
        """
        error_str = str(error).lower()
        status_code = None
        
        # Detect rate limit errors (429)
        if any(indicator in error_str for indicator in [
            '429', 'rate limit', 'resource_exhausted', 'quota', 'too many requests'
        ]):
            status_code = 429
            logger.warning(f"⚠️  {self.provider_name} rate limit error: {error}")
        
        # Detect availability errors (503)
        elif any(indicator in error_str for indicator in [
            '503', 'unavailable', 'overloaded', 'service unavailable', 'timeout'
        ]):
            status_code = 503
            logger.warning(f"⚠️  {self.provider_name} availability error: {error}")
        
        # Detect generic server errors (500)
        elif any(indicator in error_str for indicator in [
            '500', 'internal error', 'server error'
        ]):
            status_code = 500
            logger.warning(f"⚠️  {self.provider_name} server error: {error}")
        
        # Update rate limiter state if needed
        if status_code in (429, 503):
            self.rate_limiter.on_error(status_code)
            logger.info(f"⏸️  Rate limiter entering cooldown due to {status_code} error")
        
        # Log unexpected errors
        if status_code is None:
            logger.error(f"❌ Unexpected {self.provider_name} error: {error}")


def get_provider_config(provider: str) -> RateLimitConfig:
    """
    Get recommended rate limit configuration for a specific provider.
    
    Args:
        provider: Provider name ('gemini', 'ollama', 'openai', etc.)
        
    Returns:
        RateLimitConfig: Recommended configuration for that provider
    """
    configs = {
        'gemini': RateLimitConfig(
            requests_per_minute=10,     # Conservative for free tier
            burst_size=3,
            cooldown_on_error=30.0
        ),
        'gemini_paid': RateLimitConfig(
            requests_per_minute=60,     # Standard tier
            burst_size=10,
            cooldown_on_error=10.0
        ),
        'ollama': RateLimitConfig(
            requests_per_minute=30,     # Local models, more generous
            burst_size=5,
            cooldown_on_error=5.0       # Faster recovery for local
        ),
        'openai': RateLimitConfig(
            requests_per_minute=20,     # OpenAI tier 1
            burst_size=5,
            cooldown_on_error=20.0
        ),
    }
    
    # Default config for unknown providers
    default = RateLimitConfig(
        requests_per_minute=10,
        burst_size=3,
        cooldown_on_error=30.0
    )
    
    return configs.get(provider.lower(), default)


# Usage examples:
"""
OPTION 1: Automatic detection from environment (recommended)
=============================================================
The system now automatically detects the LLM provider from util/llm_model.py
and applies appropriate rate limiting via sequential agent execution.

No code changes needed in agents - rate limiting is transparent!


OPTION 2: Manual configuration for custom scenarios
====================================================
from util.gemini_wrapper import UniversalLLMWrapper, get_provider_config

# For Gemini free tier
gemini_config = get_provider_config('gemini')
wrapper = UniversalLLMWrapper(rate_limit_config=gemini_config, provider_name="Gemini")

# For Ollama local models  
ollama_config = get_provider_config('ollama')
wrapper = UniversalLLMWrapper(rate_limit_config=ollama_config, provider_name="Ollama")

# For OpenAI
openai_config = get_provider_config('openai')
wrapper = UniversalLLMWrapper(rate_limit_config=openai_config, provider_name="OpenAI")


CURRENT IMPLEMENTATION:
=======================
Rate limiting is implemented via sequential agent execution in orchestrator_agent/agent.py.
This approach works with ALL LLM providers transparently:

1. Agents execute one at a time (not in parallel)
2. 2-second delay between agents
3. Prevents API overload regardless of provider
4. No provider-specific code needed

See orchestrator_agent/agent.py lines 306-335 for implementation.
"""
