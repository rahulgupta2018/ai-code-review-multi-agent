"""
System constants and enums for ADK Multi-Agent Code Review MVP.

This module defines all system-wide constants, enumerations, and configuration
values used throughout the application.
"""

from enum import Enum
from typing import Dict, List, Set


# Application Constants
APP_NAME = "ADK Multi-Agent Code Review"
APP_VERSION = "1.0.0"
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Default timeouts (in seconds)
DEFAULT_API_TIMEOUT = 30
DEFAULT_AGENT_TIMEOUT = 300
DEFAULT_WORKFLOW_TIMEOUT = 1200
DEFAULT_LLM_TIMEOUT = 120
DEFAULT_SESSION_TIMEOUT = 1800  # 30 minutes

# Rate limiting constants
DEFAULT_RATE_LIMIT_PER_MINUTE = 100
DEFAULT_CONCURRENT_REQUESTS = 10
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_BACKOFF_FACTOR = 2.0

# File processing limits
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_FILES_PER_REQUEST = 50
MAX_TOTAL_CONTENT_SIZE = 100 * 1024 * 1024  # 100MB
MAX_FILENAME_LENGTH = 255
MAX_FILE_CONTENT_LENGTH = 1_000_000  # 1M characters

# Analysis constants
MIN_COMPLEXITY_THRESHOLD = 1
MAX_COMPLEXITY_THRESHOLD = 50
DEFAULT_COMPLEXITY_THRESHOLD = 10

# Session constants
MAX_CONCURRENT_SESSIONS = 100
SESSION_CLEANUP_INTERVAL = 300  # 5 minutes
MAX_SESSION_MEMORY_MB = 500


class SupportedLanguage(str, Enum):
    """Supported programming languages for analysis."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    C = "c"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"
    KOTLIN = "kotlin"
    SWIFT = "swift"
    SCALA = "scala"


class AnalysisType(str, Enum):
    """Types of analysis that can be performed."""
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    ENGINEERING_PRACTICES = "engineering_practices"
    COMPREHENSIVE = "comprehensive"


class AgentType(str, Enum):
    """Types of analysis agents."""
    CODE_QUALITY_AGENT = "code_quality_agent"
    SECURITY_AGENT = "security_agent"
    ENGINEERING_PRACTICES_AGENT = "engineering_practices_agent"
    MASTER_ORCHESTRATOR = "master_orchestrator"


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class SessionStatus(str, Enum):
    """Session status values."""
    CREATED = "created"
    ACTIVE = "active"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Priority levels for analysis and issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Severity(str, Enum):
    """Severity levels for findings and issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ComplexityMetric(str, Enum):
    """Code complexity metrics."""
    CYCLOMATIC = "cyclomatic"
    COGNITIVE = "cognitive"
    HALSTEAD = "halstead"
    MAINTAINABILITY_INDEX = "maintainability_index"
    LINES_OF_CODE = "lines_of_code"
    NESTING_DEPTH = "nesting_depth"


class SecurityCategory(str, Enum):
    """Security vulnerability categories."""
    INJECTION = "injection"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SENSITIVE_DATA = "sensitive_data"
    CRYPTOGRAPHY = "cryptography"
    INPUT_VALIDATION = "input_validation"
    OUTPUT_ENCODING = "output_encoding"
    ERROR_HANDLING = "error_handling"
    LOGGING = "logging"
    CONFIGURATION = "configuration"


class EngineeringPracticeCategory(str, Enum):
    """Engineering practice categories."""
    TESTING = "testing"
    ERROR_HANDLING = "error_handling"
    LOGGING = "logging"
    DOCUMENTATION = "documentation"
    CODE_ORGANIZATION = "code_organization"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    SCALABILITY = "scalability"
    MONITORING = "monitoring"
    DEPLOYMENT = "deployment"


class GeminiModel(str, Enum):
    """Available Gemini models."""
    GEMINI_PRO = "gemini-1.5-pro"
    GEMINI_FLASH = "gemini-2.0-flash-exp"
    GEMINI_FLASH_8B = "gemini-1.5-flash-8b"


class HTTPMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ContentType(str, Enum):
    """HTTP content types."""
    JSON = "application/json"
    TEXT = "text/plain"
    HTML = "text/html"
    XML = "application/xml"
    FORM_DATA = "multipart/form-data"
    URL_ENCODED = "application/x-www-form-urlencoded"


# Language file extensions mapping
LANGUAGE_EXTENSIONS: Dict[SupportedLanguage, Set[str]] = {
    SupportedLanguage.PYTHON: {".py", ".pyw", ".pyi"},
    SupportedLanguage.JAVASCRIPT: {".js", ".mjs", ".jsx"},
    SupportedLanguage.TYPESCRIPT: {".ts", ".tsx", ".d.ts"},
    SupportedLanguage.JAVA: {".java"},
    SupportedLanguage.GO: {".go"},
    SupportedLanguage.RUST: {".rs"},
    SupportedLanguage.CPP: {".cpp", ".cxx", ".cc", ".hpp", ".hxx", ".h"},
    SupportedLanguage.C: {".c", ".h"},
    SupportedLanguage.CSHARP: {".cs"},
    SupportedLanguage.PHP: {".php", ".phtml", ".php3", ".php4", ".php5"},
    SupportedLanguage.RUBY: {".rb", ".rbw"},
    SupportedLanguage.KOTLIN: {".kt", ".kts"},
    SupportedLanguage.SWIFT: {".swift"},
    SupportedLanguage.SCALA: {".scala", ".sc"},
}

# Extension to language mapping (reverse lookup)
EXTENSION_TO_LANGUAGE: Dict[str, SupportedLanguage] = {}
for language, extensions in LANGUAGE_EXTENSIONS.items():
    for ext in extensions:
        EXTENSION_TO_LANGUAGE[ext] = language

# Tree-sitter language mapping
TREE_SITTER_LANGUAGES: Dict[SupportedLanguage, str] = {
    SupportedLanguage.PYTHON: "python",
    SupportedLanguage.JAVASCRIPT: "javascript",
    SupportedLanguage.TYPESCRIPT: "typescript",
    SupportedLanguage.JAVA: "java",
    SupportedLanguage.GO: "go",
    SupportedLanguage.RUST: "rust",
    SupportedLanguage.CPP: "cpp",
    SupportedLanguage.C: "c",
    SupportedLanguage.CSHARP: "c_sharp",
    SupportedLanguage.PHP: "php",
    SupportedLanguage.RUBY: "ruby",
    SupportedLanguage.KOTLIN: "kotlin",
    SupportedLanguage.SWIFT: "swift",
    SupportedLanguage.SCALA: "scala",
}

# Default complexity thresholds by language
COMPLEXITY_THRESHOLDS: Dict[SupportedLanguage, Dict[ComplexityMetric, int]] = {
    SupportedLanguage.PYTHON: {
        ComplexityMetric.CYCLOMATIC: 10,
        ComplexityMetric.COGNITIVE: 15,
        ComplexityMetric.NESTING_DEPTH: 4,
        ComplexityMetric.LINES_OF_CODE: 50,
    },
    SupportedLanguage.JAVASCRIPT: {
        ComplexityMetric.CYCLOMATIC: 10,
        ComplexityMetric.COGNITIVE: 15,
        ComplexityMetric.NESTING_DEPTH: 4,
        ComplexityMetric.LINES_OF_CODE: 50,
    },
    SupportedLanguage.TYPESCRIPT: {
        ComplexityMetric.CYCLOMATIC: 10,
        ComplexityMetric.COGNITIVE: 15,
        ComplexityMetric.NESTING_DEPTH: 4,
        ComplexityMetric.LINES_OF_CODE: 50,
    },
    SupportedLanguage.JAVA: {
        ComplexityMetric.CYCLOMATIC: 12,
        ComplexityMetric.COGNITIVE: 18,
        ComplexityMetric.NESTING_DEPTH: 5,
        ComplexityMetric.LINES_OF_CODE: 60,
    },
    SupportedLanguage.GO: {
        ComplexityMetric.CYCLOMATIC: 8,
        ComplexityMetric.COGNITIVE: 12,
        ComplexityMetric.NESTING_DEPTH: 3,
        ComplexityMetric.LINES_OF_CODE: 40,
    },
}

# Security patterns to detect
SECURITY_PATTERNS: Dict[SecurityCategory, List[str]] = {
    SecurityCategory.INJECTION: [
        r"exec\s*\(",
        r"eval\s*\(",
        r"subprocess\.call",
        r"os\.system",
        r"shell=True",
        r"sql\s*=.*\+.*",  # Basic SQL injection pattern
    ],
    SecurityCategory.SENSITIVE_DATA: [
        r"password\s*=",
        r"api_key\s*=",
        r"secret\s*=",
        r"token\s*=",
        r"private_key",
        r"aws_access_key",
    ],
    SecurityCategory.CRYPTOGRAPHY: [
        r"md5\(",
        r"sha1\(",
        r"DES\(",
        r"RC4\(",
        r"random\.random\(",
    ],
}

# Common bad practices patterns
BAD_PRACTICES_PATTERNS: Dict[EngineeringPracticeCategory, List[str]] = {
    EngineeringPracticeCategory.ERROR_HANDLING: [
        r"except:\s*pass",
        r"except\s+Exception:\s*pass",
        r"try:.*except:.*pass",
    ],
    EngineeringPracticeCategory.LOGGING: [
        r"print\s*\(",  # In production code
        r"console\.log\(",  # In production JavaScript
    ],
    EngineeringPracticeCategory.CODE_ORGANIZATION: [
        r"^(?!.*def\s|.*class\s|.*import\s|.*from\s).*\S.*$",  # Code outside functions/classes
    ],
}

# HTTP status codes
HTTP_STATUS_CODES = {
    "OK": 200,
    "CREATED": 201,
    "ACCEPTED": 202,
    "NO_CONTENT": 204,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "METHOD_NOT_ALLOWED": 405,
    "CONFLICT": 409,
    "UNPROCESSABLE_ENTITY": 422,
    "TOO_MANY_REQUESTS": 429,
    "INTERNAL_SERVER_ERROR": 500,
    "BAD_GATEWAY": 502,
    "SERVICE_UNAVAILABLE": 503,
    "GATEWAY_TIMEOUT": 504,
}

# Response messages
RESPONSE_MESSAGES = {
    "ANALYSIS_STARTED": "Code analysis started successfully",
    "ANALYSIS_COMPLETED": "Code analysis completed successfully",
    "ANALYSIS_FAILED": "Code analysis failed",
    "SESSION_CREATED": "Analysis session created",
    "SESSION_NOT_FOUND": "Session not found",
    "INVALID_INPUT": "Invalid input provided",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded",
    "AUTHENTICATION_REQUIRED": "Authentication required",
    "INSUFFICIENT_PERMISSIONS": "Insufficient permissions",
    "SERVICE_UNAVAILABLE": "Service temporarily unavailable",
}

# ADK Configuration keys
ADK_CONFIG_KEYS = {
    "SESSION_SERVICE": "session_service",
    "MODEL_GARDEN": "model_garden",
    "AGENT_TIMEOUT": "agent_timeout",
    "WORKFLOW_TIMEOUT": "workflow_timeout",
    "MAX_RETRIES": "max_retries",
}

# Gemini model configurations
GEMINI_MODEL_CONFIGS = {
    GeminiModel.GEMINI_PRO: {
        "max_tokens": 8192,
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 40,
    },
    GeminiModel.GEMINI_FLASH: {
        "max_tokens": 8192,
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 40,
    },
    GeminiModel.GEMINI_FLASH_8B: {
        "max_tokens": 8192,
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 40,
    },
}

# Logging configuration
LOG_FORMATS = {
    "SIMPLE": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "DETAILED": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    "JSON": "json",
}

# Environment variable names
ENV_VARS = {
    "GEMINI_API_KEY": "GEMINI_API_KEY",
    "API_KEYS": "API_KEYS",
    "ENVIRONMENT": "ENVIRONMENT",
    "LOG_LEVEL": "LOG_LEVEL",
    "DATABASE_URL": "DATABASE_URL",
    "REDIS_URL": "REDIS_URL",
    "GOOGLE_CLOUD_PROJECT_ID": "GOOGLE_CLOUD_PROJECT_ID",
}

# Correlation ID header name
CORRELATION_ID_HEADER = "X-Correlation-ID"

# Request ID header name
REQUEST_ID_HEADER = "X-Request-ID"

# Default headers for API responses
DEFAULT_RESPONSE_HEADERS = {
    "Content-Type": ContentType.JSON.value,
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}

# Export all constants and enums
__all__ = [
    # Constants
    "APP_NAME",
    "APP_VERSION", 
    "API_VERSION",
    "API_PREFIX",
    "DEFAULT_API_TIMEOUT",
    "DEFAULT_AGENT_TIMEOUT",
    "DEFAULT_WORKFLOW_TIMEOUT",
    "DEFAULT_LLM_TIMEOUT",
    "DEFAULT_SESSION_TIMEOUT",
    "DEFAULT_RATE_LIMIT_PER_MINUTE",
    "DEFAULT_CONCURRENT_REQUESTS",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RETRY_DELAY",
    "DEFAULT_BACKOFF_FACTOR",
    "MAX_FILE_SIZE_BYTES",
    "MAX_FILES_PER_REQUEST",
    "MAX_TOTAL_CONTENT_SIZE",
    "MAX_FILENAME_LENGTH",
    "MAX_FILE_CONTENT_LENGTH",
    "MIN_COMPLEXITY_THRESHOLD",
    "MAX_COMPLEXITY_THRESHOLD",
    "DEFAULT_COMPLEXITY_THRESHOLD",
    "MAX_CONCURRENT_SESSIONS",
    "SESSION_CLEANUP_INTERVAL",
    "MAX_SESSION_MEMORY_MB",
    "CORRELATION_ID_HEADER",
    "REQUEST_ID_HEADER",
    
    # Enums
    "SupportedLanguage",
    "AnalysisType",
    "AgentType", 
    "AgentStatus",
    "SessionStatus",
    "WorkflowStatus",
    "Priority",
    "Severity",
    "ComplexityMetric",
    "SecurityCategory",
    "EngineeringPracticeCategory",
    "GeminiModel",
    "HTTPMethod",
    "ContentType",
    
    # Mappings
    "LANGUAGE_EXTENSIONS",
    "EXTENSION_TO_LANGUAGE",
    "TREE_SITTER_LANGUAGES",
    "COMPLEXITY_THRESHOLDS",
    "SECURITY_PATTERNS",
    "BAD_PRACTICES_PATTERNS",
    "HTTP_STATUS_CODES",
    "RESPONSE_MESSAGES",
    "ADK_CONFIG_KEYS",
    "GEMINI_MODEL_CONFIGS",
    "LOG_FORMATS",
    "ENV_VARS",
    "DEFAULT_RESPONSE_HEADERS",
]
