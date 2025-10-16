"""
Constants for LLM (Large Language Model) components.

This module contains constants specific to LLM operations,
model configurations, and provider integrations.
"""

from enum import Enum

# LLM timeouts (seconds)
DEFAULT_LLM_TIMEOUT = 60
QUICK_LLM_TIMEOUT = 30
LONG_LLM_TIMEOUT = 180

# LLM retry configuration
DEFAULT_LLM_RETRY_ATTEMPTS = 3
MAX_LLM_RETRY_ATTEMPTS = 5
LLM_RETRY_BACKOFF_BASE = 2

# Token limits
DEFAULT_MAX_TOKENS = 4000
MAX_CONTEXT_TOKENS = 32000
MAX_OUTPUT_TOKENS = 8000

# Temperature ranges
MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 2.0
DEFAULT_TEMPERATURE = 0.7

# Model configuration defaults
DEFAULT_MODEL_CONFIG = {
    "temperature": DEFAULT_TEMPERATURE,
    "max_tokens": DEFAULT_MAX_TOKENS,
    "timeout_seconds": DEFAULT_LLM_TIMEOUT
}

# Provider-specific constants
OLLAMA_DEFAULT_HOST = "http://localhost:11434"
OLLAMA_DEFAULT_TIMEOUT = 60
OLLAMA_HEALTH_ENDPOINT = "/api/tags"

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_DEFAULT_MODEL = "gemini-1.5-flash"

OPENAI_API_BASE_URL = "https://api.openai.com/v1"
OPENAI_DEFAULT_MODEL = "gpt-3.5-turbo"

ANTHROPIC_API_BASE_URL = "https://api.anthropic.com/v1"
ANTHROPIC_DEFAULT_MODEL = "claude-3-haiku-20240307"

# Rate limiting defaults (requests per minute)
DEFAULT_RATE_LIMIT_RPM = 60
OLLAMA_RATE_LIMIT_RPM = 300  # Higher for local
GEMINI_RATE_LIMIT_RPM = 60
OPENAI_RATE_LIMIT_RPM = 60
ANTHROPIC_RATE_LIMIT_RPM = 60

# Token cost estimates (per 1K tokens in USD)
TOKEN_COSTS = {
    "gpt-3.5-turbo": 0.002,
    "gpt-4": 0.06,
    "gemini-1.5-flash": 0.00015,
    "claude-3-haiku": 0.00025,
    "ollama": 0.0  # Local models are free
}

# Response validation constants
MAX_RESPONSE_LENGTH = 50000  # characters
MIN_RESPONSE_LENGTH = 10    # characters
RESPONSE_VALIDATION_TIMEOUT = 5  # seconds

# Content filtering constants
CONTENT_FILTER_ENABLED = True
MAX_CONTENT_FILTER_RETRIES = 2

# Model capabilities
MODEL_CAPABILITIES = {
    "supports_system_prompts": True,
    "supports_function_calling": False,
    "supports_streaming": True,
    "max_context_length": MAX_CONTEXT_TOKENS
}

# Prompt engineering constants
MAX_SYSTEM_PROMPT_LENGTH = 2000
MAX_USER_PROMPT_LENGTH = 10000
PROMPT_TEMPLATE_VERSION = "1.0"

# LLM monitoring constants
PERFORMANCE_TRACKING_ENABLED = True
USAGE_TRACKING_ENABLED = True
COST_TRACKING_ENABLED = True

# Error handling constants
MAX_CONSECUTIVE_ERRORS = 5
ERROR_RECOVERY_DELAY = 10  # seconds
CIRCUIT_BREAKER_TIMEOUT = 300  # 5 minutes

# Metrics constants
METRICS_COLLECTION_INTERVAL = 60  # seconds
METRICS_RETENTION_DAYS = 30
USAGE_REPORT_INTERVAL = 86400  # 24 hours

# Provider health check constants
PROVIDER_HEALTH_CHECK_INTERVAL = 300  # 5 minutes
PROVIDER_HEALTH_TIMEOUT = 10  # seconds
MAX_FAILED_PROVIDER_CHECKS = 3

# Model selection constants
MODEL_SELECTION_STRATEGY = "round_robin"  # round_robin, least_cost, fastest
MODEL_FALLBACK_ENABLED = True
MAX_MODEL_FALLBACKS = 2