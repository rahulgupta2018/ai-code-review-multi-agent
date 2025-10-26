"""
ADK Helpers and Utilities

This module provides ADK-specific utilities and helper functions for the
multi-agent code review system. These utilities support agent operations,
session management, validation, and integration with Google ADK framework.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable
from pathlib import Path
import logging

try:
    import structlog
    HAS_STRUCTLOG = True
    
    def get_structured_logger(name: str):
        return structlog.get_logger(name)
        
except ImportError:
    HAS_STRUCTLOG = False
    
    def get_structured_logger(name: str):
        return logging.getLogger(name)

try:
    from google.adk.core import SequentialAgent, FunctionTool
    HAS_ADK = True
except ImportError:
    # Mock ADK classes for development/testing
    class SequentialAgent:
        def __init__(self, agents: List[Any]):
            self.agents = agents
            
    class FunctionTool:
        def __init__(self, name: str, description: str, func: Callable):
            self.name = name
            self.description = description
            self.func = func
    HAS_ADK = False

from ..config.loader import get_config
from ..common.exceptions import ADKCodeReviewError
from ..common.utils import generate_correlation_id
from ..agents.types import AgentType, AgentStatus, AgentResult, WorkflowExecution
from ..agents.exceptions import (
    AgentError, AgentExecutionError, AgentValidationError,
    WorkflowError, WorkflowExecutionError, FunctionToolError
)


class ADKHelpers:
    """
    ADK-specific helper utilities for agent operations.
    
    Provides utilities for:
    - Agent validation and registration
    - Workflow orchestration
    - Function tool creation and management
    - Session coordination
    - Result aggregation
    - Error handling and recovery
    """
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """
        Initialize ADK helpers.
        
        Args:
            config_override: Optional configuration overrides
        """
        self._load_configuration(config_override)
        self.logger = get_structured_logger(self.__class__.__name__)
        
        # Initialize agent registry
        self._registered_agents: Dict[str, Any] = {}
        self._registered_tools: Dict[str, FunctionTool] = {}
        
        self.logger.info("ADK Helpers initialized - ADK available: %s", HAS_ADK)
    
    def _load_configuration(self, config_override: Optional[Dict[str, Any]] = None) -> None:
        """Load configuration from YAML files."""
        try:
            config = get_config()
            
            # Get ADK configuration
            adk_config = config.get('adk', {})
            agent_config = config.get('agents', {})
            
            # Merge configurations
            self._config = {
                **adk_config,
                **agent_config,
                **(config_override or {})
            }
            
        except Exception as e:
            self.logger.warning("Failed to load ADK configuration: %s", str(e))
            self._config = config_override or {}
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the ADK configuration."""
        return self._config.copy()
    
    @property
    def has_adk(self) -> bool:
        """Check if Google ADK is available."""
        return HAS_ADK
    
    # Agent Management
    
    async def validate_agent_config(self, agent_config: Dict[str, Any]) -> bool:
        """
        Validate agent configuration.
        
        Args:
            agent_config: Agent configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            required_fields = ['name', 'description', 'timeout']
            
            # Check required fields
            for field in required_fields:
                if field not in agent_config:
                    self.logger.error("Missing required agent field: %s", field)
                    return False
            
            # Validate timeout
            timeout = agent_config.get('timeout')
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                self.logger.error("Invalid timeout value: %s", timeout)
                return False
            
            # Validate agent type if present
            agent_type = agent_config.get('agent_type')
            if agent_type:
                try:
                    AgentType(agent_type)
                except ValueError:
                    self.logger.error("Invalid agent type: %s", agent_type)
                    return False
            
            self.logger.info("Agent configuration validated successfully")
            return True
            
        except Exception as e:
            self.logger.error("Agent configuration validation failed: %s", str(e))
            return False
    
    async def register_agent(self, agent_id: str, agent: Any) -> bool:
        """
        Register an agent with the ADK system.
        
        Args:
            agent_id: Unique agent identifier
            agent: Agent instance to register
            
        Returns:
            True if registered successfully, False otherwise
        """
        try:
            if agent_id in self._registered_agents:
                self.logger.warning("Agent already registered: %s", agent_id)
                return False
            
            # Validate agent has required methods
            required_methods = ['_run_async_impl', 'health_check']
            for method in required_methods:
                if not hasattr(agent, method):
                    self.logger.error("Agent missing required method: %s", method)
                    return False
            
            self._registered_agents[agent_id] = {
                'agent': agent,
                'registered_at': datetime.now(),
                'status': 'active'
            }
            
            self.logger.info("Agent registered successfully: %s", agent_id)
            return True
            
        except Exception as e:
            self.logger.error("Failed to register agent %s: %s", agent_id, str(e))
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent.
        
        Args:
            agent_id: Agent identifier to unregister
            
        Returns:
            True if unregistered successfully, False otherwise
        """
        try:
            if agent_id not in self._registered_agents:
                return False
            
            del self._registered_agents[agent_id]
            
            self.logger.info("Agent unregistered successfully: %s", agent_id)
            return True
            
        except Exception as e:
            self.logger.error("Failed to unregister agent %s: %s", agent_id, str(e))
            return False
    
    def get_registered_agents(self) -> Dict[str, Any]:
        """Get all registered agents."""
        return self._registered_agents.copy()
    
    # Workflow Management
    
    async def create_sequential_workflow(
        self,
        agents: List[Any],
        workflow_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        Create a sequential workflow using ADK SequentialAgent.
        
        Args:
            agents: List of agents to include in workflow
            workflow_id: Optional workflow identifier
            session_id: Optional session identifier
            
        Returns:
            SequentialAgent instance or None if creation failed
        """
        try:
            if not agents:
                self.logger.error("Cannot create workflow with empty agent list")
                return None
            
            if not HAS_ADK:
                self.logger.warning("ADK not available - creating mock workflow")
                return SequentialAgent(agents)
            
            # Create sequential workflow
            workflow = SequentialAgent(agents)
            
            # Track workflow
            if workflow_id:
                workflow_data: WorkflowExecution = {
                    'workflow_id': workflow_id,
                    'session_id': session_id or str(uuid.uuid4()),
                    'status': 'pending',
                    'agents': [{'agent_id': getattr(agent, 'agent_id', str(uuid.uuid4())), 
                               'agent_type': getattr(agent, 'agent_type', AgentType.CODE_QUALITY),
                               'enabled': True,
                               'priority': 1,
                               'timeout_seconds': 300,
                               'model_config': {}} for agent in agents],
                    'started_at': datetime.now(),
                    'completed_at': None,
                    'results': [],
                    'metadata': {'created_by': 'adk_helpers'}
                }
            
            self.logger.info(
                "Sequential workflow created - Agents: %d, ID: %s",
                len(agents),
                workflow_id
            )
            
            return workflow
            
        except Exception as e:
            self.logger.error("Failed to create sequential workflow: %s", str(e))
            return None
    
    async def execute_workflow_with_timeout(
        self,
        workflow: Any,
        ctx: Any,
        timeout_seconds: Optional[float] = None
    ) -> Any:
        """
        Execute a workflow with timeout and error handling.
        
        Args:
            workflow: Workflow to execute
            ctx: Execution context
            timeout_seconds: Optional timeout override
            
        Returns:
            Workflow execution result
        """
        try:
            # Get timeout from config if not provided
            if timeout_seconds is None:
                timeout_seconds = self._config.get('workflow', {}).get('default_timeout', 1800)
            
            self.logger.info("Executing workflow with timeout: %.1fs", timeout_seconds)
            
            # Execute workflow with timeout
            result = await asyncio.wait_for(
                workflow._run_async_impl(ctx),
                timeout=timeout_seconds
            )
            
            self.logger.info("Workflow execution completed successfully")
            return result
            
        except asyncio.TimeoutError as e:
            self.logger.error("Workflow execution timed out: %.1fs", timeout_seconds)
            raise WorkflowExecutionError(f"Workflow execution timed out after {timeout_seconds}s") from e
            
        except Exception as e:
            self.logger.error("Workflow execution failed: %s", str(e))
            if isinstance(e, WorkflowError):
                raise
            else:
                raise WorkflowExecutionError(f"Workflow execution failed: {e}") from e
    
    # Function Tool Management
    
    async def create_function_tool(
        self,
        name: str,
        description: str,
        func: Callable[..., Awaitable[Any]],
        validate_args: bool = True
    ) -> Optional[FunctionTool]:
        """
        Create an ADK FunctionTool.
        
        Args:
            name: Tool name
            description: Tool description
            func: Function to wrap as tool
            validate_args: Whether to validate function arguments
            
        Returns:
            FunctionTool instance or None if creation failed
        """
        try:
            if not name or not description or not func:
                self.logger.error("Invalid function tool parameters")
                return None
            
            # Validate function if requested
            if validate_args and not asyncio.iscoroutinefunction(func):
                self.logger.error("Function tool must be async: %s", name)
                return None
            
            # Create function tool
            if HAS_ADK:
                tool = FunctionTool(name=name, description=description, func=func)
            else:
                # Mock FunctionTool
                tool = FunctionTool(name=name, description=description, func=func)
            
            # Register tool
            self._registered_tools[name] = tool
            
            self.logger.info("Function tool created: %s", name)
            return tool
            
        except Exception as e:
            self.logger.error("Failed to create function tool %s: %s", name, str(e))
            return None
    
    def get_registered_tools(self) -> Dict[str, FunctionTool]:
        """Get all registered function tools."""
        return self._registered_tools.copy()
    
    # Result Processing
    
    async def aggregate_agent_results(
        self,
        results: List[AgentResult],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple agents.
        
        Args:
            results: List of agent results to aggregate
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            Aggregated result dictionary
        """
        try:
            if not results:
                return {
                    'summary': 'No results to aggregate',
                    'total_agents': 0,
                    'successful_agents': 0,
                    'failed_agents': 0,
                    'results': []
                }
            
            successful_results = [r for r in results if r['status'] == AgentStatus.COMPLETED]
            failed_results = [r for r in results if r['status'] == AgentStatus.FAILED]
            
            # Calculate aggregate metrics
            total_execution_time = sum(r.get('execution_time_seconds', 0) for r in results)
            
            aggregated = {
                'summary': f"Aggregated results from {len(results)} agents",
                'correlation_id': correlation_id or generate_correlation_id(),
                'total_agents': len(results),
                'successful_agents': len(successful_results),
                'failed_agents': len(failed_results),
                'total_execution_time_seconds': total_execution_time,
                'timestamp': datetime.now(),
                'results': results,
                'metadata': {
                    'aggregated_by': 'adk_helpers',
                    'aggregation_timestamp': datetime.now()
                }
            }
            
            # Add agent-type specific aggregations
            by_agent_type = {}
            for result in results:
                agent_type = result.get('agent_type', 'unknown')
                if isinstance(agent_type, AgentType):
                    agent_type = agent_type.value
                
                if agent_type not in by_agent_type:
                    by_agent_type[agent_type] = {
                        'count': 0,
                        'successful': 0,
                        'failed': 0,
                        'execution_time': 0.0
                    }
                
                by_agent_type[agent_type]['count'] += 1
                by_agent_type[agent_type]['execution_time'] += result.get('execution_time_seconds', 0)
                
                if result['status'] == AgentStatus.COMPLETED:
                    by_agent_type[agent_type]['successful'] += 1
                elif result['status'] == AgentStatus.FAILED:
                    by_agent_type[agent_type]['failed'] += 1
            
            aggregated['by_agent_type'] = by_agent_type
            
            self.logger.info(
                "Results aggregated - Total: %d, Successful: %d, Failed: %d",
                len(results),
                len(successful_results),
                len(failed_results)
            )
            
            return aggregated
            
        except Exception as e:
            self.logger.error("Failed to aggregate results: %s", str(e))
            return {
                'summary': f'Aggregation failed: {str(e)}',
                'error': str(e),
                'total_agents': len(results) if results else 0,
                'successful_agents': 0,
                'failed_agents': 0,
                'results': results or []
            }
    
    # Validation and Health Checks
    
    async def validate_adk_environment(self) -> Dict[str, Any]:
        """
        Validate the ADK environment setup.
        
        Returns:
            Validation result dictionary
        """
        try:
            validation_result = {
                'adk_available': HAS_ADK,
                'configuration_loaded': bool(self._config),
                'registered_agents': len(self._registered_agents),
                'registered_tools': len(self._registered_tools),
                'timestamp': datetime.now(),
                'status': 'healthy',
                'issues': []
            }
            
            # Check ADK availability
            if not HAS_ADK:
                validation_result['issues'].append("Google ADK not available - using mock implementations")
            
            # Check configuration
            if not self._config:
                validation_result['issues'].append("ADK configuration not loaded")
                validation_result['status'] = 'unhealthy'
            
            # Check required config sections
            required_sections = ['agent', 'session_service']
            for section in required_sections:
                if section not in self._config:
                    validation_result['issues'].append(f"Missing configuration section: {section}")
            
            if validation_result['issues']:
                validation_result['status'] = 'warning' if HAS_ADK else 'unhealthy'
            
            self.logger.info(
                "ADK environment validation completed - Status: %s, Issues: %d",
                validation_result['status'],
                len(validation_result['issues'])
            )
            
            return validation_result
            
        except Exception as e:
            self.logger.error("ADK environment validation failed: %s", str(e))
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    async def health_check_agents(self, agent_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform health checks on registered agents.
        
        Args:
            agent_ids: Optional list of specific agent IDs to check
            
        Returns:
            Health check results
        """
        try:
            agents_to_check = agent_ids or list(self._registered_agents.keys())
            health_results = {}
            
            for agent_id in agents_to_check:
                if agent_id not in self._registered_agents:
                    health_results[agent_id] = {
                        'status': 'not_found',
                        'error': 'Agent not registered'
                    }
                    continue
                
                try:
                    agent_info = self._registered_agents[agent_id]
                    agent = agent_info['agent']
                    
                    # Call agent health check if available
                    if hasattr(agent, 'health_check'):
                        health_result = await agent.health_check()
                        health_results[agent_id] = health_result
                    else:
                        health_results[agent_id] = {
                            'status': 'healthy',
                            'note': 'No health_check method available'
                        }
                        
                except Exception as e:
                    health_results[agent_id] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            
            overall_status = 'healthy'
            unhealthy_count = sum(1 for result in health_results.values() 
                                 if result.get('status') != 'healthy')
            
            if unhealthy_count > 0:
                overall_status = 'unhealthy' if unhealthy_count == len(health_results) else 'warning'
            
            summary = {
                'overall_status': overall_status,
                'total_agents': len(agents_to_check),
                'healthy_agents': len(health_results) - unhealthy_count,
                'unhealthy_agents': unhealthy_count,
                'individual_results': health_results,
                'timestamp': datetime.now()
            }
            
            self.logger.info(
                "Agent health check completed - Total: %d, Healthy: %d, Unhealthy: %d",
                len(agents_to_check),
                summary['healthy_agents'],
                summary['unhealthy_agents']
            )
            
            return summary
            
        except Exception as e:
            self.logger.error("Agent health check failed: %s", str(e))
            return {
                'overall_status': 'error',
                'error': str(e),
                'timestamp': datetime.now()
            }
    
    # Utility Functions
    
    def generate_workflow_id(self, prefix: str = "workflow") -> str:
        """Generate a unique workflow ID."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    def generate_agent_id(self, agent_type: Union[str, AgentType], prefix: str = "agent") -> str:
        """Generate a unique agent ID."""
        type_str = agent_type.value if isinstance(agent_type, AgentType) else str(agent_type)
        return f"{prefix}_{type_str}_{uuid.uuid4().hex[:8]}"
    
    async def format_execution_summary(
        self,
        workflow_execution: Dict[str, Any],
        include_detailed_results: bool = False
    ) -> str:
        """
        Format workflow execution summary for logging/reporting.
        
        Args:
            workflow_execution: Workflow execution data
            include_detailed_results: Whether to include detailed agent results
            
        Returns:
            Formatted summary string
        """
        try:
            summary_lines = [
                f"Workflow Execution Summary",
                f"=" * 40,
                f"Workflow ID: {workflow_execution.get('workflow_id', 'Unknown')}",
                f"Session ID: {workflow_execution.get('session_id', 'Unknown')}",
                f"Status: {workflow_execution.get('status', 'Unknown')}",
                f"Started: {workflow_execution.get('started_at', 'Unknown')}",
                f"Completed: {workflow_execution.get('completed_at', 'In Progress')}",
                f"Total Agents: {len(workflow_execution.get('agents', []))}",
                f"Results: {len(workflow_execution.get('results', []))}"
            ]
            
            if include_detailed_results:
                results = workflow_execution.get('results', [])
                if results:
                    summary_lines.extend([
                        "",
                        "Detailed Results:",
                        "-" * 20
                    ])
                    
                    for i, result in enumerate(results, 1):
                        agent_id = result.get('agent_id', 'Unknown')
                        status = result.get('status', 'Unknown')
                        exec_time = result.get('execution_time_seconds', 0)
                        
                        summary_lines.append(
                            f"{i}. {agent_id}: {status} ({exec_time:.2f}s)"
                        )
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            self.logger.error("Failed to format execution summary: %s", str(e))
            return f"Failed to format summary: {str(e)}"


# Global ADK helpers instance
_adk_helpers: Optional[ADKHelpers] = None


def get_adk_helpers(config_override: Optional[Dict[str, Any]] = None) -> ADKHelpers:
    """
    Get the global ADK helpers instance.
    
    Args:
        config_override: Optional configuration overrides
        
    Returns:
        ADK helpers instance
    """
    global _adk_helpers
    
    if _adk_helpers is None:
        _adk_helpers = ADKHelpers(config_override)
    
    return _adk_helpers
