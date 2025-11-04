"""
Consolidated constants for AI Code Review Multi-Agent System.

This module contains all constants used across the application,
organized by functional area for better maintainability.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, Any

# ===== ENUMS =====
class AgentType(Enum):
    """Types of analysis agents."""
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    ENGINEERING_PRACTICES = "engineering_practices"
    COMPLEXITY = "complexity"
    DOCUMENTATION = "documentation"


class AgentStatus(Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class SessionStatus(Enum):
    """Session status values."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(Enum):
    """Analysis priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Severity(Enum):
    """Finding severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalysisType(Enum):
    """Types of code analysis."""
    QUALITY = "quality"
    SECURITY = "security"
    COMPLEXITY = "complexity"
    DOCUMENTATION = "documentation"
    ENGINEERING_PRACTICES = "engineering_practices"
    COMPREHENSIVE = "comprehensive"


class ToolType(Enum):
    """Tool type categories."""
    STATIC_ANALYZER = "static_analyzer"
    COMPLEXITY_ANALYZER = "complexity_analyzer"
    TREE_SITTER = "tree_sitter"
    LINTER = "linter"
    FORMATTER = "formatter"


class ToolStatus(Enum):
    """Tool execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class WorkflowType(Enum):
    """Workflow type categories."""
    CODE_REVIEW = "code_review"
    QUALITY_ANALYSIS = "quality_analysis"
    SECURITY_SCAN = "security_scan"
    COMPREHENSIVE = "comprehensive"


class StepStatus(Enum):
    """Workflow step execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ReportType(Enum):
    """Report type categories."""
    SUMMARY = "summary"
    DETAILED = "detailed"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"


class ReportFormat(Enum):
    """Report output formats."""
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"


class FindingCategory(Enum):
    """Finding categories."""
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"


class SecurityCategory(Enum):
    """Security finding categories."""
    VULNERABILITY = "vulnerability"
    CRYPTOGRAPHY = "cryptography"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input_validation"


class ComplexityMetric(Enum):
    """Code complexity metrics."""
    CYCLOMATIC = "cyclomatic"
    COGNITIVE = "cognitive"
    HALSTEAD = "halstead"
    MAINTAINABILITY_INDEX = "maintainability_index"


class EngineeringPracticeCategory(Enum):
    """Engineering practice categories."""
    TESTING = "testing"
    CODE_ORGANIZATION = "code_organization"
    ERROR_HANDLING = "error_handling"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"

# ===== ENVIRONMENT AND DEPLOYMENT =====
ENVIRONMENT_DEVELOPMENT = "development"
ENVIRONMENT_STAGING = "staging"
ENVIRONMENT_PRODUCTION = "production"

# Environment variable constants
ENV_VAR_PREFIX = "ACRMA_"  # AI Code Review Multi-Agent
CONFIG_FILE_ENV_VAR = f"{ENV_VAR_PREFIX}CONFIG_FILE"
ENVIRONMENT_ENV_VAR = f"{ENV_VAR_PREFIX}ENVIRONMENT"
DEBUG_ENV_VAR = f"{ENV_VAR_PREFIX}DEBUG"

# ===== TIMEOUTS =====
DEFAULT_TIMEOUT = 30
SHORT_TIMEOUT = 10
LONG_TIMEOUT = 300

# Agent execution timeouts (seconds)
DEFAULT_AGENT_TIMEOUT = 300  # 5 minutes
QUICK_AGENT_TIMEOUT = 60   # 1 minute
LONG_AGENT_TIMEOUT = 900   # 15 minutes

# Workflow timeouts (seconds)
DEFAULT_WORKFLOW_TIMEOUT = 1800  # 30 minutes
QUICK_WORKFLOW_TIMEOUT = 300     # 5 minutes
LONG_WORKFLOW_TIMEOUT = 3600     # 1 hour

# Session timeouts (seconds)
DEFAULT_SESSION_TIMEOUT = 7200   # 2 hours
MAX_SESSION_TIMEOUT = 86400      # 24 hours

# LLM timeouts (seconds)
DEFAULT_LLM_TIMEOUT = 60
QUICK_LLM_TIMEOUT = 30
LONG_LLM_TIMEOUT = 180

# API timeouts (seconds)
DEFAULT_API_TIMEOUT = 30
DEFAULT_REQUEST_TIMEOUT = 60
LONG_RUNNING_REQUEST_TIMEOUT = 300

# Configuration loading timeouts (seconds)
CONFIG_LOAD_TIMEOUT = 30
CONFIG_VALIDATION_TIMEOUT = 10

# ===== FILE SYSTEM =====
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE  # Alias for compatibility
MAX_FILES_PER_REQUEST = 50
MAX_FILENAME_LENGTH = 255
MAX_FILE_CONTENT_LENGTH = 1024 * 1024  # 1MB
TEMP_DIR = "/tmp"
CONFIG_DIR = "config"

# Configuration file names and paths
CONFIG_DIR_NAME = "config"
CONFIG_FILE_EXTENSIONS = [".yaml", ".yml", ".json"]
DEFAULT_CONFIG_FILENAME = "application.yaml"

# Configuration file size limits (bytes)
MAX_CONFIG_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Request size limits (bytes)
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
MAX_JSON_PAYLOAD_SIZE = 5 * 1024 * 1024  # 5MB

# ===== LOGGING =====
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"

# ===== API AND HTTP =====
API_VERSION_V1 = "v1"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1

# HTTP Headers
CORRELATION_ID_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"
RATE_LIMIT_HEADER = "X-RateLimit-Limit"
RATE_LIMIT_REMAINING_HEADER = "X-RateLimit-Remaining"
RATE_LIMIT_RESET_HEADER = "X-RateLimit-Reset"
API_VERSION_HEADER = "API-Version"

# Content Types
JSON_CONTENT_TYPE = "application/json"
TEXT_CONTENT_TYPE = "text/plain"
YAML_CONTENT_TYPE = "application/x-yaml"

# Default headers for API responses
DEFAULT_RESPONSE_HEADERS = {
    "Content-Type": JSON_CONTENT_TYPE,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block"
}

# HTTP Methods
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

# Status Code Groups
INFORMATIONAL_STATUS_CODES = range(100, 200)
SUCCESS_STATUS_CODES = range(200, 300)
REDIRECTION_STATUS_CODES = range(300, 400)
CLIENT_ERROR_STATUS_CODES = range(400, 500)
SERVER_ERROR_STATUS_CODES = range(500, 600)

# Common HTTP Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_202_ACCEPTED = 202
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_405_METHOD_NOT_ALLOWED = 405
HTTP_409_CONFLICT = 409
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_429_TOO_MANY_REQUESTS = 429
HTTP_500_INTERNAL_SERVER_ERROR = 500
HTTP_502_BAD_GATEWAY = 502
HTTP_503_SERVICE_UNAVAILABLE = 503
HTTP_504_GATEWAY_TIMEOUT = 504

# Response messages
RESPONSE_MESSAGES = {
    "success": "Operation completed successfully",
    "created": "Resource created successfully",
    "updated": "Resource updated successfully",
    "deleted": "Resource deleted successfully",
    "not_found": "Resource not found",
    "bad_request": "Invalid request format",
    "unauthorized": "Authentication required",
    "forbidden": "Access denied",
    "conflict": "Resource conflict",
    "validation_error": "Request validation failed",
    "rate_limit_exceeded": "Rate limit exceeded",
    "internal_error": "Internal server error",
    "service_unavailable": "Service temporarily unavailable",
    "timeout": "Request timeout"
}

# Rate limiting constants
DEFAULT_RATE_LIMIT = 1000  # requests per hour
DEFAULT_RATE_LIMIT_WINDOW = 3600  # seconds

# API versioning
SUPPORTED_API_VERSIONS = ["v1"]
DEFAULT_API_VERSION = "v1"

# CORS settings
CORS_MAX_AGE = 86400  # 24 hours
CORS_ALLOW_CREDENTIALS = True

# Request context constants
MAX_CORRELATION_ID_LENGTH = 36  # UUID length
MAX_USER_AGENT_LENGTH = 500

# ===== LLM CONFIGURATION =====
DEFAULT_MAX_TOKENS = 4000
MAX_CONTEXT_TOKENS = 32000
MAX_OUTPUT_TOKENS = 8000
DEFAULT_TEMPERATURE = 0.7

# Temperature ranges
MIN_TEMPERATURE = 0.0
MAX_TEMPERATURE = 2.0

# Model configuration defaults
DEFAULT_MODEL_CONFIG = {
    "temperature": DEFAULT_TEMPERATURE,
    "max_tokens": DEFAULT_MAX_TOKENS,
    "timeout_seconds": DEFAULT_LLM_TIMEOUT
}

# LLM retry configuration
DEFAULT_LLM_RETRY_ATTEMPTS = 3
MAX_LLM_RETRY_ATTEMPTS = 5
LLM_RETRY_BACKOFF_BASE = 2

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

# ===== AGENT CONFIGURATION =====
MAX_CONCURRENT_AGENTS = 10
MAX_AGENTS_PER_WORKFLOW = 20
MAX_WORKFLOW_DEPTH = 5
MAX_CONCURRENT_SESSIONS = 50  # Maximum concurrent user sessions

# Agent priority levels
AGENT_PRIORITY_CRITICAL = 1
AGENT_PRIORITY_HIGH = 2
AGENT_PRIORITY_MEDIUM = 3
AGENT_PRIORITY_LOW = 4

# Agent retry configuration
DEFAULT_RETRY_ATTEMPTS = 3
MAX_RETRY_ATTEMPTS = 5
RETRY_BACKOFF_BASE = 2  # exponential backoff multiplier

# Agent result scoring
MIN_QUALITY_SCORE = 0.0
MAX_QUALITY_SCORE = 100.0
MIN_RISK_SCORE = 0.0
MAX_RISK_SCORE = 100.0

# Agent memory limits
MAX_AGENT_MEMORY_MB = 512
MAX_SESSION_MEMORY_MB = 2048

# Function tool limits
MAX_TOOL_EXECUTION_TIME = 60  # seconds
DEFAULT_TOOL_TIMEOUT = MAX_TOOL_EXECUTION_TIME  # Alias for compatibility
DEFAULT_MAX_TOOL_RETRIES = DEFAULT_RETRY_ATTEMPTS  # Alias for compatibility
MAX_TOOL_OUTPUT_SIZE = 1024 * 1024  # 1MB
MAX_TOOLS_PER_AGENT = 50

# Agent metadata constants
AGENT_VERSION_KEY = "agent_version"
EXECUTION_CONTEXT_KEY = "execution_context"
PERFORMANCE_METRICS_KEY = "performance_metrics"

# Workflow execution states
WORKFLOW_STATE_PENDING = "pending"
WORKFLOW_STATE_RUNNING = "running"
WORKFLOW_STATE_COMPLETED = "completed"
WORKFLOW_STATE_FAILED = "failed"
WORKFLOW_STATE_CANCELLED = "cancelled"

# Agent health check constants
AGENT_HEALTH_CHECK_INTERVAL = 30  # seconds
AGENT_HEALTH_TIMEOUT = 10  # seconds
MAX_FAILED_HEALTH_CHECKS = 3

# Agent registry constants
MAX_AGENT_NAME_LENGTH = 100
MAX_AGENT_DESCRIPTION_LENGTH = 500
AGENT_CONFIG_VERSION = "1.0"

# Session management constants
SESSION_CLEANUP_INTERVAL = 3600  # 1 hour
SESSION_INACTIVITY_TIMEOUT = 1800  # 30 minutes
MAX_SESSIONS_PER_USER = 10

# Analysis result constants
MAX_FINDINGS_PER_AGENT = 1000
MAX_RECOMMENDATION_LENGTH = 1000
MAX_SUMMARY_LENGTH = 2000

# Agent communication constants
INTER_AGENT_MESSAGE_TIMEOUT = 30  # seconds
MAX_MESSAGE_SIZE = 10 * 1024  # 10KB
MAX_MESSAGES_PER_AGENT = 100

# ===== CODE ANALYSIS =====
CODE_QUALITY_THRESHOLD = 70.0
SECURITY_RISK_THRESHOLD = 30.0
COMPLEXITY_THRESHOLD = 10
DOCUMENTATION_COVERAGE_THRESHOLD = 80.0

# ===== CONFIGURATION MANAGEMENT =====
# Configuration keys for loading
CONFIG_KEYS = {
    'APPLICATION': 'application',
    'API': 'api',
    'OBSERVABILITY': 'observability',
    'LLM': 'llm',
    'AGENTS': 'agents',
    'ENVIRONMENTS': 'environments',
    'TREE_SITTER': 'tree_sitter',
    'RULES': 'rules',
    'INTEGRATIONS': 'integrations',
    'REPORTING': 'reporting'
}

# Default configuration values
DEFAULT_VALUES = {
    'environment': 'development',
    'debug': False,
    'log_level': 'INFO',
    'api_version': 'v1',
    'api_prefix': '/api/v1'
}

# Configuration validation constants
REQUIRED_CONFIG_SECTIONS = ['application', 'api', 'observability']
OPTIONAL_CONFIG_SECTIONS = ['llm', 'agents', 'environments']

# ===== UTILITY FUNCTIONS =====
# Note: Functions are defined at end of file to use utility section constants

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

from pathlib import Path
from typing import Dict, Any

# ==============================================================================
# SYSTEM CONSTANTS
# ==============================================================================

# System identification
SYSTEM_NAME = "AI Code Review Multi-Agent"
SYSTEM_VERSION = "1.0.0"
API_VERSION = "v1"

# Environment constants
DEFAULT_ENVIRONMENT = "development"
PRODUCTION_ENVIRONMENT = "production"
SUPPORTED_ENVIRONMENTS = ["development", "staging", "production"]

# ==============================================================================
# CONFIGURATION CONSTANTS
# ==============================================================================

# Configuration paths and files
CONFIG_DIR_NAME = "config"
CONFIG_FILE_EXTENSIONS = [".yaml", ".yml", ".json"]
DEFAULT_CONFIG_FILENAME = "application.yaml"

# Configuration keys
CONFIG_KEYS = {
    'APPLICATION': 'application',
    'API': 'api',
    'OBSERVABILITY': 'observability',
    'LLM': 'llm',
    'AGENTS': 'agents',
    'ADK': 'adk',
    'ENVIRONMENTS': 'environments',
    'TREE_SITTER': 'tree_sitter',
    'RULES': 'rules',
    'INTEGRATIONS': 'integrations',
    'REPORTING': 'reporting'
}

# Environment variable constants
ENV_VAR_PREFIX = "ACRMA_"  # AI Code Review Multi-Agent
CONFIG_FILE_ENV_VAR = f"{ENV_VAR_PREFIX}CONFIG_FILE"
ENVIRONMENT_ENV_VAR = f"{ENV_VAR_PREFIX}ENVIRONMENT"
DEBUG_ENV_VAR = f"{ENV_VAR_PREFIX}DEBUG"

# Configuration validation
REQUIRED_CONFIG_SECTIONS = ['application', 'api', 'observability']
OPTIONAL_CONFIG_SECTIONS = ['llm', 'agents', 'adk', 'environments']

# Configuration limits
CONFIG_LOAD_TIMEOUT = 30  # seconds
CONFIG_VALIDATION_TIMEOUT = 10  # seconds
MAX_CONFIG_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# ==============================================================================
# AGENT CONSTANTS
# ==============================================================================

# Agent execution timeouts (seconds)
DEFAULT_AGENT_TIMEOUT = 300  # 5 minutes
QUICK_AGENT_TIMEOUT = 60   # 1 minute
LONG_AGENT_TIMEOUT = 900   # 15 minutes

# Workflow timeouts (seconds)
DEFAULT_WORKFLOW_TIMEOUT = 1800  # 30 minutes
QUICK_WORKFLOW_TIMEOUT = 300     # 5 minutes
LONG_WORKFLOW_TIMEOUT = 3600     # 1 hour

# Session timeouts (seconds)
DEFAULT_SESSION_TIMEOUT = 7200   # 2 hours
MAX_SESSION_TIMEOUT = 86400      # 24 hours
SESSION_CLEANUP_INTERVAL = 3600  # 1 hour
SESSION_INACTIVITY_TIMEOUT = 1800  # 30 minutes

# Agent priority levels
AGENT_PRIORITY_CRITICAL = 1
AGENT_PRIORITY_HIGH = 2
AGENT_PRIORITY_MEDIUM = 3
AGENT_PRIORITY_LOW = 4

# Agent retry configuration
DEFAULT_RETRY_ATTEMPTS = 3
MAX_RETRY_ATTEMPTS = 5
RETRY_BACKOFF_BASE = 2  # exponential backoff multiplier

# Agent execution limits
MAX_CONCURRENT_AGENTS = 10
MAX_AGENTS_PER_WORKFLOW = 20
MAX_WORKFLOW_DEPTH = 5
MAX_SESSIONS_PER_USER = 10

# Agent memory limits (MB)
MAX_AGENT_MEMORY_MB = 512
MAX_SESSION_MEMORY_MB = 2048

# Agent health checks
AGENT_HEALTH_CHECK_INTERVAL = 30  # seconds
AGENT_HEALTH_TIMEOUT = 10  # seconds
MAX_FAILED_HEALTH_CHECKS = 3

# ==============================================================================
# TOOL CONSTANTS
# ==============================================================================

# Function tool limits
MAX_TOOL_EXECUTION_TIME = 60  # seconds
MAX_TOOL_OUTPUT_SIZE = 1024 * 1024  # 1MB
MAX_TOOLS_PER_AGENT = 50

# Tool timeouts by type (seconds)
TREE_SITTER_TOOL_TIMEOUT = 60
COMPLEXITY_ANALYZER_TIMEOUT = 90
STATIC_ANALYZER_TIMEOUT = 120

# ==============================================================================
# ANALYSIS CONSTANTS
# ==============================================================================

# Quality thresholds
CODE_QUALITY_THRESHOLD = 70.0
SECURITY_RISK_THRESHOLD = 30.0
COMPLEXITY_THRESHOLD = 10
DOCUMENTATION_COVERAGE_THRESHOLD = 80.0
TEST_COVERAGE_THRESHOLD = 80.0

# Scoring ranges
MIN_QUALITY_SCORE = 0.0
MAX_QUALITY_SCORE = 100.0
MIN_RISK_SCORE = 0.0
MAX_RISK_SCORE = 100.0

# Analysis limits
MAX_FINDINGS_PER_AGENT = 1000
MAX_RECOMMENDATION_LENGTH = 1000
MAX_SUMMARY_LENGTH = 2000

# ==============================================================================
# API CONSTANTS
# ==============================================================================

# API configuration
API_PREFIX = "/api/v1"
DEFAULT_API_TIMEOUT = 30  # seconds

# HTTP limits
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
MAX_RESPONSE_SIZE = 50 * 1024 * 1024  # 50MB

# Rate limiting
DEFAULT_RATE_LIMIT = 100  # requests per minute
BURST_RATE_LIMIT = 200  # burst requests

# ==============================================================================
# SECURITY CONSTANTS
# ==============================================================================

# Content validation
MAX_INPUT_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = [".py", ".js", ".ts", ".java", ".go", ".rb", ".php", ".cpp", ".c", ".cs"]

# Message limits
INTER_AGENT_MESSAGE_TIMEOUT = 30  # seconds
MAX_MESSAGE_SIZE = 10 * 1024  # 10KB
MAX_MESSAGES_PER_AGENT = 100

# ==============================================================================
# METADATA CONSTANTS
# ==============================================================================

# Agent metadata keys
AGENT_VERSION_KEY = "agent_version"
EXECUTION_CONTEXT_KEY = "execution_context"
PERFORMANCE_METRICS_KEY = "performance_metrics"

# Agent registry
MAX_AGENT_NAME_LENGTH = 100
MAX_AGENT_DESCRIPTION_LENGTH = 500
AGENT_CONFIG_VERSION = "1.0"

# ==============================================================================
# STATE CONSTANTS
# ==============================================================================

# Workflow execution states
WORKFLOW_STATE_PENDING = "pending"
WORKFLOW_STATE_RUNNING = "running"
WORKFLOW_STATE_COMPLETED = "completed"
WORKFLOW_STATE_FAILED = "failed"
WORKFLOW_STATE_CANCELLED = "cancelled"

# Agent status states
AGENT_STATUS_PENDING = "pending"
AGENT_STATUS_RUNNING = "running"
AGENT_STATUS_COMPLETED = "completed"
AGENT_STATUS_FAILED = "failed"
AGENT_STATUS_TIMEOUT = "timeout"

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def get_config_dir() -> Path:
    """Get the configuration directory path."""
    current_file = Path(__file__)
    # Go up to src parent, then config
    repo_root = current_file.parent.parent
    return repo_root / CONFIG_DIR_NAME


def get_default_config_paths() -> Dict[str, Path]:
    """Get default configuration file paths."""
    config_dir = get_config_dir()
    return {
        'application': config_dir / 'api' / 'application.yaml',
        'observability': config_dir / 'observability' / 'monitoring.yaml',
        'adk': config_dir / 'adk',
        'llm': config_dir / 'llm',
        'agents': config_dir / 'agents',
        'environments': config_dir / 'environments',
        'tree_sitter': config_dir / 'tree_sitter',
        'rules': config_dir / 'rules',
        'integrations': config_dir / 'integrations',
        'reporting': config_dir / 'reporting'
    }