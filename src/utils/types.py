"""
Consolidated type definitions for AI Code Review Multi-Agent System.

This module contains all type definitions used across the application,
organized by functional area for better maintainability.
"""

from typing import (
    Any, Dict, List, Optional, Union, Tuple, Callable, Awaitable,
    TypeVar, Generic, Protocol, runtime_checkable, TypedDict
)
from datetime import datetime
from pathlib import Path
from enum import Enum

# =============================================================================
# BASIC TYPE ALIASES (SHARED ACROSS ALL DOMAINS)
# =============================================================================

CorrelationID = str
SessionID = str
AgentID = str
WorkflowID = str
RequestID = str
Timestamp = datetime
FilePath = Union[str, Path]
JSONType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]

# Generic type variables
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

# Configuration dictionary type (used by config modules)
ConfigDict = Dict[str, Any]

# Status type (used across domains)
Status = str

# Generic callback type
CallbackFunction = Callable[..., Any]
AsyncCallbackFunction = Callable[..., Awaitable[Any]]

# Generic result type
Result = Union[T, Exception]

# Validation result type
ValidationResult = Tuple[bool, Optional[str]]


# =============================================================================
# PROTOCOLS
# =============================================================================

@runtime_checkable
class Identifiable(Protocol):
    """Protocol for objects that have an ID."""
    id: str


@runtime_checkable
class Timestamped(Protocol):
    """Protocol for objects that have timestamps."""
    created_at: datetime
    updated_at: Optional[datetime]


# =============================================================================
# BASE DATA STRUCTURES
# =============================================================================

class BaseResponse(Dict[str, Any]):
    """Base response structure for API endpoints."""
    pass


class BaseEvent(Dict[str, Any]):
    """Base event structure for system events."""
    pass


# =============================================================================
# AGENT TYPES
# =============================================================================

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


class SupportedLanguage(Enum):
    """Supported programming languages for analysis."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"


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


class AgentConfig(TypedDict):
    """Agent configuration."""
    agent_id: AgentID
    agent_type: AgentType
    enabled: bool
    priority: int
    timeout_seconds: int
    model_config: Dict[str, Any]


class AgentResult(TypedDict):
    """Base agent analysis result."""
    agent_id: str
    agent_type: AgentType
    status: AgentStatus
    execution_time_seconds: float
    timestamp: Timestamp
    error_message: Optional[str]
    metadata: Dict[str, Any]


class CodeQualityResult(AgentResult):
    """Code quality agent result."""
    findings: List[Dict[str, Any]]  # QualityFinding from analysis module
    overall_metrics: Dict[str, Any]  # ComplexityMetrics from analysis module
    quality_score: float
    summary: str
    recommendations: List[str]


class SecurityResult(AgentResult):
    """Security agent result."""
    findings: List[Dict[str, Any]]  # SecurityFinding from analysis module
    risk_score: float
    summary: str
    critical_issues_count: int
    high_issues_count: int
    recommendations: List[str]


class EngineeringPracticesResult(AgentResult):
    """Engineering practices agent result."""
    findings: List[Dict[str, Any]]  # EngineeringPracticeFinding from analysis module
    practice_score: float
    summary: str
    areas_for_improvement: List[str]
    recommendations: List[str]


class WorkflowExecution(TypedDict):
    """Workflow execution tracking."""
    workflow_id: WorkflowID
    session_id: SessionID
    status: WorkflowStatus
    agents: List[AgentConfig]
    started_at: Timestamp
    completed_at: Optional[Timestamp]
    results: List[AgentResult]
    metadata: Dict[str, Any]


class AgentSession(TypedDict):
    """Agent session information."""
    session_id: SessionID
    correlation_id: CorrelationID
    status: SessionStatus
    created_at: Timestamp
    updated_at: Timestamp
    metadata: Dict[str, Any]


class AgentMetrics(TypedDict):
    """Metrics for agent performance."""
    agent_id: AgentID
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float
    last_execution: Optional[Timestamp]


class WorkflowMetrics(TypedDict):
    """Metrics for workflow performance."""
    workflow_id: WorkflowID
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float
    agent_metrics: List[AgentMetrics]


# =============================================================================
# API TYPES
# =============================================================================

class HTTPMethod(Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class APIRequest(TypedDict):
    """API request data."""
    method: str
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, str]
    body: Optional[JSONType]
    correlation_id: CorrelationID
    timestamp: Timestamp


class APIResponse(TypedDict):
    """API response data."""
    status_code: int
    headers: Dict[str, str]
    body: JSONType
    correlation_id: CorrelationID
    execution_time_seconds: float
    timestamp: Timestamp


class ErrorResponse(TypedDict):
    """Error response format."""
    success: bool
    error: Dict[str, Any]
    correlation_id: CorrelationID
    timestamp: Timestamp


class SuccessResponse(TypedDict):
    """Success response format."""
    success: bool
    data: JSONType
    correlation_id: CorrelationID
    timestamp: Timestamp


class PaginatedResponse(TypedDict):
    """Paginated response format."""
    success: bool
    data: List[JSONType]
    pagination: Dict[str, Any]
    correlation_id: CorrelationID
    timestamp: Timestamp


class ValidationErrorDetail(TypedDict):
    """Validation error detail."""
    field: str
    message: str
    invalid_value: Optional[Any]


class APIMetrics(TypedDict):
    """API performance metrics."""
    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    last_request: Optional[Timestamp]


class RateLimitInfo(TypedDict):
    """Rate limiting information."""
    limit: int
    remaining: int
    reset_time: Timestamp
    window_seconds: int


class RequestContext(TypedDict):
    """Request context information."""
    correlation_id: CorrelationID
    user_id: Optional[str]
    client_ip: str
    user_agent: str
    timestamp: Timestamp
    rate_limit_info: Optional[RateLimitInfo]


# =============================================================================
# LLM TYPES
# =============================================================================

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


# =============================================================================
# VALIDATION TYPES
# =============================================================================

class CodeFile(TypedDict):
    """Code file structure for validation."""
    filename: str
    content: str
    language: SupportedLanguage
    size_bytes: int
    line_count: int
    encoding: str


# Extension to language mapping
EXTENSION_TO_LANGUAGE = {
    ".py": SupportedLanguage.PYTHON,
    ".js": SupportedLanguage.JAVASCRIPT,
    ".ts": SupportedLanguage.TYPESCRIPT,
    ".tsx": SupportedLanguage.TYPESCRIPT,
    ".jsx": SupportedLanguage.JAVASCRIPT,
    ".java": SupportedLanguage.JAVA,
    ".cs": SupportedLanguage.CSHARP,
    ".cpp": SupportedLanguage.CPP,
    ".cc": SupportedLanguage.CPP,
    ".cxx": SupportedLanguage.CPP,
    ".c": SupportedLanguage.CPP,
    ".h": SupportedLanguage.CPP,
    ".hpp": SupportedLanguage.CPP,
    ".go": SupportedLanguage.GO,
    ".rs": SupportedLanguage.RUST,
    ".php": SupportedLanguage.PHP,
    ".rb": SupportedLanguage.RUBY,
}