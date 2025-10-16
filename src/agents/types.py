"""
Type definitions for Agent components.

This module provides type definitions specific to agent operations,
including agent configurations, results, workflows, and sessions.
"""

from typing import Any, Dict, Optional, List, TypedDict
from enum import Enum

from ..common import AgentID, SessionID, WorkflowID, Timestamp, CorrelationID


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