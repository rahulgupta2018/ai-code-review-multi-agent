"""
Pydantic models for tool management in ADK Multi-Agent Code Review MVP.

This module defines models for tool configuration, execution tracking, and
integration management for external analysis tools.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import StrictStr, StrictInt, StrictFloat, StrictBool

from ..utils.constants import (
    Priority, DEFAULT_RETRY_ATTEMPTS, MAX_TOOL_EXECUTION_TIME
)


class ToolParameterModel(BaseModel):
    """Model for tool parameter definition."""
    name: StrictStr = Field(..., description="Parameter name")
    param_type: StrictStr = Field(..., description="Parameter type")
    description: StrictStr = Field(..., description="Parameter description")
    
    # Validation
    required: StrictBool = Field(default=False, description="Whether parameter is required")
    default_value: Optional[Any] = Field(default=None, description="Default parameter value")
    allowed_values: Optional[List[Any]] = Field(default=None, description="Allowed parameter values")
    min_value: Optional[Union[int, float]] = Field(default=None, description="Minimum value for numeric parameters")
    max_value: Optional[Union[int, float]] = Field(default=None, description="Maximum value for numeric parameters")
    pattern: Optional[StrictStr] = Field(default=None, description="Regex pattern for string parameters")
    
    # UI hints
    display_name: Optional[StrictStr] = Field(default=None, description="Display name for UI")
    help_text: Optional[StrictStr] = Field(default=None, description="Help text for UI")
    category: Optional[StrictStr] = Field(default=None, description="Parameter category")
    
    @validator('param_type')
    def validate_param_type(cls, v):
        """Validate parameter type."""
        valid_types = ['string', 'integer', 'float', 'boolean', 'array', 'object', 'file_path']
        if v not in valid_types:
            raise ValueError(f"Parameter type must be one of: {valid_types}")
        return v


class ToolCapabilityModel(BaseModel):
    """Model for tool capabilities."""
    capability_name: StrictStr = Field(..., description="Capability identifier")
    description: StrictStr = Field(..., description="Capability description")
    supported_languages: List[SupportedLanguage] = Field(..., description="Supported languages")
    
    # Performance characteristics
    accuracy_score: StrictFloat = Field(ge=0.0, le=1.0, description="Expected accuracy")
    performance_tier: StrictStr = Field(..., description="Performance tier")
    resource_intensity: StrictStr = Field(..., description="Resource intensity level")
    
    # Output characteristics
    finding_types: List[StrictStr] = Field(..., description="Types of findings produced")
    metrics_provided: List[StrictStr] = Field(default_factory=list, description="Metrics provided")
    confidence_scoring: StrictBool = Field(default=False, description="Whether tool provides confidence scores")
    
    @validator('performance_tier')
    def validate_performance_tier(cls, v):
        """Validate performance tier."""
        valid_tiers = ['fast', 'balanced', 'thorough', 'comprehensive']
        if v not in valid_tiers:
            raise ValueError(f"Performance tier must be one of: {valid_tiers}")
        return v
    
    @validator('resource_intensity')
    def validate_resource_intensity(cls, v):
        """Validate resource intensity."""
        valid_levels = ['low', 'medium', 'high', 'very_high']
        if v not in valid_levels:
            raise ValueError(f"Resource intensity must be one of: {valid_levels}")
        return v


class ToolConfigModel(BaseModel):
    """Model for tool configuration."""
    tool_id: StrictStr = Field(..., description="Unique tool identifier")
    name: StrictStr = Field(..., description="Human-readable tool name")
    description: StrictStr = Field(..., description="Tool description")
    version: StrictStr = Field(..., description="Tool version")
    tool_type: ToolType = Field(..., description="Tool type category")
    
    # Execution configuration
    executable_path: Optional[StrictStr] = Field(default=None, description="Tool executable path")
    working_directory: Optional[StrictStr] = Field(default=None, description="Working directory")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    
    # Parameters
    parameters: List[ToolParameterModel] = Field(default_factory=list, description="Tool parameters")
    default_parameters: Dict[str, Any] = Field(default_factory=dict, description="Default parameter values")
    
    # Capabilities
    capabilities: List[ToolCapabilityModel] = Field(..., description="Tool capabilities")
    
    # Resource requirements
    min_memory_mb: StrictInt = Field(default=128, ge=64, description="Minimum memory requirement")
    max_memory_mb: StrictInt = Field(default=1024, ge=128, description="Maximum memory usage")
    min_cpu_cores: StrictFloat = Field(default=0.5, ge=0.1, description="Minimum CPU cores")
    max_cpu_cores: StrictFloat = Field(default=2.0, ge=0.1, description="Maximum CPU cores")
    
    # Timeout configuration
    default_timeout_seconds: StrictInt = Field(default=DEFAULT_TOOL_TIMEOUT, ge=10, le=3600, description="Default timeout")
    max_timeout_seconds: StrictInt = Field(default=1800, ge=60, le=7200, description="Maximum allowed timeout")
    
    # Retry configuration
    max_retries: StrictInt = Field(default=DEFAULT_MAX_TOOL_RETRIES, ge=0, le=10, description="Maximum retry attempts")
    retry_delay_seconds: StrictFloat = Field(default=1.0, ge=0.1, le=60.0, description="Retry delay")
    
    # Integration settings
    supports_streaming: StrictBool = Field(default=False, description="Whether tool supports streaming output")
    supports_cancellation: StrictBool = Field(default=True, description="Whether tool supports cancellation")
    requires_isolation: StrictBool = Field(default=False, description="Whether tool requires process isolation")
    
    # Output configuration
    output_format: StrictStr = Field(default="json", description="Expected output format")
    output_parser: Optional[StrictStr] = Field(default=None, description="Custom output parser")
    error_patterns: List[StrictStr] = Field(default_factory=list, description="Error detection patterns")
    
    # Health check
    health_check_command: Optional[StrictStr] = Field(default=None, description="Health check command")
    health_check_interval_seconds: StrictInt = Field(default=300, ge=60, description="Health check interval")
    
    # Metadata
    vendor: Optional[StrictStr] = Field(default=None, description="Tool vendor")
    license: Optional[StrictStr] = Field(default=None, description="Tool license")
    documentation_url: Optional[StrictStr] = Field(default=None, description="Documentation URL")
    tags: List[StrictStr] = Field(default_factory=list, description="Tool tags")
    
    @validator('tool_id')
    def validate_tool_id(cls, v):
        """Validate tool ID format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Tool ID must be alphanumeric with underscores/hyphens")
        return v
    
    @validator('version')
    def validate_version(cls, v):
        """Validate version format."""
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError("Version must be in format x.y.z")
        return v
    
    @validator('output_format')
    def validate_output_format(cls, v):
        """Validate output format."""
        valid_formats = ['json', 'xml', 'text', 'csv', 'yaml']
        if v not in valid_formats:
            raise ValueError(f"Output format must be one of: {valid_formats}")
        return v


class ToolExecutionRequestModel(BaseModel):
    """Model for tool execution request."""
    tool_id: StrictStr = Field(..., description="Tool to execute")
    execution_id: StrictStr = Field(..., description="Unique execution identifier")
    session_id: StrictStr = Field(..., description="Associated session ID")
    correlation_id: Optional[StrictStr] = Field(default=None, description="Request correlation ID")
    
    # Input data
    input_files: List[Dict[str, Any]] = Field(..., description="Input files to process")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    
    # Execution configuration
    timeout_seconds: Optional[StrictInt] = Field(default=None, description="Custom timeout")
    priority: Priority = Field(default=Priority.MEDIUM, description="Execution priority")
    resource_limits: Dict[str, Any] = Field(default_factory=dict, description="Resource limits")
    
    # Output configuration
    output_format: Optional[StrictStr] = Field(default=None, description="Requested output format")
    include_raw_output: StrictBool = Field(default=False, description="Include raw tool output")
    include_performance_metrics: StrictBool = Field(default=True, description="Include performance metrics")
    
    # Callback configuration
    callback_url: Optional[StrictStr] = Field(default=None, description="Result callback URL")
    webhook_config: Dict[str, Any] = Field(default_factory=dict, description="Webhook configuration")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Request metadata")


class ToolExecutionResultModel(BaseModel):
    """Model for tool execution result."""
    execution_id: StrictStr = Field(..., description="Execution identifier")
    tool_id: StrictStr = Field(..., description="Tool identifier")
    session_id: StrictStr = Field(..., description="Session identifier")
    status: ToolStatus = Field(..., description="Execution status")
    
    # Timing information
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: Optional[datetime] = Field(default=None, description="Execution completion time")
    execution_time_seconds: StrictFloat = Field(ge=0.0, description="Total execution time")
    
    # Output data
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="Tool findings")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Analysis metrics")
    raw_output: Optional[StrictStr] = Field(default=None, description="Raw tool output")
    parsed_output: Dict[str, Any] = Field(default_factory=dict, description="Parsed output data")
    
    # Quality metrics
    findings_count: StrictInt = Field(default=0, ge=0, description="Number of findings")
    confidence_score: Optional[StrictFloat] = Field(default=None, ge=0.0, le=1.0, description="Overall confidence")
    quality_score: Optional[StrictFloat] = Field(default=None, ge=0.0, le=100.0, description="Quality score")
    
    # Performance metrics
    cpu_time_seconds: StrictFloat = Field(default=0.0, ge=0.0, description="CPU time used")
    memory_peak_mb: StrictFloat = Field(default=0.0, ge=0.0, description="Peak memory usage")
    disk_io_mb: StrictFloat = Field(default=0.0, ge=0.0, description="Disk I/O volume")
    
    # Error handling
    exit_code: Optional[StrictInt] = Field(default=None, description="Tool exit code")
    error_message: Optional[StrictStr] = Field(default=None, description="Error message if failed")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed error information")
    retry_count: StrictInt = Field(default=0, ge=0, description="Number of retries performed")
    
    # Caching information
    cache_hit: StrictBool = Field(default=False, description="Whether result was cached")
    cache_key: Optional[StrictStr] = Field(default=None, description="Cache key used")
    
    # Metadata
    tool_version: Optional[StrictStr] = Field(default=None, description="Tool version used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Result metadata")
    
    @root_validator
    def validate_completion(cls, values):
        """Validate completion consistency."""
        status = values.get('status')
        completed_at = values.get('completed_at')
        execution_time = values.get('execution_time_seconds', 0.0)
        
        if status in [ToolStatus.COMPLETED, ToolStatus.FAILED] and not completed_at:
            values['completed_at'] = datetime.utcnow()
        
        if completed_at and execution_time <= 0:
            started_at = values.get('started_at')
            if started_at:
                calculated_time = (completed_at - started_at).total_seconds()
                values['execution_time_seconds'] = max(0.1, calculated_time)
        
        return values


class ToolRegistryEntryModel(BaseModel):
    """Model for tool registry entry."""
    tool_id: StrictStr = Field(..., description="Tool identifier")
    config: ToolConfigModel = Field(..., description="Tool configuration")
    
    # Registration info
    registered_at: datetime = Field(default_factory=datetime.utcnow, description="Registration timestamp")
    registered_by: StrictStr = Field(..., description="Registration user/system")
    
    # Status and health
    is_enabled: StrictBool = Field(default=True, description="Whether tool is enabled")
    is_available: StrictBool = Field(default=True, description="Whether tool is available")
    health_status: StrictStr = Field(default="unknown", description="Health check status")
    last_health_check: Optional[datetime] = Field(default=None, description="Last health check time")
    
    # Usage statistics
    total_executions: StrictInt = Field(default=0, ge=0, description="Total number of executions")
    successful_executions: StrictInt = Field(default=0, ge=0, description="Number of successful executions")
    failed_executions: StrictInt = Field(default=0, ge=0, description="Number of failed executions")
    average_execution_time_seconds: StrictFloat = Field(default=0.0, ge=0.0, description="Average execution time")
    
    # Performance metrics
    success_rate: StrictFloat = Field(default=0.0, ge=0.0, le=1.0, description="Success rate")
    average_memory_usage_mb: StrictFloat = Field(default=0.0, ge=0.0, description="Average memory usage")
    average_cpu_usage: StrictFloat = Field(default=0.0, ge=0.0, description="Average CPU usage")
    
    # Scheduling info
    current_executions: StrictInt = Field(default=0, ge=0, description="Current active executions")
    max_concurrent_executions: StrictInt = Field(default=3, ge=1, description="Maximum concurrent executions")
    queue_length: StrictInt = Field(default=0, ge=0, description="Current queue length")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Registry metadata")
    
    def is_healthy(self) -> bool:
        """Check if tool is healthy."""
        return (
            self.is_enabled and
            self.is_available and
            self.health_status in ["healthy", "warning"]
        )
    
    def can_accept_execution(self) -> bool:
        """Check if tool can accept new executions."""
        return (
            self.is_healthy() and
            self.current_executions < self.max_concurrent_executions
        )
    
    def update_execution_stats(self, success: bool, execution_time: float, memory_usage: float) -> None:
        """Update execution statistics."""
        self.total_executions += 1
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
        
        # Update averages
        total = self.total_executions
        self.average_execution_time_seconds = (
            (self.average_execution_time_seconds * (total - 1) + execution_time) / total
        )
        self.average_memory_usage_mb = (
            (self.average_memory_usage_mb * (total - 1) + memory_usage) / total
        )
        self.success_rate = self.successful_executions / total if total > 0 else 0.0


# Request/Response Models
class ToolListRequestModel(BaseModel):
    """Model for tool list request."""
    tool_types: Optional[List[ToolType]] = Field(default=None, description="Filter by tool types")
    supported_languages: Optional[List[SupportedLanguage]] = Field(default=None, description="Filter by supported languages")
    capabilities: Optional[List[StrictStr]] = Field(default=None, description="Filter by capabilities")
    available_only: StrictBool = Field(default=False, description="Only available tools")
    enabled_only: StrictBool = Field(default=True, description="Only enabled tools")
    include_config: StrictBool = Field(default=False, description="Include tool configuration")
    include_stats: StrictBool = Field(default=True, description="Include usage statistics")


class ToolListResponseModel(BaseModel):
    """Model for tool list response."""
    tools: List[ToolRegistryEntryModel] = Field(..., description="List of tools")
    total_count: StrictInt = Field(ge=0, description="Total number of tools")
    available_count: StrictInt = Field(ge=0, description="Number of available tools")
    enabled_count: StrictInt = Field(ge=0, description="Number of enabled tools")


class ToolExecutionListRequestModel(BaseModel):
    """Model for tool execution list request."""
    tool_id: Optional[StrictStr] = Field(default=None, description="Filter by tool ID")
    session_id: Optional[StrictStr] = Field(default=None, description="Filter by session ID")
    status: Optional[List[ToolStatus]] = Field(default=None, description="Filter by status")
    start_date: Optional[datetime] = Field(default=None, description="Filter start date")
    end_date: Optional[datetime] = Field(default=None, description="Filter end date")
    limit: StrictInt = Field(default=50, ge=1, le=1000, description="Maximum results")
    offset: StrictInt = Field(default=0, ge=0, description="Result offset")
    include_results: StrictBool = Field(default=False, description="Include execution results")


class ToolExecutionListResponseModel(BaseModel):
    """Model for tool execution list response."""
    executions: List[ToolExecutionResultModel] = Field(..., description="Tool executions")
    total_count: StrictInt = Field(ge=0, description="Total number of executions")
    has_more: StrictBool = Field(..., description="Whether more results are available")


# Export all models
__all__ = [
    # Configuration models
    "ToolParameterModel",
    "ToolCapabilityModel",
    "ToolConfigModel",
    
    # Execution models
    "ToolExecutionRequestModel",
    "ToolExecutionResultModel",
    
    # Registry models
    "ToolRegistryEntryModel",
    
    # Request/Response models
    "ToolListRequestModel",
    "ToolListResponseModel",
    "ToolExecutionListRequestModel",
    "ToolExecutionListResponseModel",
]
