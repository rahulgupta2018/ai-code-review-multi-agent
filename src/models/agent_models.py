"""
Pydantic models for agent management in ADK Multi-Agent Code Review MVP.

This module defines models for agent configuration, state management, and 
communication for multi-agent analysis coordination.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Literal
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import StrictStr, StrictInt, StrictFloat, StrictBool

from ..agents.types import AgentType, AgentStatus, Priority
from ..agents.constants import DEFAULT_AGENT_TIMEOUT, DEFAULT_RETRY_ATTEMPTS

# TODO: Move GeminiModel to LLM module
class GeminiModel(Enum):
    """Gemini model types."""
    FLASH = "gemini-1.5-flash"
    PRO = "gemini-1.5-pro"

DEFAULT_MAX_RETRIES = DEFAULT_RETRY_ATTEMPTS


class AgentCapabilityModel(BaseModel):
    """Model for agent capabilities."""
    name: StrictStr = Field(..., description="Capability name")
    description: StrictStr = Field(..., description="Capability description")
    supported_languages: List[StrictStr] = Field(..., description="Supported programming languages")
    complexity_score: StrictFloat = Field(ge=0.0, le=1.0, description="Complexity handling capability")
    accuracy_score: StrictFloat = Field(ge=0.0, le=1.0, description="Expected accuracy")
    performance_tier: Literal["fast", "balanced", "thorough"] = Field(..., description="Performance tier")


class AgentModelConfigModel(BaseModel):
    """Model for agent LLM configuration."""
    primary_model: GeminiModel = Field(..., description="Primary LLM model")
    fallback_model: Optional[GeminiModel] = Field(default=None, description="Fallback model")
    temperature: StrictFloat = Field(default=0.1, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: StrictInt = Field(default=8192, ge=100, le=32768, description="Maximum output tokens")
    timeout_seconds: StrictInt = Field(default=120, ge=10, le=600, description="Model timeout")
    
    # Cost optimization
    max_cost_per_request: StrictFloat = Field(default=0.10, ge=0.0, description="Maximum cost per request")
    enable_caching: StrictBool = Field(default=True, description="Enable response caching")
    cache_ttl_minutes: StrictInt = Field(default=60, ge=1, le=1440, description="Cache TTL in minutes")


class AgentToolConfigModel(BaseModel):
    """Model for agent tool configuration."""
    tool_name: StrictStr = Field(..., description="Tool identifier")
    enabled: StrictBool = Field(default=True, description="Whether tool is enabled")
    config: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific configuration")
    timeout_seconds: StrictInt = Field(default=30, ge=1, le=300, description="Tool execution timeout")
    max_retries: StrictInt = Field(default=2, ge=0, le=5, description="Maximum retry attempts")
    
    @validator('tool_name')
    def validate_tool_name(cls, v):
        """Validate tool name format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Tool name must be alphanumeric with underscores/hyphens")
        return v


class AgentConfigModel(BaseModel):
    """Model for agent configuration."""
    agent_id: StrictStr = Field(..., description="Unique agent identifier")
    agent_type: AgentType = Field(..., description="Agent type")
    name: StrictStr = Field(..., description="Human-readable agent name")
    description: StrictStr = Field(..., description="Agent description")
    version: StrictStr = Field(..., description="Agent version")
    
    # Capabilities
    capabilities: List[AgentCapabilityModel] = Field(..., description="Agent capabilities")
    
    # Model configuration
    model_config: AgentModelConfigModel = Field(..., description="LLM configuration")
    
    # Tool configuration
    tools: List[AgentToolConfigModel] = Field(default_factory=list, description="Available tools")
    
    # Execution configuration
    timeout_seconds: StrictInt = Field(default=DEFAULT_AGENT_TIMEOUT, ge=30, le=1800, description="Execution timeout")
    max_retries: StrictInt = Field(default=DEFAULT_MAX_RETRIES, ge=0, le=10, description="Maximum retry attempts")
    retry_delay_seconds: StrictFloat = Field(default=1.0, ge=0.1, le=60.0, description="Retry delay")
    
    # Resource limits
    max_memory_mb: StrictInt = Field(default=512, ge=64, le=2048, description="Maximum memory usage")
    max_cpu_seconds: StrictInt = Field(default=300, ge=10, le=1800, description="Maximum CPU time")
    
    # Priority and scheduling
    priority: Priority = Field(default=Priority.MEDIUM, description="Agent priority")
    max_concurrent_executions: StrictInt = Field(default=3, ge=1, le=10, description="Max concurrent executions")
    
    # Monitoring
    enable_detailed_logging: StrictBool = Field(default=True, description="Enable detailed logging")
    enable_performance_tracking: StrictBool = Field(default=True, description="Enable performance tracking")
    
    @validator('agent_id')
    def validate_agent_id(cls, v):
        """Validate agent ID format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Agent ID must be alphanumeric with underscores/hyphens")
        return v
    
    @validator('version')
    def validate_version(cls, v):
        """Validate version format."""
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError("Version must be in format x.y.z")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "agent_id": "code_quality_agent_v1",
                "agent_type": "code_quality_agent",
                "name": "Code Quality Analyzer",
                "description": "Analyzes code quality metrics and complexity",
                "version": "1.0.0",
                "capabilities": [
                    {
                        "name": "complexity_analysis",
                        "description": "Analyzes code complexity metrics",
                        "supported_languages": ["python", "javascript", "typescript"],
                        "complexity_score": 0.9,
                        "accuracy_score": 0.85,
                        "performance_tier": "balanced"
                    }
                ],
                "model_config": {
                    "primary_model": "gemini-1.5-pro",
                    "temperature": 0.1,
                    "max_tokens": 4096,
                    "timeout_seconds": 120
                },
                "tools": [
                    {
                        "tool_name": "tree_sitter_parser",
                        "enabled": True,
                        "config": {"enable_caching": True},
                        "timeout_seconds": 30
                    }
                ]
            }
        }


class AgentStateModel(BaseModel):
    """Model for agent runtime state."""
    agent_id: StrictStr = Field(..., description="Agent identifier")
    status: AgentStatus = Field(..., description="Current agent status")
    session_id: Optional[StrictStr] = Field(default=None, description="Associated session ID")
    
    # Execution tracking
    current_task_id: Optional[StrictStr] = Field(default=None, description="Current task identifier")
    started_at: Optional[datetime] = Field(default=None, description="Task start time")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    
    # Progress tracking
    progress_percent: StrictFloat = Field(default=0.0, ge=0.0, le=100.0, description="Task progress")
    current_step: Optional[StrictStr] = Field(default=None, description="Current processing step")
    
    # Resource usage
    memory_usage_mb: StrictFloat = Field(default=0.0, ge=0.0, description="Current memory usage")
    cpu_time_seconds: StrictFloat = Field(default=0.0, ge=0.0, description="CPU time consumed")
    
    # Performance metrics
    requests_processed: StrictInt = Field(default=0, ge=0, description="Number of requests processed")
    average_response_time_seconds: StrictFloat = Field(default=0.0, ge=0.0, description="Average response time")
    error_count: StrictInt = Field(default=0, ge=0, description="Number of errors encountered")
    
    # Context and metadata
    context: Dict[str, Any] = Field(default_factory=dict, description="Agent context data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Health status
    health_score: StrictFloat = Field(default=1.0, ge=0.0, le=1.0, description="Agent health score")
    last_error: Optional[StrictStr] = Field(default=None, description="Last error message")
    
    @validator('progress_percent')
    def validate_progress_with_status(cls, v, values):
        """Validate progress matches status."""
        status = values.get('status')
        if status == AgentStatus.COMPLETED and v < 100.0:
            raise ValueError("Completed agent must have 100% progress")
        if status == AgentStatus.IDLE and v > 0.0:
            v = 0.0  # Reset idle agent progress
        return v


class AgentExecutionContextModel(BaseModel):
    """Model for agent execution context."""
    session_id: StrictStr = Field(..., description="Session identifier")
    correlation_id: StrictStr = Field(..., description="Request correlation ID")
    task_id: StrictStr = Field(..., description="Task identifier")
    
    # Input data
    files: List[Dict[str, Any]] = Field(..., description="Files to process")
    analysis_options: Dict[str, Any] = Field(default_factory=dict, description="Analysis options")
    
    # Execution parameters
    timeout_seconds: StrictInt = Field(default=DEFAULT_AGENT_TIMEOUT, description="Execution timeout")
    priority: Priority = Field(default=Priority.MEDIUM, description="Task priority")
    
    # Dependencies
    depends_on: List[StrictStr] = Field(default_factory=list, description="Dependent agent results")
    provides_for: List[StrictStr] = Field(default_factory=list, description="Agents depending on this result")
    
    # Callbacks and notifications
    callback_url: Optional[StrictStr] = Field(default=None, description="Result callback URL")
    notification_config: Dict[str, Any] = Field(default_factory=dict, description="Notification configuration")


class AgentResultModel(BaseModel):
    """Model for agent execution result."""
    agent_id: StrictStr = Field(..., description="Agent identifier")
    task_id: StrictStr = Field(..., description="Task identifier")
    session_id: StrictStr = Field(..., description="Session identifier")
    status: AgentStatus = Field(..., description="Execution status")
    
    # Timing information
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: Optional[datetime] = Field(default=None, description="Execution completion time")
    execution_time_seconds: StrictFloat = Field(ge=0.0, description="Total execution time")
    
    # Results
    results: Dict[str, Any] = Field(default_factory=dict, description="Agent results")
    findings_count: StrictInt = Field(default=0, ge=0, description="Number of findings")
    score: Optional[StrictFloat] = Field(default=None, ge=0.0, le=100.0, description="Overall score")
    
    # Performance metrics
    model_requests: StrictInt = Field(default=0, ge=0, description="Number of model requests")
    tool_invocations: StrictInt = Field(default=0, ge=0, description="Number of tool invocations")
    cache_hits: StrictInt = Field(default=0, ge=0, description="Number of cache hits")
    
    # Resource usage
    memory_peak_mb: StrictFloat = Field(default=0.0, ge=0.0, description="Peak memory usage")
    cpu_time_seconds: StrictFloat = Field(default=0.0, ge=0.0, description="CPU time used")
    cost_usd: Optional[StrictFloat] = Field(default=None, ge=0.0, description="Execution cost")
    
    # Error handling
    error_message: Optional[StrictStr] = Field(default=None, description="Error message if failed")
    retry_count: StrictInt = Field(default=0, ge=0, description="Number of retries performed")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @root_validator
    def validate_completion(cls, values):
        """Validate completion consistency."""
        status = values.get('status')
        completed_at = values.get('completed_at')
        execution_time = values.get('execution_time_seconds', 0.0)
        
        if status in [AgentStatus.COMPLETED, AgentStatus.FAILED] and not completed_at:
            raise ValueError("Completed or failed agents must have completion time")
        
        if completed_at and execution_time <= 0:
            started_at = values.get('started_at')
            if started_at:
                calculated_time = (completed_at - started_at).total_seconds()
                values['execution_time_seconds'] = max(0.1, calculated_time)
        
        return values


class AgentRegistryEntryModel(BaseModel):
    """Model for agent registry entry."""
    agent_id: StrictStr = Field(..., description="Agent identifier")
    agent_type: AgentType = Field(..., description="Agent type")
    config: AgentConfigModel = Field(..., description="Agent configuration")
    state: AgentStateModel = Field(..., description="Current agent state")
    
    # Registration info
    registered_at: datetime = Field(default_factory=datetime.utcnow, description="Registration timestamp")
    last_seen: datetime = Field(default_factory=datetime.utcnow, description="Last seen timestamp")
    
    # Health and availability
    is_available: StrictBool = Field(default=True, description="Whether agent is available")
    health_check_url: Optional[StrictStr] = Field(default=None, description="Health check endpoint")
    
    # Scheduling info
    current_load: StrictFloat = Field(default=0.0, ge=0.0, le=1.0, description="Current load factor")
    queue_length: StrictInt = Field(default=0, ge=0, description="Current queue length")
    
    def update_last_seen(self) -> None:
        """Update last seen timestamp."""
        self.last_seen = datetime.utcnow()
    
    def is_healthy(self) -> bool:
        """Check if agent is healthy."""
        time_threshold = datetime.utcnow() - timedelta(minutes=5)
        return (
            self.is_available and
            self.last_seen > time_threshold and
            self.state.health_score > 0.5
        )


class AgentMessageModel(BaseModel):
    """Model for inter-agent communication."""
    message_id: StrictStr = Field(..., description="Unique message identifier")
    from_agent: StrictStr = Field(..., description="Sender agent ID")
    to_agent: StrictStr = Field(..., description="Recipient agent ID")
    message_type: StrictStr = Field(..., description="Message type")
    
    # Content
    payload: Dict[str, Any] = Field(..., description="Message payload")
    priority: Priority = Field(default=Priority.MEDIUM, description="Message priority")
    
    # Routing
    session_id: Optional[StrictStr] = Field(default=None, description="Associated session")
    correlation_id: Optional[StrictStr] = Field(default=None, description="Request correlation ID")
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Message creation time")
    expires_at: Optional[datetime] = Field(default=None, description="Message expiration time")
    
    # Delivery tracking
    delivered_at: Optional[datetime] = Field(default=None, description="Delivery timestamp")
    acknowledged_at: Optional[datetime] = Field(default=None, description="Acknowledgment timestamp")
    retry_count: StrictInt = Field(default=0, ge=0, description="Delivery retry count")
    
    @validator('expires_at')
    def validate_expiration(cls, v, values):
        """Validate expiration time."""
        created_at = values.get('created_at')
        if v and created_at and v <= created_at:
            raise ValueError("Expiration time must be after creation time")
        return v


# Request/Response Models
class AgentExecutionRequestModel(BaseModel):
    """Model for agent execution request."""
    agent_id: StrictStr = Field(..., description="Target agent identifier")
    context: AgentExecutionContextModel = Field(..., description="Execution context")
    priority: Priority = Field(default=Priority.MEDIUM, description="Request priority")
    timeout_seconds: Optional[StrictInt] = Field(default=None, description="Custom timeout")


class AgentListRequestModel(BaseModel):
    """Model for agent list request."""
    agent_types: Optional[List[AgentType]] = Field(default=None, description="Filter by agent types")
    status_filter: Optional[List[AgentStatus]] = Field(default=None, description="Filter by status")
    available_only: StrictBool = Field(default=False, description="Only available agents")
    include_config: StrictBool = Field(default=False, description="Include configuration")
    include_state: StrictBool = Field(default=True, description="Include current state")


class AgentListResponseModel(BaseModel):
    """Model for agent list response."""
    agents: List[AgentRegistryEntryModel] = Field(..., description="List of agents")
    total_count: StrictInt = Field(ge=0, description="Total number of agents")
    available_count: StrictInt = Field(ge=0, description="Number of available agents")


# Export all models
__all__ = [
    # Configuration models
    "AgentCapabilityModel",
    "AgentModelConfigModel",
    "AgentToolConfigModel",
    "AgentConfigModel",
    
    # State models
    "AgentStateModel",
    "AgentExecutionContextModel",
    "AgentResultModel",
    
    # Registry models
    "AgentRegistryEntryModel",
    "AgentMessageModel",
    
    # Request/Response models
    "AgentExecutionRequestModel",
    "AgentListRequestModel",
    "AgentListResponseModel",
]
