"""
Type definitions for ADK Multi-Agent Code Review MVP.

This module provides comprehensive type definitions for better type safety,
IDE support, and code documentation throughout the application.
"""

from typing import (
    Any, Dict, List, Optional, Union, Tuple, Callable, Awaitable,
    TypeVar, Generic, Protocol, runtime_checkable, TypedDict, Literal
)
from datetime import datetime
from pathlib import Path
import uuid

from .constants import (
    SupportedLanguage, AnalysisType, AgentType, AgentStatus,
    SessionStatus, WorkflowStatus, Priority, Severity,
    ComplexityMetric, SecurityCategory, EngineeringPracticeCategory
)

# Basic type aliases
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


# Configuration Types
class EnvironmentConfig(TypedDict, total=False):
    """Environment-specific configuration."""
    debug: bool
    log_level: str
    database_url: str
    redis_url: Optional[str]
    api_keys: List[str]


class ModelConfig(TypedDict):
    """LLM model configuration."""
    name: str
    temperature: float
    max_tokens: int
    timeout_seconds: int
    api_key: str


class AgentConfig(TypedDict):
    """Agent configuration."""
    name: str
    agent_type: AgentType
    model_config: ModelConfig
    timeout_seconds: int
    max_retries: int
    tools: List[str]


# File and Content Types
class CodeFile(TypedDict):
    """Represents a code file for analysis."""
    filename: str
    language: SupportedLanguage
    content: str
    size_bytes: int
    encoding: str


class FileMetadata(TypedDict):
    """Metadata about a code file."""
    filename: str
    language: SupportedLanguage
    size_bytes: int
    lines_count: int
    encoding: str
    last_modified: Optional[Timestamp]
    checksum: Optional[str]


# Analysis Types
class ComplexityMetrics(TypedDict):
    """Code complexity metrics."""
    cyclomatic: int
    cognitive: int
    halstead_volume: Optional[float]
    halstead_difficulty: Optional[float]
    maintainability_index: Optional[float]
    lines_of_code: int
    logical_lines: int
    comment_lines: int
    blank_lines: int
    nesting_depth: int


class SecurityFinding(TypedDict):
    """Security vulnerability finding."""
    category: SecurityCategory
    severity: Severity
    title: str
    description: str
    file_path: str
    line_number: int
    column_number: Optional[int]
    code_snippet: str
    recommendation: str
    cwe_id: Optional[str]
    confidence: float


class EngineeringPracticeFinding(TypedDict):
    """Engineering practice finding."""
    category: EngineeringPracticeCategory
    severity: Severity
    title: str
    description: str
    file_path: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    recommendation: str
    impact: str
    effort: str


class QualityFinding(TypedDict):
    """Code quality finding."""
    title: str
    description: str
    severity: Severity
    file_path: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    metrics: ComplexityMetrics
    suggestion: str
    impact: str


# Agent Result Types
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
    findings: List[QualityFinding]
    overall_metrics: ComplexityMetrics
    quality_score: float
    summary: str
    recommendations: List[str]


class SecurityResult(AgentResult):
    """Security agent result."""
    findings: List[SecurityFinding]
    risk_score: float
    summary: str
    critical_issues_count: int
    high_issues_count: int
    recommendations: List[str]


class EngineeringPracticesResult(AgentResult):
    """Engineering practices agent result."""
    findings: List[EngineeringPracticeFinding]
    practice_score: float
    summary: str
    areas_for_improvement: List[str]
    recommendations: List[str]


# Comprehensive Analysis Types
class AnalysisRequest(TypedDict):
    """Request for code analysis."""
    files: List[CodeFile]
    analysis_types: List[AnalysisType]
    options: Dict[str, Any]
    correlation_id: CorrelationID
    priority: Priority


class AnalysisResponse(TypedDict):
    """Response from code analysis."""
    session_id: SessionID
    correlation_id: CorrelationID
    status: WorkflowStatus
    results: Dict[AgentType, Union[CodeQualityResult, SecurityResult, EngineeringPracticesResult]]
    summary: str
    overall_score: float
    execution_time_seconds: float
    timestamp: Timestamp


# Session Types
class SessionInfo(TypedDict):
    """Session information."""
    session_id: SessionID
    status: SessionStatus
    created_at: Timestamp
    updated_at: Timestamp
    expires_at: Timestamp
    correlation_id: CorrelationID
    files_count: int
    agents_count: int
    progress_percent: float


class SessionMemory(TypedDict):
    """Session memory data."""
    analysis_context: Dict[str, Any]
    agent_states: Dict[AgentID, Dict[str, Any]]
    intermediate_results: Dict[str, Any]
    metadata: Dict[str, Any]


# Workflow Types
class WorkflowStep(TypedDict):
    """Individual workflow step."""
    step_id: str
    agent_type: AgentType
    status: AgentStatus
    started_at: Optional[Timestamp]
    completed_at: Optional[Timestamp]
    execution_time_seconds: Optional[float]
    error_message: Optional[str]


class WorkflowExecution(TypedDict):
    """Workflow execution information."""
    workflow_id: WorkflowID
    session_id: SessionID
    status: WorkflowStatus
    steps: List[WorkflowStep]
    started_at: Timestamp
    completed_at: Optional[Timestamp]
    total_execution_time_seconds: Optional[float]


# LLM Types
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


# API Types
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


# Monitoring Types
class PerformanceMetrics(TypedDict):
    """Performance monitoring metrics."""
    request_count: int
    error_count: int
    average_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    active_sessions: int


class HealthStatus(TypedDict):
    """Health check status."""
    status: str
    timestamp: Timestamp
    version: str
    uptime_seconds: float
    dependencies: Dict[str, bool]
    metrics: PerformanceMetrics


# Protocol Types
@runtime_checkable
class Configurable(Protocol):
    """Protocol for configurable components."""
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the component with the given configuration."""
        ...


@runtime_checkable
class Loggable(Protocol):
    """Protocol for components with logging capability."""
    
    def get_logger(self) -> Any:
        """Get the logger instance."""
        ...


@runtime_checkable
class Monitorable(Protocol):
    """Protocol for monitorable components."""
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get performance metrics."""
        ...
    
    def get_health_status(self) -> HealthStatus:
        """Get health status."""
        ...


@runtime_checkable
class AsyncAnalyzer(Protocol):
    """Protocol for asynchronous analyzers."""
    
    async def analyze(
        self,
        files: List[CodeFile],
        options: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """Perform asynchronous analysis."""
        ...


@runtime_checkable
class SessionManager(Protocol):
    """Protocol for session management."""
    
    async def create_session(self, correlation_id: CorrelationID) -> SessionID:
        """Create a new session."""
        ...
    
    async def get_session(self, session_id: SessionID) -> Optional[SessionInfo]:
        """Get session information."""
        ...
    
    async def update_session(self, session_id: SessionID, updates: Dict[str, Any]) -> None:
        """Update session information."""
        ...
    
    async def delete_session(self, session_id: SessionID) -> None:
        """Delete a session."""
        ...


# Function Types
ConfigValidator = Callable[[Dict[str, Any]], bool]
ErrorHandler = Callable[[Exception, Dict[str, Any]], None]
MiddlewareFunction = Callable[[APIRequest], Awaitable[APIRequest]]
ResponseFormatter = Callable[[Any], APIResponse]

# Generic Response Types
class Result(Generic[T]):
    """Generic result type for operations that can succeed or fail."""
    
    def __init__(self, value: Optional[T] = None, error: Optional[Exception] = None):
        self._value = value
        self._error = error
    
    @property
    def is_success(self) -> bool:
        """Check if the result is successful."""
        return self._error is None
    
    @property
    def is_error(self) -> bool:
        """Check if the result is an error."""
        return self._error is not None
    
    @property
    def value(self) -> T:
        """Get the value (raises if error)."""
        if self._error:
            raise self._error
        if self._value is None:
            raise ValueError("Result has no value")
        return self._value
    
    @property
    def error(self) -> Optional[Exception]:
        """Get the error."""
        return self._error
    
    def unwrap_or(self, default: T) -> T:
        """Get the value or return default if error."""
        return self._value if self.is_success and self._value is not None else default


class AsyncResult(Generic[T]):
    """Async result type for operations that can succeed or fail."""
    
    def __init__(self, awaitable: Awaitable[Result[T]]):
        self._awaitable = awaitable
    
    async def get(self) -> Result[T]:
        """Get the result."""
        return await self._awaitable


# Cache Types
CacheKey = str
CacheValue = JSONType
CacheTTL = int

class CacheEntry(TypedDict):
    """Cache entry with metadata."""
    value: CacheValue
    created_at: Timestamp
    expires_at: Timestamp
    access_count: int
    last_accessed: Timestamp


# Pagination Types
class PaginationParams(TypedDict):
    """Pagination parameters."""
    page: int
    page_size: int
    sort_by: Optional[str]
    sort_order: Literal["asc", "desc"]


class PaginatedResponse(Generic[T], TypedDict):
    """Paginated response."""
    items: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


# Validation Types
ValidationRule = Callable[[Any], bool]
ValidationResult = Tuple[bool, Optional[str]]

class ValidationSchema(TypedDict):
    """Validation schema definition."""
    required_fields: List[str]
    optional_fields: List[str]
    field_types: Dict[str, type]
    field_validators: Dict[str, List[ValidationRule]]
    custom_validators: List[Callable[[Dict[str, Any]], ValidationResult]]


# Export all types
__all__ = [
    # Basic types
    "CorrelationID",
    "SessionID", 
    "AgentID",
    "WorkflowID",
    "RequestID",
    "Timestamp",
    "FilePath",
    "JSONType",
    "T", "K", "V",
    
    # Configuration types
    "EnvironmentConfig",
    "ModelConfig",
    "AgentConfig",
    
    # File types
    "CodeFile",
    "FileMetadata",
    
    # Analysis types
    "ComplexityMetrics",
    "SecurityFinding",
    "EngineeringPracticeFinding",
    "QualityFinding",
    
    # Result types
    "AgentResult",
    "CodeQualityResult",
    "SecurityResult", 
    "EngineeringPracticesResult",
    "AnalysisRequest",
    "AnalysisResponse",
    
    # Session types
    "SessionInfo",
    "SessionMemory",
    
    # Workflow types
    "WorkflowStep",
    "WorkflowExecution",
    
    # LLM types
    "LLMRequest",
    "LLMResponse",
    
    # API types
    "APIRequest",
    "APIResponse",
    "ErrorResponse",
    
    # Monitoring types
    "PerformanceMetrics",
    "HealthStatus",
    
    # Protocol types
    "Configurable",
    "Loggable", 
    "Monitorable",
    "AsyncAnalyzer",
    "SessionManager",
    
    # Function types
    "ConfigValidator",
    "ErrorHandler",
    "MiddlewareFunction",
    "ResponseFormatter",
    
    # Generic types
    "Result",
    "AsyncResult",
    
    # Cache types
    "CacheKey",
    "CacheValue",
    "CacheTTL",
    "CacheEntry",
    
    # Pagination types
    "PaginationParams",
    "PaginatedResponse",
    
    # Validation types
    "ValidationRule",
    "ValidationResult",
    "ValidationSchema",
]
