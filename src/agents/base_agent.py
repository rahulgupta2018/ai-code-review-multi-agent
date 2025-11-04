"""ADK BaseAgent Implementation for AI Code Review Multi-Agent System."""

import asyncio
import time
import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, List

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

from ..utils.config_loader import get_config
from ..utils.exceptions import (
    ADKCodeReviewError, AgentError, AgentExecutionError, AgentTimeoutError, 
    AgentConfigurationError, AgentValidationError, FunctionToolError
)
from ..utils.common import generate_correlation_id
from ..utils.constants import (
    DEFAULT_AGENT_TIMEOUT, 
    AGENT_VERSION_KEY,
    MAX_TOOL_EXECUTION_TIME,
    AGENT_HEALTH_CHECK_INTERVAL,
    AGENT_HEALTH_TIMEOUT
)
from ..utils.types import AgentType, AgentStatus
from ..utils.adk_helpers import get_adk_helpers


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
        
        # Tool orchestration components
        self._tools: Dict[str, Any] = {}
        self._tool_registry: Dict[str, Dict[str, Any]] = {}
        self._tool_timeouts: Dict[str, float] = {}
        
        # ADK FunctionTool integration
        self._function_tools: Dict[str, Any] = {}
        self._adk_helpers = get_adk_helpers()
        self._function_tools_registered = False
        
        # Initialize tool orchestration
        self._load_tools()
        
        self.logger.info("Agent initialized - ID: %s, Type: %s, Tools: %d", 
                        self.agent_id, agent_type.value, len(self._tools))
    
    def _load_configuration(self, agent_type: AgentType, config_override: Optional[Dict[str, Any]] = None) -> None:
        """Load configuration from YAML files using consolidated config loader."""
        try:
            config = get_config()
            
            # Get ADK agent configuration
            adk_config = config.get('adk', {}).get('agent', {})
            
            # Get agent configurations
            agent_configs = config.get('agents', {})
            
            # Get agent-specific configuration
            agent_specific_config = agent_configs.get(agent_type.value, {})
            
            # Fail if no agent-specific configuration found
            if not agent_specific_config:
                raise AgentConfigurationError(f"No configuration found for agent type: {agent_type.value}")
            
            # Merge configurations with priority: config_override > agent_specific > adk_config
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
    
    def _load_tools(self) -> None:
        """Load and register tools based strictly on agent configuration - no fallbacks."""
        try:
            # Get tool configuration from agent config - fail if not present
            agent_tools = self._config.get('tools', [])
            
            if not agent_tools:
                self.logger.error("No tools configured for agent type: %s", self.agent_type.value)
                raise AgentConfigurationError(f"No tools configured for agent type: {self.agent_type.value}")
            
            self.logger.info("Loading configured tools for agent type: %s, tools: %s", 
                           self.agent_type.value, agent_tools)
            
            # Get available tools from configuration
            available_tools = self._discover_available_tools()
            
            # Register tools based on agent configuration - fail if any tool is missing
            missing_tools = []
            for tool_name in agent_tools:
                if tool_name in available_tools:
                    self._register_tool(tool_name, available_tools[tool_name])
                else:
                    missing_tools.append(tool_name)
            
            # Fail fast if any configured tools are missing
            if missing_tools:
                self.logger.error("Configured tools not available: %s", missing_tools)
                raise AgentConfigurationError(f"Configured tools not available: {missing_tools}")
            
            if len(self._tools) == 0:
                self.logger.error("No tools successfully registered for agent type: %s", self.agent_type.value)
                raise AgentConfigurationError(f"No tools successfully registered for agent type: {self.agent_type.value}")
            
            self.logger.info("Tool loading completed - %d tools registered", len(self._tools))
            
        except Exception as e:
            self.logger.error("Failed to load tools: %s", str(e))
            if isinstance(e, AgentConfigurationError):
                raise
            else:
                raise AgentConfigurationError(f"Tool loading failed: {e}") from e
    
    def _discover_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Discover available tools from configuration and validate against src/tools directory."""
        available_tools = {}
        
        try:
            # Load tool configuration from config/adk/tools.yaml
            config = get_config()
            tools_config = config.get('adk', {}).get('tools', {})
            
            if not tools_config:
                self.logger.error("No ADK tools configuration found")
                raise AgentConfigurationError("ADK tools configuration not found")
            
            configured_tools = tools_config.get('tools', {})
            if not configured_tools:
                self.logger.error("No tools defined in tools configuration")
                raise AgentConfigurationError("No tools defined in configuration")
            
            # Get tools directory path for validation
            from pathlib import Path
            tools_path = Path(__file__).parent.parent / "tools"
            
            if not tools_path.exists():
                self.logger.error("Tools directory not found: %s", tools_path)
                raise AgentConfigurationError(f"Tools directory not found: {tools_path}")
            
            # Process each configured tool
            for tool_key, tool_config in configured_tools.items():
                try:
                    # Validate tool configuration
                    required_fields = ['name', 'description', 'module', 'agent_types']
                    missing_fields = [field for field in required_fields if field not in tool_config]
                    
                    if missing_fields:
                        self.logger.error("Tool %s missing required fields: %s", tool_key, missing_fields)
                        continue
                    
                    # Check if this tool is compatible with current agent type
                    if self.agent_type.value not in tool_config['agent_types']:
                        self.logger.debug("Tool %s not compatible with agent type %s", 
                                        tool_key, self.agent_type.value)
                        continue
                    
                    # Validate tool file exists
                    tool_file = tools_path / f"{tool_config['module']}.py"
                    if not tool_file.exists():
                        self.logger.error("Tool module file not found: %s", tool_file)
                        raise AgentConfigurationError(f"Tool module file not found: {tool_file}")
                    
                    # Add tool to available tools
                    available_tools[tool_key] = {
                        'name': tool_config['name'],
                        'description': tool_config['description'],
                        'module': tool_config['module'],
                        'agent_types': tool_config['agent_types'],
                        'timeout': tool_config.get('timeout', 60.0),
                        'parameters': tool_config.get('parameters', {}),
                        'config': tool_config.get('config', {})
                    }
                    
                    self.logger.debug("Discovered tool: %s for agent type: %s", 
                                    tool_key, self.agent_type.value)
                    
                except Exception as e:
                    self.logger.error("Failed to process tool configuration %s: %s", tool_key, str(e))
                    raise AgentConfigurationError(f"Invalid tool configuration for {tool_key}: {e}") from e
            
            if not available_tools:
                self.logger.error("No compatible tools found for agent type: %s", self.agent_type.value)
                raise AgentConfigurationError(f"No compatible tools found for agent type: {self.agent_type.value}")
            
            self.logger.info("Tool discovery completed - %d tools available for %s", 
                           len(available_tools), self.agent_type.value)
            return available_tools
            
        except Exception as e:
            self.logger.error("Tool discovery failed: %s", str(e))
            if isinstance(e, AgentConfigurationError):
                raise
            else:
                raise AgentConfigurationError(f"Tool discovery failed: {e}") from e
    
    def _register_tool(self, tool_name: str, tool_info: Dict[str, Any]) -> None:
        """Register a tool for use by this agent."""
        try:
            # Create tool registration entry
            tool_registration = {
                'name': tool_info['name'],
                'description': tool_info['description'],
                'module': tool_info['module'],
                'timeout': tool_info.get('timeout', 60.0),
                'agent_types': tool_info['agent_types'],
                'status': 'registered',
                'registered_at': time.time()
            }
            
            # Store in registries
            self._tool_registry[tool_name] = tool_registration
            self._tool_timeouts[tool_name] = tool_registration['timeout']
            
            # For now, store the tool info - actual tool instances will be created when needed
            self._tools[tool_name] = tool_registration
            
            self.logger.info("Tool registered: %s (%s)", tool_name, tool_info['name'])
            
        except Exception as e:
            self.logger.error("Failed to register tool %s: %s", tool_name, str(e))
            raise AgentConfigurationError(f"Tool registration failed for {tool_name}: {e}") from e
    
    async def _execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a registered tool with comprehensive error handling and timeout management."""
        if tool_name not in self._tools:
            raise AgentExecutionError(f"Tool not registered: {tool_name}")
        
        tool_info = self._tools[tool_name]
        execution_start = time.time()
        tool_timeout = self._tool_timeouts.get(tool_name, 60.0)
        
        self.logger.info("Executing tool: %s with timeout: %.1fs", tool_name, tool_timeout)
        
        try:
            # Create tool execution context
            tool_context = {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type.value,
                'session': self._current_session,
                'correlation_id': self.correlation_id,
                'execution_start': execution_start,
                **kwargs
            }
            
            # Execute tool with timeout
            result = await asyncio.wait_for(
                self._execute_tool_implementation(tool_name, tool_info, tool_context),
                timeout=tool_timeout
            )
            
            execution_time = time.time() - execution_start
            self.logger.info("Tool execution completed: %s in %.2fs", tool_name, execution_time)
            
            # Validate and enhance result
            validated_result = await self._validate_tool_result(tool_name, result)
            validated_result.update({
                'execution_time_seconds': execution_time,
                'tool_name': tool_name,
                'agent_id': self.agent_id
            })
            
            return validated_result
            
        except asyncio.TimeoutError as e:
            execution_time = time.time() - execution_start
            self.logger.error("Tool execution timeout: %s after %.2fs", tool_name, execution_time)
            raise AgentTimeoutError(f"Tool {tool_name} execution timed out after {execution_time:.2f}s") from e
            
        except Exception as e:
            execution_time = time.time() - execution_start
            self.logger.error("Tool execution failed: %s after %.2fs, error: %s", 
                            tool_name, execution_time, str(e))
            raise AgentExecutionError(f"Tool {tool_name} execution failed: {e}") from e
    
    async def _execute_tool_implementation(self, tool_name: str, tool_info: Dict[str, Any], 
                                         tool_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual tool implementation with proper error handling."""
        try:
            # Dynamic import of tool module
            import importlib
            module_name = f"src.tools.{tool_info['module']}"
            
            try:
                # Import the tool module
                tool_module = importlib.import_module(module_name)
            except ImportError as e:
                self.logger.error("Failed to import tool module %s: %s", module_name, str(e))
                raise AgentExecutionError(f"Tool module {module_name} not found or failed to import: {e}") from e
            
            # Check if the tool module has the expected function or class
            tool_class_name = tool_info['name']
            if not hasattr(tool_module, tool_class_name):
                self.logger.error("Tool class %s not found in module %s", tool_class_name, module_name)
                raise AgentExecutionError(f"Tool class {tool_class_name} not found in module {module_name}")
            
            # Get the tool class
            tool_class = getattr(tool_module, tool_class_name)
            
            # Instantiate the tool with configuration
            tool_config = tool_info.get('config', {})
            tool_parameters = tool_info.get('parameters', {})
            
            try:
                tool_instance = tool_class(config=tool_config, **tool_parameters)
            except Exception as e:
                self.logger.error("Failed to instantiate tool %s: %s", tool_class_name, str(e))
                raise AgentExecutionError(f"Failed to instantiate tool {tool_class_name}: {e}") from e
            
            # Execute the tool with the provided context
            try:
                if hasattr(tool_instance, 'execute'):
                    if asyncio.iscoroutinefunction(tool_instance.execute):
                        result = await tool_instance.execute(tool_context)
                    else:
                        result = tool_instance.execute(tool_context)
                elif hasattr(tool_instance, 'run'):
                    if asyncio.iscoroutinefunction(tool_instance.run):
                        result = await tool_instance.run(tool_context)
                    else:
                        result = tool_instance.run(tool_context)
                elif callable(tool_instance):
                    if asyncio.iscoroutinefunction(tool_instance):
                        result = await tool_instance(tool_context)
                    else:
                        result = tool_instance(tool_context)
                else:
                    self.logger.error("Tool %s has no executable method (execute, run, or __call__)", tool_class_name)
                    raise AgentExecutionError(f"Tool {tool_class_name} has no executable method")
                
                # Ensure result is a dictionary
                if not isinstance(result, dict):
                    self.logger.error("Tool %s returned non-dictionary result: %s", tool_class_name, type(result))
                    raise AgentExecutionError(f"Tool {tool_class_name} must return a dictionary result")
                
                return result
                
            except Exception as e:
                self.logger.error("Tool execution failed for %s: %s", tool_class_name, str(e))
                raise AgentExecutionError(f"Tool {tool_class_name} execution failed: {e}") from e
                
        except Exception as e:
            self.logger.error("Tool implementation execution failed: %s", str(e))
            if isinstance(e, AgentExecutionError):
                raise
            else:
                raise AgentExecutionError(f"Tool implementation execution failed: {e}") from e
    
    async def _validate_tool_result(self, tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and standardize tool execution results."""
        try:
            # Ensure result is a dictionary
            if not isinstance(result, dict):
                self.logger.warning("Tool result not a dictionary: %s", tool_name)
                result = {'status': 'error', 'error_message': 'Invalid result format'}
            
            # Ensure required fields exist
            required_fields = ['status']
            for field in required_fields:
                if field not in result:
                    result[field] = 'unknown'
            
            # Add tool metadata
            result.setdefault('metadata', {}).update({
                'tool_name': tool_name,
                'agent_id': self.agent_id,
                'validation_timestamp': time.time()
            })
            
            return result
            
        except Exception as e:
            self.logger.error("Tool result validation failed for %s: %s", tool_name, str(e))
            return {
                'status': 'validation_error',
                'tool_name': tool_name,
                'error_message': f"Result validation failed: {e}",
                'metadata': {'agent_id': self.agent_id, 'validation_timestamp': time.time()}
            }
    
    async def _register_function_tools(self) -> None:
        """Register existing tools as ADK FunctionTools for enhanced integration."""
        try:
            self.logger.info("Starting ADK FunctionTool registration for %d tools", len(self._tools))
            
            for tool_name, tool_info in self._tools.items():
                try:
                    # Create a wrapper function for the tool that conforms to ADK FunctionTool interface
                    async def create_tool_wrapper(tn=tool_name, ti=tool_info):
                        async def tool_function(**kwargs) -> Dict[str, Any]:
                            """ADK FunctionTool wrapper for existing tool implementation."""
                            try:
                                # Execute the tool using our existing tool execution pipeline
                                result = await self._execute_tool(tn, **kwargs)
                                return result
                            except Exception as e:
                                self.logger.error("FunctionTool execution failed for %s: %s", tn, str(e))
                                raise FunctionToolError(f"FunctionTool {tn} execution failed: {e}") from e
                        return tool_function
                    
                    # Create the tool wrapper
                    tool_wrapper = await create_tool_wrapper()
                    
                    # Register as ADK FunctionTool using adk_helpers
                    function_tool = await self._adk_helpers.create_function_tool(
                        name=tool_name,
                        description=tool_info.get('description', f"ADK FunctionTool for {tool_name}"),
                        func=tool_wrapper,
                        validate_args=True
                    )
                    
                    if function_tool:
                        self._function_tools[tool_name] = function_tool
                        self.logger.info("Registered ADK FunctionTool: %s", tool_name)
                    else:
                        self.logger.error("Failed to create ADK FunctionTool: %s", tool_name)
                        
                except Exception as e:
                    self.logger.error("Failed to register FunctionTool %s: %s", tool_name, str(e))
                    # Continue with other tools
                    continue
            
            self.logger.info("ADK FunctionTool registration completed - %d tools registered", 
                           len(self._function_tools))
            
        except Exception as e:
            self.logger.error("ADK FunctionTool registration failed: %s", str(e))
            # Don't fail agent initialization if FunctionTool registration fails
            pass

    def get_function_tools(self) -> Dict[str, Any]:
        """Get all registered ADK FunctionTools."""
        return self._function_tools.copy()
    
    def get_function_tool(self, tool_name: str) -> Optional[Any]:
        """Get a specific ADK FunctionTool by name."""
        return self._function_tools.get(tool_name)
    
    async def execute_function_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute an ADK FunctionTool directly."""
        if tool_name not in self._function_tools:
            raise FunctionToolError(f"ADK FunctionTool not registered: {tool_name}")
        
        try:
            function_tool = self._function_tools[tool_name]
            
            # Execute FunctionTool using ADK interface
            if hasattr(function_tool, 'func'):
                result = await function_tool.func(**kwargs)
            else:
                # Fallback to calling the tool directly
                result = await function_tool(**kwargs)
            
            self.logger.info("ADK FunctionTool executed successfully: %s", tool_name)
            return result
            
        except Exception as e:
            self.logger.error("ADK FunctionTool execution failed for %s: %s", tool_name, str(e))
            raise FunctionToolError(f"ADK FunctionTool {tool_name} execution failed: {e}") from e

    async def validate_function_tool_integration(self) -> Dict[str, Any]:
        """Validate that FunctionTool integration is working correctly."""
        try:
            validation_result = {
                'status': 'success',
                'adk_helpers_available': self._adk_helpers is not None,
                'total_tools': len(self._tools),
                'function_tools_registered': len(self._function_tools),
                'function_tool_names': list(self._function_tools.keys()),
                'integration_healthy': True,
                'issues': []
            }
            
            # Check if ADK helpers are available
            if not self._adk_helpers:
                validation_result['issues'].append("ADK helpers not available")
                validation_result['integration_healthy'] = False
            
            # Check if all tools were registered as FunctionTools
            missing_function_tools = set(self._tools.keys()) - set(self._function_tools.keys())
            if missing_function_tools:
                validation_result['issues'].append(f"Tools not registered as FunctionTools: {list(missing_function_tools)}")
                validation_result['integration_healthy'] = False
            
            # Validate each FunctionTool
            for tool_name, function_tool in self._function_tools.items():
                if not hasattr(function_tool, 'name') or not hasattr(function_tool, 'description'):
                    validation_result['issues'].append(f"FunctionTool {tool_name} missing required attributes")
                    validation_result['integration_healthy'] = False
            
            if validation_result['issues']:
                validation_result['status'] = 'warning' if validation_result['integration_healthy'] else 'error'
            
            self.logger.info("FunctionTool integration validation completed - Status: %s", 
                           validation_result['status'])
            return validation_result
            
        except Exception as e:
            self.logger.error("FunctionTool integration validation failed: %s", str(e))
            return {
                'status': 'error',
                'error': str(e),
                'integration_healthy': False,
                'issues': [f"Validation failed: {str(e)}"]
            }
    
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
    
    async def _ensure_function_tools_registered(self) -> None:
        """Ensure ADK FunctionTools are registered before use."""
        if not self._function_tools_registered:
            await self._register_function_tools()
            self._function_tools_registered = True

    async def _execute_with_context(self, ctx, execution_id: str) -> Dict[str, Any]:
        """Execute agent logic with proper context setup."""
        # Ensure FunctionTools are registered
        await self._ensure_function_tools_registered()
        
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
    
    def get_registered_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered tools."""
        return self._tool_registry.copy()
    
    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a specific tool is available for execution."""
        return tool_name in self._tools
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific tool."""
        return self._tool_registry.get(tool_name)
    
    async def execute_tools(self, tool_executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute multiple tools and aggregate results."""
        results = {}
        execution_start = time.time()
        
        self.logger.info("Executing %d tools", len(tool_executions))
        
        for tool_execution in tool_executions:
            tool_name = tool_execution.get('tool_name')
            tool_kwargs = tool_execution.get('kwargs', {})
            
            if not tool_name:
                self.logger.warning("Tool execution missing tool_name")
                continue
                
            try:
                result = await self._execute_tool(tool_name, **tool_kwargs)
                results[tool_name] = result
            except Exception as e:
                self.logger.error("Failed to execute tool %s: %s", tool_name, str(e))
                results[tool_name] = {
                    'status': 'error',
                    'tool_name': tool_name,
                    'error_message': str(e),
                    'error_type': type(e).__name__
                }
        
        total_execution_time = time.time() - execution_start
        
        return {
            'total_execution_time_seconds': total_execution_time,
            'tools_executed': len(results),
            'successful_tools': len([r for r in results.values() if r.get('status') != 'error']),
            'failed_tools': len([r for r in results.values() if r.get('status') == 'error']),
            'results': results,
            'agent_id': self.agent_id
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform agent health check including tool orchestration status."""
        try:            
            health_status = {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type.value,
                'status': 'healthy',
                'last_check': datetime.now(),
                'metrics': self._metrics,
                'configuration_valid': True,
                'session_active': self._current_session is not None,
                'tool_orchestration': {
                    'tools_loaded': len(self._tools) > 0,
                    'registered_tools_count': len(self._tools),
                    'tool_registry_status': 'operational' if self._tool_registry else 'empty',
                    'tools_available': list(self._tools.keys()),
                    'function_tools_registered': len(self._function_tools),
                    'function_tool_names': list(self._function_tools.keys()),
                    'adk_integration_status': 'operational' if self._function_tools else 'not_registered'
                }
            }
            self.logger.info("Health check completed - Status: healthy, Tools: %d", len(self._tools))
            return health_status
        except Exception as e:
            self.logger.error("Health check failed - Error: %s", str(e))
            return {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type.value,
                'status': 'unhealthy',
                'last_check': datetime.now(),
                'error': str(e),
                'tool_orchestration': {
                    'tools_loaded': False,
                    'function_tools_registered': 0,
                    'error': 'Health check failed during tool status evaluation'
                }
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive agent information including tool orchestration details."""
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
            'has_structlog': HAS_STRUCTLOG,
            'tool_orchestration': {
                'registered_tools': list(self._tools.keys()),
                'tool_registry': self._tool_registry,
                'tool_count': len(self._tools),
                'tool_timeouts': self._tool_timeouts,
                'function_tools': list(self._function_tools.keys()),
                'function_tool_count': len(self._function_tools),
                'adk_helpers_available': self._adk_helpers is not None
            }
        }
