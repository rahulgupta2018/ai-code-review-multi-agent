"""
Pydantic models for workflow management in ADK Multi-Agent Code Review MVP.

This module defines models for workflow orchestration, step management, and
execution tracking for coordinated multi-agent analysis.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Set
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import StrictStr, StrictInt, StrictFloat, StrictBool

from ..core.constants import (
    WorkflowType, WorkflowStatus, StepStatus, Priority,
    DEFAULT_WORKFLOW_TIMEOUT, DEFAULT_MAX_WORKFLOW_RETRIES
)


class WorkflowStepConditionModel(BaseModel):
    """Model for workflow step execution conditions."""
    condition_type: Literal["always", "on_success", "on_failure", "conditional"] = Field(..., description="Condition type")
    expression: Optional[StrictStr] = Field(default=None, description="Conditional expression")
    depends_on: List[StrictStr] = Field(default_factory=list, description="Dependencies")
    timeout_seconds: Optional[StrictInt] = Field(default=None, description="Step timeout override")
    
    @validator('expression')
    def validate_conditional_expression(cls, v, values):
        """Validate conditional expression when needed."""
        condition_type = values.get('condition_type')
        if condition_type == 'conditional' and not v:
            raise ValueError("Conditional steps must have an expression")
        return v


class WorkflowStepModel(BaseModel):
    """Model for individual workflow step."""
    step_id: StrictStr = Field(..., description="Unique step identifier")
    name: StrictStr = Field(..., description="Human-readable step name")
    description: StrictStr = Field(..., description="Step description")
    step_type: Literal["agent", "tool", "decision", "parallel", "sequential"] = Field(..., description="Step type")
    
    # Execution configuration
    agent_id: Optional[StrictStr] = Field(default=None, description="Target agent for agent steps")
    tool_name: Optional[StrictStr] = Field(default=None, description="Tool name for tool steps")
    action: StrictStr = Field(..., description="Action to perform")
    
    # Input/Output mapping
    input_mapping: Dict[str, str] = Field(default_factory=dict, description="Input parameter mapping")
    output_mapping: Dict[str, str] = Field(default_factory=dict, description="Output result mapping")
    
    # Execution conditions
    conditions: WorkflowStepConditionModel = Field(..., description="Execution conditions")
    
    # Retry configuration
    max_retries: StrictInt = Field(default=2, ge=0, le=10, description="Maximum retry attempts")
    retry_delay_seconds: StrictFloat = Field(default=1.0, ge=0.1, le=60.0, description="Retry delay")
    retry_backoff_multiplier: StrictFloat = Field(default=2.0, ge=1.0, le=5.0, description="Backoff multiplier")
    
    # Timeouts
    timeout_seconds: StrictInt = Field(default=300, ge=30, le=3600, description="Step timeout")
    
    # Priority and resource management
    priority: Priority = Field(default=Priority.MEDIUM, description="Step priority")
    resource_requirements: Dict[str, Any] = Field(default_factory=dict, description="Resource requirements")
    
    # Metadata
    tags: List[StrictStr] = Field(default_factory=list, description="Step tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('step_id')
    def validate_step_id(cls, v):
        """Validate step ID format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Step ID must be alphanumeric with underscores/hyphens")
        return v
    
    @root_validator
    def validate_step_configuration(cls, values):
        """Validate step configuration consistency."""
        step_type = values.get('step_type')
        agent_id = values.get('agent_id')
        tool_name = values.get('tool_name')
        
        if step_type == 'agent' and not agent_id:
            raise ValueError("Agent steps must specify agent_id")
        if step_type == 'tool' and not tool_name:
            raise ValueError("Tool steps must specify tool_name")
        
        return values


class WorkflowDefinitionModel(BaseModel):
    """Model for workflow definition."""
    workflow_id: StrictStr = Field(..., description="Unique workflow identifier")
    name: StrictStr = Field(..., description="Human-readable workflow name")
    description: StrictStr = Field(..., description="Workflow description")
    version: StrictStr = Field(..., description="Workflow version")
    workflow_type: WorkflowType = Field(..., description="Workflow type")
    
    # Steps and structure
    steps: List[WorkflowStepModel] = Field(..., description="Workflow steps")
    start_step: StrictStr = Field(..., description="Starting step ID")
    
    # Configuration
    timeout_seconds: StrictInt = Field(default=DEFAULT_WORKFLOW_TIMEOUT, ge=60, le=7200, description="Workflow timeout")
    max_retries: StrictInt = Field(default=DEFAULT_MAX_WORKFLOW_RETRIES, ge=0, le=5, description="Maximum workflow retries")
    
    # Resource management
    max_parallel_steps: StrictInt = Field(default=5, ge=1, le=20, description="Maximum parallel steps")
    resource_limits: Dict[str, Any] = Field(default_factory=dict, description="Resource limits")
    
    # Error handling
    error_handling_strategy: Literal["fail_fast", "continue_on_error", "retry_failed"] = Field(
        default="fail_fast", description="Error handling strategy"
    )
    fallback_workflow: Optional[StrictStr] = Field(default=None, description="Fallback workflow ID")
    
    # Input/Output schema
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="Input schema definition")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="Output schema definition")
    
    # Metadata
    tags: List[StrictStr] = Field(default_factory=list, description="Workflow tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Versioning
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    created_by: StrictStr = Field(..., description="Creator identifier")
    is_active: StrictBool = Field(default=True, description="Whether workflow is active")
    
    @validator('workflow_id')
    def validate_workflow_id(cls, v):
        """Validate workflow ID format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Workflow ID must be alphanumeric with underscores/hyphens")
        return v
    
    @validator('version')
    def validate_version(cls, v):
        """Validate version format."""
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError("Version must be in format x.y.z")
        return v
    
    @validator('start_step')
    def validate_start_step(cls, v, values):
        """Validate start step exists."""
        steps = values.get('steps', [])
        step_ids = {step.step_id for step in steps}
        if v not in step_ids:
            raise ValueError(f"Start step '{v}' not found in workflow steps")
        return v
    
    def get_step(self, step_id: str) -> Optional[WorkflowStepModel]:
        """Get step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def validate_dependencies(self) -> List[str]:
        """Validate step dependencies and return any errors."""
        errors = []
        step_ids = {step.step_id for step in self.steps}
        
        for step in self.steps:
            for dep in step.conditions.depends_on:
                if dep not in step_ids:
                    errors.append(f"Step '{step.step_id}' depends on non-existent step '{dep}'")
        
        return errors


class WorkflowStepExecutionModel(BaseModel):
    """Model for workflow step execution state."""
    step_id: StrictStr = Field(..., description="Step identifier")
    execution_id: StrictStr = Field(..., description="Unique execution identifier")
    status: StepStatus = Field(..., description="Step execution status")
    
    # Timing
    started_at: Optional[datetime] = Field(default=None, description="Execution start time")
    completed_at: Optional[datetime] = Field(default=None, description="Execution completion time")
    execution_time_seconds: StrictFloat = Field(default=0.0, ge=0.0, description="Execution duration")
    
    # Retry tracking
    attempt_number: StrictInt = Field(default=1, ge=1, description="Current attempt number")
    retry_count: StrictInt = Field(default=0, ge=0, description="Number of retries performed")
    next_retry_at: Optional[datetime] = Field(default=None, description="Next retry time")
    
    # Input/Output
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Step input data")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="Step output data")
    
    # Agent/Tool execution
    agent_execution_id: Optional[StrictStr] = Field(default=None, description="Agent execution ID")
    tool_execution_id: Optional[StrictStr] = Field(default=None, description="Tool execution ID")
    
    # Error handling
    error_message: Optional[StrictStr] = Field(default=None, description="Error message if failed")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed error information")
    
    # Performance metrics
    cpu_time_seconds: StrictFloat = Field(default=0.0, ge=0.0, description="CPU time used")
    memory_peak_mb: StrictFloat = Field(default=0.0, ge=0.0, description="Peak memory usage")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata")
    
    @root_validator
    def validate_timing_consistency(cls, values):
        """Validate timing consistency."""
        status = values.get('status')
        started_at = values.get('started_at')
        completed_at = values.get('completed_at')
        execution_time = values.get('execution_time_seconds', 0.0)
        
        if status in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED] and not completed_at:
            values['completed_at'] = datetime.utcnow()
        
        if started_at and completed_at and execution_time <= 0:
            calculated_time = (completed_at - started_at).total_seconds()
            values['execution_time_seconds'] = max(0.1, calculated_time)
        
        return values


class WorkflowExecutionModel(BaseModel):
    """Model for workflow execution state."""
    execution_id: StrictStr = Field(..., description="Unique execution identifier")
    workflow_id: StrictStr = Field(..., description="Workflow identifier")
    session_id: StrictStr = Field(..., description="Associated session ID")
    status: WorkflowStatus = Field(..., description="Workflow execution status")
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Execution start time")
    completed_at: Optional[datetime] = Field(default=None, description="Execution completion time")
    execution_time_seconds: StrictFloat = Field(default=0.0, ge=0.0, description="Total execution time")
    
    # Progress tracking
    current_step: Optional[StrictStr] = Field(default=None, description="Currently executing step")
    completed_steps: List[StrictStr] = Field(default_factory=list, description="Completed step IDs")
    failed_steps: List[StrictStr] = Field(default_factory=list, description="Failed step IDs")
    skipped_steps: List[StrictStr] = Field(default_factory=list, description="Skipped step IDs")
    
    # Step executions
    step_executions: Dict[str, WorkflowStepExecutionModel] = Field(
        default_factory=dict, description="Step execution details"
    )
    
    # Input/Output
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Workflow input data")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="Workflow output data")
    
    # Retry tracking
    retry_count: StrictInt = Field(default=0, ge=0, description="Workflow retry count")
    last_retry_at: Optional[datetime] = Field(default=None, description="Last retry timestamp")
    
    # Error handling
    error_message: Optional[StrictStr] = Field(default=None, description="Error message if failed")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed error information")
    
    # Performance metrics
    total_steps: StrictInt = Field(default=0, ge=0, description="Total number of steps")
    parallel_execution_count: StrictInt = Field(default=0, ge=0, description="Parallel executions")
    resource_usage: Dict[str, Any] = Field(default_factory=dict, description="Resource usage metrics")
    
    # Metadata
    priority: Priority = Field(default=Priority.MEDIUM, description="Execution priority")
    correlation_id: Optional[StrictStr] = Field(default=None, description="Request correlation ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata")
    
    def get_step_execution(self, step_id: str) -> Optional[WorkflowStepExecutionModel]:
        """Get step execution by step ID."""
        return self.step_executions.get(step_id)
    
    def add_step_execution(self, step_execution: WorkflowStepExecutionModel) -> None:
        """Add step execution."""
        self.step_executions[step_execution.step_id] = step_execution
    
    def get_progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_steps == 0:
            return 0.0
        completed = len(self.completed_steps) + len(self.skipped_steps)
        return min(100.0, (completed / self.total_steps) * 100.0)
    
    def is_step_ready(self, step: WorkflowStepModel) -> bool:
        """Check if step is ready for execution."""
        for dep in step.conditions.depends_on:
            if dep not in self.completed_steps and dep not in self.skipped_steps:
                return False
        return True


class WorkflowTemplateModel(BaseModel):
    """Model for workflow template."""
    template_id: StrictStr = Field(..., description="Unique template identifier")
    name: StrictStr = Field(..., description="Template name")
    description: StrictStr = Field(..., description="Template description")
    category: StrictStr = Field(..., description="Template category")
    
    # Template definition
    workflow_definition: WorkflowDefinitionModel = Field(..., description="Base workflow definition")
    
    # Customization options
    configurable_parameters: List[Dict[str, Any]] = Field(
        default_factory=list, description="Configurable parameters"
    )
    step_variants: Dict[str, List[WorkflowStepModel]] = Field(
        default_factory=dict, description="Alternative step implementations"
    )
    
    # Usage tracking
    usage_count: StrictInt = Field(default=0, ge=0, description="Number of times used")
    last_used: Optional[datetime] = Field(default=None, description="Last usage timestamp")
    
    # Metadata
    tags: List[StrictStr] = Field(default_factory=list, description="Template tags")
    author: StrictStr = Field(..., description="Template author")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    is_public: StrictBool = Field(default=False, description="Whether template is public")


# Request/Response Models
class WorkflowExecutionRequestModel(BaseModel):
    """Model for workflow execution request."""
    workflow_id: StrictStr = Field(..., description="Workflow to execute")
    session_id: StrictStr = Field(..., description="Associated session ID")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data")
    priority: Priority = Field(default=Priority.MEDIUM, description="Execution priority")
    timeout_seconds: Optional[StrictInt] = Field(default=None, description="Custom timeout")
    correlation_id: Optional[StrictStr] = Field(default=None, description="Request correlation ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Request metadata")


class WorkflowStatusRequestModel(BaseModel):
    """Model for workflow status request."""
    execution_id: StrictStr = Field(..., description="Execution identifier")
    include_step_details: StrictBool = Field(default=True, description="Include step execution details")
    include_performance_metrics: StrictBool = Field(default=False, description="Include performance metrics")


class WorkflowListRequestModel(BaseModel):
    """Model for workflow list request."""
    workflow_type: Optional[WorkflowType] = Field(default=None, description="Filter by workflow type")
    status: Optional[List[WorkflowStatus]] = Field(default=None, description="Filter by status")
    session_id: Optional[StrictStr] = Field(default=None, description="Filter by session")
    limit: StrictInt = Field(default=50, ge=1, le=1000, description="Maximum results")
    offset: StrictInt = Field(default=0, ge=0, description="Result offset")


class WorkflowListResponseModel(BaseModel):
    """Model for workflow list response."""
    executions: List[WorkflowExecutionModel] = Field(..., description="Workflow executions")
    total_count: StrictInt = Field(ge=0, description="Total number of executions")
    has_more: StrictBool = Field(..., description="Whether more results are available")


# Export all models
__all__ = [
    # Definition models
    "WorkflowStepConditionModel",
    "WorkflowStepModel",
    "WorkflowDefinitionModel",
    
    # Execution models
    "WorkflowStepExecutionModel",
    "WorkflowExecutionModel",
    
    # Template models
    "WorkflowTemplateModel",
    
    # Request/Response models
    "WorkflowExecutionRequestModel",
    "WorkflowStatusRequestModel",
    "WorkflowListRequestModel",
    "WorkflowListResponseModel",
]
