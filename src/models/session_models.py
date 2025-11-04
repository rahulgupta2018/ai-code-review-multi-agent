"""
Pydantic models for session management in ADK Multi-Agent Code Review MVP.

This module defines models for session lifecycle, memory management, and 
state tracking for multi-agent analysis workflows.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import StrictStr, StrictInt, StrictFloat, StrictBool

from ..utils.constants import (
    DEFAULT_SESSION_TIMEOUT, SESSION_CLEANUP_INTERVAL, MAX_SESSION_MEMORY_MB,
    WORKFLOW_STATE_PENDING, WORKFLOW_STATE_RUNNING, WORKFLOW_STATE_COMPLETED,
    WORKFLOW_STATE_FAILED, WORKFLOW_STATE_CANCELLED
)


class SessionConfigModel(BaseModel):
    """Model for session configuration."""
    timeout_minutes: StrictInt = Field(default=30, ge=1, le=1440, description="Session timeout in minutes")
    max_memory_mb: StrictInt = Field(default=MAX_SESSION_MEMORY_MB, ge=10, le=2048, description="Maximum memory usage")
    enable_persistence: StrictBool = Field(default=False, description="Enable session persistence")
    cleanup_interval_seconds: StrictInt = Field(default=SESSION_CLEANUP_INTERVAL, ge=60, description="Cleanup interval")
    max_concurrent_sessions: StrictInt = Field(default=MAX_CONCURRENT_SESSIONS, ge=1, le=1000, description="Max concurrent sessions")


class SessionMetadataModel(BaseModel):
    """Model for session metadata."""
    client_id: Optional[StrictStr] = Field(default=None, description="Client identifier")
    user_id: Optional[StrictStr] = Field(default=None, description="User identifier")
    project_id: Optional[StrictStr] = Field(default=None, description="Project identifier")
    tags: Dict[str, StrictStr] = Field(default_factory=dict, description="Custom tags")
    origin: Optional[StrictStr] = Field(default=None, description="Request origin")
    user_agent: Optional[StrictStr] = Field(default=None, description="User agent")
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags dictionary."""
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        for key, value in v.items():
            if len(key) > 50 or len(value) > 200:
                raise ValueError("Tag key/value too long")
        return v


class SessionProgressModel(BaseModel):
    """Model for session progress tracking."""
    total_steps: StrictInt = Field(ge=0, description="Total number of steps")
    completed_steps: StrictInt = Field(ge=0, description="Number of completed steps")
    current_step: Optional[StrictStr] = Field(default=None, description="Current step description")
    progress_percent: StrictFloat = Field(ge=0.0, le=100.0, description="Progress percentage")
    estimated_completion: Optional[datetime] = Field(default=None, description="Estimated completion time")
    
    @root_validator
    def validate_progress(cls, values):
        """Validate progress consistency."""
        total = values.get('total_steps', 0)
        completed = values.get('completed_steps', 0)
        percent = values.get('progress_percent', 0.0)
        
        if completed > total:
            raise ValueError("Completed steps cannot exceed total steps")
        
        if total > 0:
            expected_percent = (completed / total) * 100
            if abs(percent - expected_percent) > 1.0:  # Allow 1% tolerance
                raise ValueError("Progress percentage doesn't match step counts")
        
        return values


class SessionInfoModel(BaseModel):
    """Model for session information."""
    session_id: StrictStr = Field(..., description="Unique session identifier")
    status: SessionStatus = Field(..., description="Current session status")
    correlation_id: StrictStr = Field(..., description="Request correlation identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    
    # Progress tracking
    progress: SessionProgressModel = Field(default_factory=SessionProgressModel, description="Progress information")
    
    # File and analysis info
    files_count: StrictInt = Field(ge=0, description="Number of files in session")
    total_file_size_bytes: StrictInt = Field(ge=0, description="Total size of all files")
    analysis_types: List[str] = Field(default_factory=list, description="Types of analysis requested")
    
    # Agent tracking
    agents_count: StrictInt = Field(ge=0, description="Number of agents involved")
    active_agents: List[AgentType] = Field(default_factory=list, description="Currently active agents")
    
    # Resource usage
    memory_usage_mb: StrictFloat = Field(ge=0.0, description="Current memory usage")
    cpu_time_seconds: StrictFloat = Field(ge=0.0, description="CPU time consumed")
    
    # Metadata
    metadata: SessionMetadataModel = Field(default_factory=SessionMetadataModel, description="Session metadata")
    
    @validator('expires_at')
    def validate_expiration(cls, v, values):
        """Validate expiration time."""
        created_at = values.get('created_at')
        if created_at and v <= created_at:
            raise ValueError("Expiration time must be after creation time")
        return v
    
    @validator('updated_at')
    def validate_update_time(cls, v, values):
        """Validate update time."""
        created_at = values.get('created_at')
        if created_at and v < created_at:
            raise ValueError("Update time cannot be before creation time")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }
        schema_extra = {
            "example": {
                "session_id": "sess-12345-67890-abcdef",
                "status": "active",
                "correlation_id": "req-12345-67890",
                "created_at": "2025-10-16T10:30:00Z",
                "updated_at": "2025-10-16T10:35:00Z",
                "expires_at": "2025-10-16T11:30:00Z",
                "progress": {
                    "total_steps": 3,
                    "completed_steps": 1,
                    "current_step": "Security Analysis",
                    "progress_percent": 33.3
                },
                "files_count": 5,
                "total_file_size_bytes": 25600,
                "analysis_types": ["code_quality", "security"],
                "agents_count": 3,
                "active_agents": ["security_agent"],
                "memory_usage_mb": 125.5,
                "cpu_time_seconds": 15.2
            }
        }


class SessionMemoryModel(BaseModel):
    """Model for session memory data."""
    analysis_context: Dict[str, Any] = Field(default_factory=dict, description="Analysis context data")
    agent_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Agent state data")
    intermediate_results: Dict[str, Any] = Field(default_factory=dict, description="Intermediate analysis results")
    cache_data: Dict[str, Any] = Field(default_factory=dict, description="Cached computation results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Memory usage tracking
    estimated_size_mb: StrictFloat = Field(ge=0.0, description="Estimated memory size")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="Last access timestamp")
    access_count: StrictInt = Field(default=0, ge=0, description="Number of accesses")
    
    @validator('estimated_size_mb')
    def validate_memory_size(cls, v):
        """Validate memory size is within limits."""
        if v > MAX_SESSION_MEMORY_MB:
            raise ValueError(f"Memory usage ({v}MB) exceeds limit ({MAX_SESSION_MEMORY_MB}MB)")
        return v
    
    def increment_access(self) -> None:
        """Increment access count and update timestamp."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


class WorkflowStepModel(BaseModel):
    """Model for individual workflow step."""
    step_id: StrictStr = Field(..., description="Unique step identifier")
    step_name: StrictStr = Field(..., description="Human-readable step name")
    agent_type: AgentType = Field(..., description="Agent type for this step")
    status: AgentStatus = Field(..., description="Step execution status")
    order: StrictInt = Field(ge=0, description="Step execution order")
    
    # Timing information
    started_at: Optional[datetime] = Field(default=None, description="Step start time")
    completed_at: Optional[datetime] = Field(default=None, description="Step completion time")
    execution_time_seconds: Optional[StrictFloat] = Field(default=None, ge=0, description="Execution duration")
    
    # Dependencies
    depends_on: List[StrictStr] = Field(default_factory=list, description="Step dependencies")
    blocks: List[StrictStr] = Field(default_factory=list, description="Steps blocked by this step")
    
    # Status information
    error_message: Optional[StrictStr] = Field(default=None, description="Error message if failed")
    retry_count: StrictInt = Field(default=0, ge=0, description="Number of retry attempts")
    
    # Progress and metadata
    progress_percent: StrictFloat = Field(default=0.0, ge=0.0, le=100.0, description="Step progress")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Step metadata")
    
    @root_validator
    def validate_timing(cls, values):
        """Validate timing consistency."""
        started_at = values.get('started_at')
        completed_at = values.get('completed_at')
        execution_time = values.get('execution_time_seconds')
        
        if started_at and completed_at:
            if completed_at < started_at:
                raise ValueError("Completion time cannot be before start time")
            
            calculated_duration = (completed_at - started_at).total_seconds()
            if execution_time and abs(execution_time - calculated_duration) > 1.0:
                raise ValueError("Execution time doesn't match start/end times")
        
        return values
    
    @validator('progress_percent')
    def validate_progress_with_status(cls, v, values):
        """Validate progress matches status."""
        status = values.get('status')
        if status == AgentStatus.COMPLETED and v < 100.0:
            raise ValueError("Completed step must have 100% progress")
        if status == AgentStatus.IDLE and v > 0.0:
            raise ValueError("Idle step should have 0% progress")
        return v


class WorkflowExecutionModel(BaseModel):
    """Model for workflow execution tracking."""
    workflow_id: StrictStr = Field(..., description="Unique workflow identifier")
    session_id: StrictStr = Field(..., description="Associated session identifier")
    workflow_name: StrictStr = Field(..., description="Workflow name")
    status: WorkflowStatus = Field(..., description="Overall workflow status")
    
    # Workflow steps
    steps: List[WorkflowStepModel] = Field(default_factory=list, description="Workflow steps")
    current_step_index: StrictInt = Field(default=0, ge=0, description="Current step index")
    
    # Timing
    started_at: datetime = Field(..., description="Workflow start time")
    completed_at: Optional[datetime] = Field(default=None, description="Workflow completion time")
    total_execution_time_seconds: Optional[StrictFloat] = Field(default=None, ge=0, description="Total execution time")
    
    # Progress
    overall_progress_percent: StrictFloat = Field(ge=0.0, le=100.0, description="Overall progress percentage")
    
    # Configuration
    max_parallel_steps: StrictInt = Field(default=1, ge=1, le=10, description="Maximum parallel steps")
    timeout_seconds: StrictInt = Field(default=1200, ge=60, description="Workflow timeout")
    
    # Error handling
    error_message: Optional[StrictStr] = Field(default=None, description="Workflow error message")
    failed_step_id: Optional[StrictStr] = Field(default=None, description="ID of failed step")
    
    @validator('steps')
    def validate_step_order(cls, v):
        """Validate step ordering."""
        orders = [step.order for step in v]
        if orders != sorted(orders):
            raise ValueError("Steps must be ordered by order field")
        return v
    
    @validator('current_step_index')
    def validate_current_step(cls, v, values):
        """Validate current step index."""
        steps = values.get('steps', [])
        if v >= len(steps) and steps:
            raise ValueError("Current step index exceeds number of steps")
        return v
    
    @root_validator
    def calculate_overall_progress(cls, values):
        """Calculate overall progress from step progress."""
        steps = values.get('steps', [])
        if not steps:
            values['overall_progress_percent'] = 0.0
            return values
        
        total_progress = sum(step.progress_percent for step in steps)
        values['overall_progress_percent'] = total_progress / len(steps)
        return values


class SessionCreateRequestModel(BaseModel):
    """Model for session creation request."""
    correlation_id: StrictStr = Field(..., description="Request correlation identifier")
    timeout_minutes: Optional[StrictInt] = Field(default=30, ge=1, le=1440, description="Session timeout")
    metadata: Optional[SessionMetadataModel] = Field(default=None, description="Session metadata")
    config: Optional[SessionConfigModel] = Field(default=None, description="Session configuration")


class SessionUpdateRequestModel(BaseModel):
    """Model for session update request."""
    status: Optional[SessionStatus] = Field(default=None, description="New session status")
    progress: Optional[SessionProgressModel] = Field(default=None, description="Progress update")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata updates")
    extend_timeout_minutes: Optional[StrictInt] = Field(default=None, ge=1, le=1440, description="Extend timeout")


class SessionListRequestModel(BaseModel):
    """Model for session list request."""
    status_filter: Optional[List[SessionStatus]] = Field(default=None, description="Filter by status")
    created_after: Optional[datetime] = Field(default=None, description="Filter by creation time")
    created_before: Optional[datetime] = Field(default=None, description="Filter by creation time")
    limit: StrictInt = Field(default=50, ge=1, le=1000, description="Maximum results")
    offset: StrictInt = Field(default=0, ge=0, description="Result offset")
    sort_by: Optional[StrictStr] = Field(default="created_at", description="Sort field")
    sort_order: Optional[StrictStr] = Field(default="desc", regex="^(asc|desc)$", description="Sort order")


class SessionListResponseModel(BaseModel):
    """Model for session list response."""
    sessions: List[SessionInfoModel] = Field(..., description="List of sessions")
    total_count: StrictInt = Field(ge=0, description="Total number of sessions")
    limit: StrictInt = Field(ge=1, description="Result limit")
    offset: StrictInt = Field(ge=0, description="Result offset")
    has_more: StrictBool = Field(..., description="Whether more results are available")


# Export all models
__all__ = [
    # Configuration models
    "SessionConfigModel",
    "SessionMetadataModel",
    
    # Core session models
    "SessionProgressModel",
    "SessionInfoModel", 
    "SessionMemoryModel",
    
    # Workflow models
    "WorkflowStepModel",
    "WorkflowExecutionModel",
    
    # Request/Response models
    "SessionCreateRequestModel",
    "SessionUpdateRequestModel",
    "SessionListRequestModel",
    "SessionListResponseModel",
]
