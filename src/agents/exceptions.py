"""
Exception definitions for Agent components.

This module provides exception classes specific to agent operations,
inheriting from the base exception classes in common.
"""

from typing import Optional, Dict, Any

from ..common import ADKError


class AgentError(ADKError):
    """Base exception for agent-related errors."""
    
    def __init__(self, message: str, agent_id: Optional[str] = None, **kwargs):
        self.agent_id = agent_id
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include agent_id in dictionary representation."""
        result = super().to_dict()
        result["agent_id"] = self.agent_id
        return result


class AgentConfigurationError(AgentError):
    """Raised when agent configuration is invalid."""
    pass


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""
    pass


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""
    pass


class AgentValidationError(AgentError):
    """Raised when agent input/output validation fails."""
    pass


class WorkflowError(ADKError):
    """Base exception for workflow-related errors."""
    
    def __init__(self, message: str, workflow_id: Optional[str] = None, **kwargs):
        self.workflow_id = workflow_id
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include workflow_id in dictionary representation."""
        result = super().to_dict()
        result["workflow_id"] = self.workflow_id
        return result


class WorkflowConfigurationError(WorkflowError):
    """Raised when workflow configuration is invalid."""
    pass


class WorkflowExecutionError(WorkflowError):
    """Raised when workflow execution fails."""
    pass


class SessionError(ADKError):
    """Base exception for session-related errors."""
    
    def __init__(self, message: str, session_id: Optional[str] = None, **kwargs):
        self.session_id = session_id
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include session_id in dictionary representation."""
        result = super().to_dict()
        result["session_id"] = self.session_id
        return result


class SessionConfigurationError(SessionError):
    """Raised when session configuration is invalid."""
    pass


class SessionExecutionError(SessionError):
    """Raised when session execution fails."""
    pass


class FunctionToolError(ADKError):
    """Base exception for function tool errors."""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, **kwargs):
        self.tool_name = tool_name
        super().__init__(message, **kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Include tool_name in dictionary representation."""
        result = super().to_dict()
        result["tool_name"] = self.tool_name
        return result


class ToolConfigurationError(FunctionToolError):
    """Raised when tool configuration is invalid."""
    pass


class ToolExecutionError(FunctionToolError):
    """Raised when tool execution fails."""
    pass