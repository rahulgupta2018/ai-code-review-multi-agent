"""ADK BaseAgent Implementation for AI Code Review Multi-Agent System."""

import asyncio
import time
import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

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
    from google.adk.core import BaseAgent as ADKBaseAgentCore
    HAS_ADK = True
except ImportError:
    class ADKBaseAgentCore:
        def __init__(self, name: str, description: str):
            self.name = name
            self.description = description
        async def _run_async_impl(self, ctx):
            return {}
    HAS_ADK = False

from ..config.loader import get_config
from ..common.exceptions import ADKCodeReviewError
from ..common.utils import generate_correlation_id
from .types import AgentType, AgentStatus
from .exceptions import AgentError, AgentExecutionError, AgentTimeoutError, AgentConfigurationError, AgentValidationError
from .constants import DEFAULT_AGENT_TIMEOUT, AGENT_VERSION_KEY


class ADKBaseAgent(ADKBaseAgentCore, ABC):
    """Base agent implementation for ADK multi-agent code review system."""
    
    def __init__(self, agent_type: AgentType, name: Optional[str] = None, description: Optional[str] = None, config_override: Optional[Dict[str, Any]] = None):
        self._load_configuration(agent_type, config_override)
        
        agent_name = name or self._config.get('name', f"{agent_type.value}_agent")
        agent_description = description or self._config.get('description', f"Agent for {agent_type.value} analysis")
        
        super().__init__(name=agent_name, description=agent_description)
        
        self.agent_type = agent_type
        self.agent_id = str(uuid.uuid4())
        self.status = AgentStatus.PENDING
        self.correlation_id = generate_correlation_id()
        
        self.logger = get_structured_logger(self.__class__.__name__)
        
        self._metrics = {
            'executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_execution_time': 0.0,
            'last_execution': None
        }
        
        self._current_session: Optional[Dict[str, Any]] = None
        self._session_data: Dict[str, Any] = {}
        
        self.logger.info("Agent initialized - ID: %s, Type: %s", self.agent_id, agent_type.value)
    
    def _load_configuration(self, agent_type: AgentType, config_override: Optional[Dict[str, Any]] = None) -> None:
        """Load configuration from YAML files with no hardcoding."""
        try:
            config = get_config()
            adk_config = config.get('adk', {}).get('agent', {})
            if not adk_config:
                raise AgentConfigurationError("ADK agent configuration not found")
            
            agent_configs = config.get('agents', {})
            if not agent_configs:
                raise AgentConfigurationError("Agent configurations not found")
            
            agent_specific_config = agent_configs.get(agent_type.value, {})
            if not agent_specific_config:
                raise AgentConfigurationError(f"Configuration for {agent_type.value} not found")
            
            self._config = {**adk_config, **agent_specific_config, **(config_override or {})}
            self._validate_configuration()
            
        except Exception as e:
            raise AgentConfigurationError(f"Failed to load agent configuration: {e}") from e
    
    def _validate_configuration(self) -> None:
        """Validate the loaded configuration."""
        required_fields = ['name', 'description', 'timeout']
        missing_fields = [field for field in required_fields if field not in self._config]
        
        if missing_fields:
            raise AgentConfigurationError(f"Missing required configuration fields: {missing_fields}")
        
        timeout = self._config.get('timeout', DEFAULT_AGENT_TIMEOUT)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise AgentConfigurationError(f"Invalid timeout value: {timeout}")
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the agent configuration."""
        return self._config.copy()
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        return self._metrics.copy()
    
    @abstractmethod
    async def _execute_agent_logic(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the specific agent logic. Must be implemented by specialized agents."""
        pass
    
    async def _run_async_impl(self, ctx) -> Any:
        """Main ADK BaseAgent execution method."""
        execution_start = time.time()
        self.status = AgentStatus.RUNNING
        execution_id = generate_correlation_id()
        
        self.logger.info("Agent execution started - ID: %s", execution_id)
        
        try:
            timeout_seconds = self._config.get('timeout', DEFAULT_AGENT_TIMEOUT)
            result = await asyncio.wait_for(
                self._execute_with_context(ctx, execution_id),
                timeout=timeout_seconds
            )
            
            execution_time = time.time() - execution_start
            await self._update_metrics(execution_time, success=True)
            self.status = AgentStatus.COMPLETED
            
            self.logger.info("Agent execution completed - Time: %.2fs", execution_time)
            return result
                
        except asyncio.TimeoutError as e:
            self.status = AgentStatus.TIMEOUT
            execution_time = time.time() - execution_start
            await self._update_metrics(execution_time, success=False)
            self.logger.error("Agent execution timeout - Time: %.2fs", execution_time)
            raise AgentTimeoutError(f"Agent execution timed out after {execution_time:.2f}s") from e
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            execution_time = time.time() - execution_start
            await self._update_metrics(execution_time, success=False)
            self.logger.error("Agent execution failed - Time: %.2fs, Error: %s", execution_time, str(e))
            
            if isinstance(e, AgentError):
                raise
            else:
                raise AgentExecutionError(f"Agent execution failed: {e}") from e
    
    async def _execute_with_context(self, ctx, execution_id: str) -> Dict[str, Any]:
        """Execute agent logic with proper context setup."""
        if hasattr(ctx, 'session_id'):
            await self._setup_session(ctx.session_id)
        
        try:
            exec_ctx = {
                'ctx': ctx,
                'logger': self.logger,
                'config': self._config,
                'session': self._current_session,
                'correlation_id': self.correlation_id,
                'execution_id': execution_id
            }
            
            result = await self._execute_agent_logic(exec_ctx)
            validated_result = await self._validate_result(result)
            return validated_result
            
        finally:
            await self._cleanup_session()
    
    async def _setup_session(self, session_id: str) -> None:
        """Set up session for agent execution."""
        try:
            self._current_session = {
                'session_id': session_id,
                'correlation_id': self.correlation_id,
                'status': 'active',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'metadata': {'agent_id': self.agent_id, 'agent_type': self.agent_type.value}
            }
            self.logger.info("Session setup completed - ID: %s", session_id)
        except Exception as e:
            self.logger.error("Session setup failed - ID: %s, Error: %s", session_id, str(e))
            raise AgentExecutionError(f"Failed to set up session: {e}") from e
    
    async def _cleanup_session(self) -> None:
        """Clean up session data after execution."""
        try:
            if self._current_session:
                session_id = self._current_session.get('session_id')
                self.logger.info("Session cleanup completed - ID: %s", session_id)
                self._current_session = None
                self._session_data.clear()
        except Exception as e:
            self.logger.warning("Session cleanup failed - Error: %s", str(e))
    
    async def _update_metrics(self, execution_time: float, success: bool) -> None:
        """Update agent performance metrics."""
        self._metrics['executions'] += 1
        self._metrics['total_execution_time'] += execution_time
        self._metrics['last_execution'] = time.time()
        
        if success:
            self._metrics['successful_executions'] += 1
        else:
            self._metrics['failed_executions'] += 1
    
    async def _validate_result(self, result: Any) -> Dict[str, Any]:
        """Validate and format the agent execution result."""
        if not isinstance(result, dict):
            raise AgentValidationError(f"Agent result must be a dictionary, got {type(result)}")
        
        agent_result = {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'status': self.status,
            'execution_time_seconds': self._metrics['total_execution_time'],
            'timestamp': datetime.now(),
            'error_message': None,
            'metadata': {
                AGENT_VERSION_KEY: self._config.get('version', '1.0.0'),
                'correlation_id': self.correlation_id,
                **result.get('metadata', {})
            }
        }
        
        agent_result.update({k: v for k, v in result.items() if k != 'metadata'})
        return agent_result
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform agent health check."""
        try:            
            health_status = {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type.value,
                'status': 'healthy',
                'last_check': datetime.now(),
                'metrics': self._metrics,
                'configuration_valid': True,
                'session_active': self._current_session is not None
            }
            self.logger.info("Health check completed - Status: healthy")
            return health_status
        except Exception as e:
            self.logger.error("Health check failed - Error: %s", str(e))
            return {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type.value,
                'status': 'unhealthy',
                'last_check': datetime.now(),
                'error': str(e)
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive agent information."""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'configuration': self._config,
            'metrics': self._metrics,
            'current_session': self._current_session,
            'correlation_id': self.correlation_id,
            'has_adk': HAS_ADK,
            'has_structlog': HAS_STRUCTLOG
        }
