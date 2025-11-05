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

from utils.config_loader import get_config
from utils.exceptions import (
    ADKCodeReviewError, AgentError, AgentExecutionError, AgentTimeoutError, 
    AgentConfigurationError, AgentValidationError, FunctionToolError
)
from utils.common import generate_correlation_id
from utils.constants import (
    DEFAULT_AGENT_TIMEOUT, 
    AGENT_VERSION_KEY,
    MAX_TOOL_EXECUTION_TIME,
    AGENT_HEALTH_CHECK_INTERVAL,
    AGENT_HEALTH_TIMEOUT,
    AGENT_PRIORITY_CRITICAL,
    AGENT_PRIORITY_HIGH,
    AGENT_PRIORITY_MEDIUM,
    AGENT_PRIORITY_LOW,
    QUICK_AGENT_TIMEOUT,
    LONG_AGENT_TIMEOUT,
    DEFAULT_RETRY_ATTEMPTS,
    RETRY_BACKOFF_BASE,
    MAX_AGENT_MEMORY_MB,
    ALLOWED_FILE_TYPES
)
from utils.types import AgentType, AgentStatus
from utils.adk_helpers import get_adk_helpers

# Service layer imports
from services.session_service import ADKSessionService
from services.memory_service import ADKMemoryService  
from services.model_service import ADKModelService


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
        
        # Service layer integration (real implementation)
        self._session_service: Optional[ADKSessionService] = None
        self._memory_service: Optional[ADKMemoryService] = None
        self._model_service: Optional[ADKModelService] = None
        
        # Configuration-driven behavior attributes (set by _apply_agent_configuration from YAML)
        self._execution_timeout: Optional[int] = None
        self._execution_priority: Optional[int] = None
        self._max_memory_mb: Optional[int] = None
        self._max_concurrent_operations: Optional[int] = None
        self._model_config: Dict[str, Any] = {}
        self._max_retries: Optional[int] = None
        self._retry_backoff_strategy: Optional[str] = None
        self._retry_base_delay: Optional[float] = None
        self._retry_max_delay: Optional[float] = None
        self._retry_backoff_base: Optional[int] = None
        self._max_execution_time: Optional[int] = None
        self._collect_metrics: Optional[bool] = None
        self._metrics_interval: Optional[int] = None
        self._performance_tracking: Optional[bool] = None
        self._resource_monitoring: Optional[bool] = None
        self._health_check_interval: Optional[int] = None
        self._health_timeout: Optional[int] = None
        self._max_failed_health_checks: Optional[int] = None
        self._validate_inputs: Optional[bool] = None
        self._sanitize_outputs: Optional[bool] = None
        self._max_input_size: Optional[int] = None
        self._allowed_file_types: Optional[List[str]] = None
        
        # Initialize services
        self._initialize_services()
        
        # Initialize tool orchestration
        self._load_tools()
        
        # Apply dynamic configuration-driven behavior
        self._apply_agent_configuration()
        
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
    
    def _initialize_services(self) -> None:
        """Initialize service layer components with error handling."""
        try:
            self.logger.info("Initializing service layer components...")
            
            # Initialize session service
            try:
                self._session_service = ADKSessionService()
                self.logger.info("Session service initialized successfully")
            except Exception as e:
                self.logger.error("Failed to initialize session service: %s", str(e))
                # Continue without session service - graceful degradation
                self._session_service = None
            
            # Initialize memory service  
            try:
                self._memory_service = ADKMemoryService()
                self.logger.info("Memory service initialized successfully")
            except Exception as e:
                self.logger.error("Failed to initialize memory service: %s", str(e))
                # Continue without memory service - graceful degradation
                self._memory_service = None
            
            # Initialize model service
            try:
                self._model_service = ADKModelService()
                self.logger.info("Model service initialized successfully")
            except Exception as e:
                self.logger.error("Failed to initialize model service: %s", str(e))
                # Continue without model service - graceful degradation
                self._model_service = None
            
            self.logger.info(
                "Service layer initialization completed - Session: %s, Memory: %s, Model: %s",
                bool(self._session_service),
                bool(self._memory_service), 
                bool(self._model_service)
            )
            
        except Exception as e:
            self.logger.error("Service layer initialization failed: %s", str(e))
            # Continue with degraded functionality
            self._session_service = None
            self._memory_service = None
            self._model_service = None
    
    def _validate_configuration(self) -> None:
        """Validate the loaded configuration."""
        required_fields = ['name', 'description', 'timeout']
        missing_fields = [field for field in required_fields if field not in self._config]
        
        if missing_fields:
            raise AgentConfigurationError(f"Missing required configuration fields: {missing_fields}")
        
        timeout = self._config.get('timeout', DEFAULT_AGENT_TIMEOUT)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise AgentConfigurationError(f"Invalid timeout value: {timeout}")
    
    def _apply_agent_configuration(self) -> None:
        """Apply agent-specific configuration dynamically to modify runtime behavior."""
        try:
            self.logger.info("Applying configuration-driven behavior for agent type: %s", self.agent_type.value)
            
            # Apply timeout configuration dynamically
            self._apply_timeout_configuration()
            
            # Apply priority-based execution ordering
            self._apply_priority_configuration()
            
            # Apply model configuration for LLM integration
            self._apply_model_configuration()
            
            # Apply retry strategy configuration
            self._apply_retry_configuration()
            
            # Apply performance and resource limits
            self._apply_resource_configuration()
            
            # Apply monitoring and metrics configuration
            self._apply_monitoring_configuration()
            
            # Apply security configuration
            self._apply_security_configuration()
            
            # Apply agent-specific analysis configuration
            self._apply_analysis_configuration()
            
            self.logger.info("Configuration-driven behavior applied successfully")
            
        except Exception as e:
            self.logger.error("Failed to apply agent configuration: %s", str(e))
            raise AgentConfigurationError(f"Configuration application failed: {e}") from e
    
    def _apply_timeout_configuration(self) -> None:
        """Apply dynamic timeout adjustment based on agent type and configuration."""
        # Get timeout from agent-specific config or use default
        agent_timeout = self._config.get('timeout', DEFAULT_AGENT_TIMEOUT)
        
        # Get ADK agent execution timeouts
        adk_execution = self._config.get('execution', {})
        default_timeout = adk_execution.get('default_timeout', DEFAULT_AGENT_TIMEOUT)
        quick_timeout = adk_execution.get('quick_timeout', QUICK_AGENT_TIMEOUT)
        long_timeout = adk_execution.get('long_timeout', LONG_AGENT_TIMEOUT)
        
        # Apply timeout based on agent priority and complexity
        priority = self._config.get('priority', AGENT_PRIORITY_MEDIUM)
        
        if priority == AGENT_PRIORITY_CRITICAL:  # Critical priority (Security Agent)
            self._execution_timeout = max(agent_timeout, long_timeout)
        elif priority == AGENT_PRIORITY_HIGH:  # High priority (Code Quality Agent)
            self._execution_timeout = max(agent_timeout, default_timeout)
        else:  # Medium/Low priority
            self._execution_timeout = min(agent_timeout, quick_timeout)
        
        # Apply tool-specific timeouts
        for tool_name, tool_config in self._tools.items():
            tool_timeout = tool_config.get('timeout', MAX_TOOL_EXECUTION_TIME)
            # Adjust tool timeout based on agent timeout
            adjusted_timeout = min(tool_timeout, self._execution_timeout * 0.8)
            tool_config['timeout'] = adjusted_timeout
        
        self.logger.info("Timeout configuration applied - Agent: %ds, Priority: %d", 
                        self._execution_timeout, priority)
    
    def _apply_priority_configuration(self) -> None:
        """Apply priority-based execution ordering and resource allocation."""
        priority = self._config.get('priority', AGENT_PRIORITY_MEDIUM)
        
        # Set execution priority for orchestration
        self._execution_priority = priority
        
        # Configure resource allocation based on priority
        resources = self._config.get('resources', {})
        base_memory = resources.get('max_memory_mb', MAX_AGENT_MEMORY_MB)
        
        if priority == AGENT_PRIORITY_CRITICAL:  # Critical - allocate more resources
            self._max_memory_mb = int(base_memory * 1.5)
            self._max_concurrent_operations = resources.get('max_concurrent_operations', 5)
        elif priority == AGENT_PRIORITY_HIGH:  # High - standard resources
            self._max_memory_mb = base_memory
            self._max_concurrent_operations = resources.get('max_concurrent_operations', 3)
        else:  # Medium/Low - conservative resources
            self._max_memory_mb = int(base_memory * 0.7)
            self._max_concurrent_operations = min(resources.get('max_concurrent_operations', 2), 2)
        
        self.logger.info("Priority configuration applied - Priority: %d, Memory: %dMB, Operations: %d",
                        priority, self._max_memory_mb, self._max_concurrent_operations)
    
    def _apply_model_configuration(self) -> None:
        """Apply model configuration for LLM integration."""
        # Get global model configuration
        global_model = self._config.get('global', {}).get('model', {})
        
        # Get agent-specific model overrides
        agent_model = self._config.get('model', {})
        
        # Merge model configuration
        self._model_config = {**global_model, **agent_model}
        
        # Apply default model settings if not specified
        if not self._model_config:
            self._model_config = {
                'provider': 'gemini',
                'model_name': 'gemini-1.5-pro',
                'temperature': 0.1,
                'max_tokens': 4096
            }
        
        # Adjust model parameters based on agent type
        if self.agent_type.value == 'security':
            # Security agent needs more conservative responses
            self._model_config['temperature'] = min(self._model_config.get('temperature', 0.1), 0.05)
        elif self.agent_type.value == 'code_quality':
            # Code quality agent can be slightly more creative
            self._model_config['temperature'] = min(self._model_config.get('temperature', 0.1), 0.15)
        
        self.logger.info("Model configuration applied - Provider: %s, Model: %s, Temperature: %.2f",
                        self._model_config.get('provider', 'unknown'),
                        self._model_config.get('model_name', 'unknown'),
                        self._model_config.get('temperature', 0.0))
    
    def _apply_retry_configuration(self) -> None:
        """Apply retry strategy configuration."""
        # Get global retry configuration
        global_retry = self._config.get('global', {}).get('retry', {})
        
        # Get agent-specific retry configuration
        agent_retry = self._config.get('retry', {})
        
        # Get ADK execution retry configuration
        execution_retry = self._config.get('execution', {})
        
        # Merge retry configurations
        retry_config = {**global_retry, **agent_retry}
        
        # Apply retry settings using constants as defaults
        self._max_retries = retry_config.get('max_attempts', execution_retry.get('max_retries', DEFAULT_RETRY_ATTEMPTS))
        self._retry_backoff_strategy = retry_config.get('backoff_strategy', 'exponential')
        self._retry_base_delay = retry_config.get('base_delay', 1.0)
        self._retry_max_delay = retry_config.get('max_delay', 60.0)
        self._retry_backoff_base = execution_retry.get('retry_backoff_base', RETRY_BACKOFF_BASE)
        
        self.logger.info("Retry configuration applied - Max retries: %d, Strategy: %s, Base delay: %.1fs",
                        self._max_retries, self._retry_backoff_strategy, self._retry_base_delay)
    
    def _apply_resource_configuration(self) -> None:
        """Apply performance and resource limits configuration."""
        resources = self._config.get('resources', {})
        
        # Apply resource limits
        self._max_execution_time = resources.get('max_execution_time', 600)
        
        # Ensure execution time doesn't exceed agent timeout (both should be set by now)
        if self._execution_timeout is not None:
            self._max_execution_time = min(self._max_execution_time, self._execution_timeout)
        
        # Apply concurrent operation limits (may have been set by priority configuration)
        if self._max_concurrent_operations is None:
            self._max_concurrent_operations = resources.get('max_concurrent_operations', 3)
        
        self.logger.info("Resource configuration applied - Max execution: %ds, Concurrent ops: %d",
                        self._max_execution_time, self._max_concurrent_operations)
    
    def _apply_monitoring_configuration(self) -> None:
        """Apply monitoring and metrics configuration."""
        monitoring = self._config.get('monitoring', {})
        
        # Apply monitoring settings using configuration values
        self._collect_metrics = monitoring.get('collect_metrics', True)
        self._metrics_interval = monitoring.get('metrics_interval', 60)
        self._performance_tracking = monitoring.get('performance_tracking', True)
        self._resource_monitoring = monitoring.get('resource_monitoring', True)
        
        # Apply health check configuration using constants as defaults
        health_config = self._config.get('health', {})
        self._health_check_interval = health_config.get('check_interval', AGENT_HEALTH_CHECK_INTERVAL)
        self._health_timeout = health_config.get('timeout', AGENT_HEALTH_TIMEOUT)
        self._max_failed_health_checks = health_config.get('max_failed_checks', 3)
        
        self.logger.info("Monitoring configuration applied - Metrics: %s, Tracking: %s, Health interval: %ds",
                        self._collect_metrics, self._performance_tracking, self._health_check_interval)
    
    def _apply_security_configuration(self) -> None:
        """Apply security configuration."""
        security = self._config.get('security', {})
        
        # Apply security settings using constants and configuration
        self._validate_inputs = security.get('validate_inputs', True)
        self._sanitize_outputs = security.get('sanitize_outputs', True)
        self._max_input_size = security.get('max_input_size', 10485760)  # 10MB from config
        self._allowed_file_types = security.get('allowed_file_types', ALLOWED_FILE_TYPES)
        
        self.logger.info("Security configuration applied - Input validation: %s, Output sanitization: %s",
                        self._validate_inputs, self._sanitize_outputs)
    
    def _apply_analysis_configuration(self) -> None:
        """Apply agent-specific analysis configuration."""
        analysis_config = self._config.get('analysis', {})
        
        if not analysis_config:
            self.logger.debug("No specific analysis configuration found for agent type: %s", self.agent_type.value)
            return
        
        # Apply analysis configuration based on agent type
        if self.agent_type.value == 'code_quality':
            self._apply_code_quality_analysis_config(analysis_config)
        elif self.agent_type.value == 'security':
            self._apply_security_analysis_config(analysis_config)
        elif self.agent_type.value == 'engineering_practices':
            self._apply_engineering_practices_analysis_config(analysis_config)
        
        self.logger.info("Analysis configuration applied for agent type: %s", self.agent_type.value)
    
    def _apply_code_quality_analysis_config(self, config: Dict[str, Any]) -> None:
        """Apply code quality specific analysis configuration."""
        self._complexity_threshold = config.get('complexity_threshold', 10)
        self._duplication_threshold = config.get('duplication_threshold', 0.1)
        self._maintainability_threshold = config.get('maintainability_threshold', 70.0)
        self._test_coverage_threshold = config.get('test_coverage_threshold', 80.0)
        
        # Apply metrics configuration
        self._metrics_to_collect = self._config.get('metrics', [
            'cyclomatic_complexity', 'cognitive_complexity', 'lines_of_code',
            'code_duplication', 'maintainability_index', 'technical_debt_ratio'
        ])
        
        # Apply quality rules
        rules = self._config.get('rules', {})
        self._max_function_length = rules.get('max_function_length', 50)
        self._max_class_length = rules.get('max_class_length', 300)
        self._max_parameters = rules.get('max_parameters', 5)
        self._max_nesting_depth = rules.get('max_nesting_depth', 4)
    
    def _apply_security_analysis_config(self, config: Dict[str, Any]) -> None:
        """Apply security specific analysis configuration."""
        self._vulnerability_scanning = config.get('vulnerability_scanning', True)
        self._secret_detection = config.get('secret_detection', True)
        self._dependency_check = config.get('dependency_check', True)
        self._code_injection_detection = config.get('code_injection_detection', True)
        
        # Apply risk thresholds
        thresholds = self._config.get('thresholds', {})
        self._critical_risk_threshold = thresholds.get('critical_risk', 90.0)
        self._high_risk_threshold = thresholds.get('high_risk', 70.0)
        self._medium_risk_threshold = thresholds.get('medium_risk', 40.0)
        self._low_risk_threshold = thresholds.get('low_risk', 20.0)
        
        # Apply security patterns
        self._security_patterns = self._config.get('patterns', [
            'sql_injection', 'xss_vulnerabilities', 'hardcoded_secrets',
            'insecure_random', 'weak_crypto', 'path_traversal'
        ])
    
    def _apply_engineering_practices_analysis_config(self, config: Dict[str, Any]) -> None:
        """Apply engineering practices specific analysis configuration."""
        practices = self._config.get('practices', {})
        
        # Apply testing practices configuration
        testing = practices.get('testing', {})
        self._check_unit_tests = testing.get('unit_tests', True)
        self._check_integration_tests = testing.get('integration_tests', True)
        self._check_test_naming = testing.get('test_naming', True)
        self._check_test_coverage = testing.get('test_coverage', True)
        
        # Apply error handling practices
        error_handling = practices.get('error_handling', {})
        self._check_exception_handling = error_handling.get('exception_handling', True)
        self._check_error_logging = error_handling.get('error_logging', True)
        self._check_graceful_degradation = error_handling.get('graceful_degradation', True)
        
        # Apply scoring weights
        scoring = self._config.get('scoring', {})
        self._testing_weight = scoring.get('testing', 0.3)
        self._error_handling_weight = scoring.get('error_handling', 0.2)
        self._logging_weight = scoring.get('logging', 0.15)
        self._documentation_weight = scoring.get('documentation', 0.2)
        self._performance_weight = scoring.get('performance', 0.15)
    
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
        """Set up session using real ADK session service."""
        try:
            if self._session_service:
                # Use real session service
                created_session_id = await self._session_service.create_session(
                    session_id=session_id,
                    correlation_id=self.correlation_id,
                    metadata={
                        'agent_id': self.agent_id,
                        'agent_type': self.agent_type.value,
                        'agent_name': self.name,
                        'created_by': 'BaseAgent',
                        'context': 'agent_execution'
                    }
                )
                
                # Retrieve session data
                session_data = await self._session_service.get_session(created_session_id)
                if session_data:
                    self._current_session = session_data
                    self.logger.info(
                        "Session setup completed via service - ID: %s, Status: %s",
                        session_id,
                        session_data.get('status', 'unknown')
                    )
                else:
                    raise AgentExecutionError(f"Failed to retrieve created session: {session_id}")
                
                # Allocate memory for session if memory service available
                if self._memory_service:
                    session_memory_data = {
                        'agent_context': {
                            'agent_id': self.agent_id,
                            'agent_type': self.agent_type.value,
                            'configuration': self._config,
                            'tools': list(self._tools.keys())
                        },
                        'execution_context': {
                            'correlation_id': self.correlation_id,
                            'session_id': session_id,
                            'start_time': datetime.now().isoformat()
                        }
                    }
                    
                    memory_allocated = await self._memory_service.allocate_session_memory(
                        session_id,
                        session_memory_data,
                        compress=True
                    )
                    
                    if memory_allocated:
                        self.logger.info("Session memory allocated successfully - ID: %s", session_id)
                    else:
                        self.logger.warning("Session memory allocation failed - ID: %s", session_id)
                
            else:
                # Fallback to in-memory session (graceful degradation)
                self._current_session = {
                    'session_id': session_id,
                    'correlation_id': self.correlation_id,
                    'status': AgentStatus.RUNNING.value,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'metadata': {
                        'agent_id': self.agent_id, 
                        'agent_type': self.agent_type.value,
                        'fallback_mode': True
                    }
                }
                self.logger.warning(
                    "Session setup using fallback mode - ID: %s (service unavailable)",
                    session_id
                )
                
        except Exception as e:
            self.logger.error("Session setup failed - ID: %s, Error: %s", session_id, str(e))
            raise AgentExecutionError(f"Failed to set up session: {e}") from e
    
    async def _cleanup_session(self) -> None:
        """Clean up session using real ADK session service."""
        try:
            if self._current_session:
                session_id = self._current_session.get('session_id')
                
                if self._session_service and session_id:
                    # Update session status to completed
                    await self._session_service.update_session(
                        session_id,
                        {
                            'completion_time': datetime.now().isoformat(),
                            'final_status': self.status.value,
                            'metrics': self._metrics
                        },
                        status=None  # Let service determine final status
                    )
                    
                    # Deallocate session memory if memory service available
                    if self._memory_service:
                        memory_freed = await self._memory_service.deallocate_session_memory(session_id)
                        if memory_freed:
                            self.logger.info("Session memory deallocated - ID: %s", session_id)
                        else:
                            self.logger.warning("Session memory deallocation failed - ID: %s", session_id)
                    
                    # Delete session (optional - depends on retention policy)
                    session_deleted = await self._session_service.delete_session(session_id)
                    if session_deleted:
                        self.logger.info("Session cleanup completed via service - ID: %s", session_id)
                    else:
                        self.logger.warning("Session deletion failed - ID: %s", session_id)
                        
                else:
                    # Fallback cleanup
                    self.logger.info("Session cleanup completed (fallback mode) - ID: %s", session_id)
                
                # Clear local session data
                self._current_session = None
                self._session_data.clear()
                
        except Exception as e:
            self.logger.warning("Session cleanup failed - Error: %s", str(e))
            # Clear local data even if service cleanup fails
            self._current_session = None
            self._session_data.clear()
    
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
        """Perform agent health check including service layer status and configuration-driven behavior."""
        try:
            # Base health status
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
                },
                'configuration_driven_behavior': {
                    'execution_timeout': self._execution_timeout or 0,
                    'execution_priority': self._execution_priority or 0,
                    'max_memory_mb': self._max_memory_mb or 0,
                    'max_concurrent_operations': self._max_concurrent_operations or 0,
                    'model_provider': self._model_config.get('provider', 'not_configured'),
                    'model_name': self._model_config.get('model_name', 'not_configured'),
                    'model_temperature': self._model_config.get('temperature', 0.0),
                    'max_retries': self._max_retries or 0,
                    'retry_strategy': self._retry_backoff_strategy or 'not_configured',
                    'metrics_collection': self._collect_metrics or False,
                    'performance_tracking': self._performance_tracking or False,
                    'resource_monitoring': self._resource_monitoring or False,
                    'health_check_interval': self._health_check_interval or 0,
                    'input_validation': self._validate_inputs or False,
                    'output_sanitization': self._sanitize_outputs or False,
                    'max_input_size_mb': (self._max_input_size or 0) / 1048576,  # Convert to MB
                    'allowed_file_types_count': len(self._allowed_file_types or [])
                }
            }
            
            # Service layer health checks
            service_health = {
                'session_service': {'status': 'unavailable', 'error': 'Not initialized'},
                'memory_service': {'status': 'unavailable', 'error': 'Not initialized'},
                'model_service': {'status': 'unavailable', 'error': 'Not initialized'}
            }
            
            # Check session service health
            if self._session_service:
                try:
                    session_health = await self._session_service.health_check()
                    service_health['session_service'] = session_health
                except Exception as e:
                    service_health['session_service'] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            
            # Check memory service health
            if self._memory_service:
                try:
                    memory_health = await self._memory_service.health_check()
                    service_health['memory_service'] = memory_health
                except Exception as e:
                    service_health['memory_service'] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            
            # Check model service health
            if self._model_service:
                try:
                    model_health = await self._model_service.health_check()
                    service_health['model_service'] = model_health
                except Exception as e:
                    service_health['model_service'] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            
            # Add service health to overall status
            health_status['service_layer'] = service_health
            
            # Determine overall health based on services
            service_statuses = [s.get('status', 'unknown') for s in service_health.values()]
            unhealthy_services = [s for s in service_statuses if s in ['unhealthy', 'degraded']]
            
            if unhealthy_services:
                if len(unhealthy_services) == len(service_statuses):
                    health_status['status'] = 'degraded'  # All services have issues
                else:
                    health_status['status'] = 'healthy'  # Some services still working
            
            self.logger.info(
                "Health check completed - Status: %s, Tools: %d, Services: %s",
                health_status['status'],
                len(self._tools),
                {k: v.get('status', 'unknown') for k, v in service_health.items()}
            )
            
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
                },
                'service_layer': {
                    'session_service': {'status': 'unknown', 'error': 'Health check failed'},
                    'memory_service': {'status': 'unknown', 'error': 'Health check failed'},
                    'model_service': {'status': 'unknown', 'error': 'Health check failed'}
                }
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive agent information including service layer details."""
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
            },
            'service_layer': {
                'session_service_available': self._session_service is not None,
                'memory_service_available': self._memory_service is not None,
                'model_service_available': self._model_service is not None,
                'session_service_type': type(self._session_service).__name__ if self._session_service else None,
                'memory_service_type': type(self._memory_service).__name__ if self._memory_service else None,
                'model_service_type': type(self._model_service).__name__ if self._model_service else None
            }
        }

    async def shutdown(self) -> None:
        """Shutdown the agent and all service layer components."""
        try:
            self.logger.info("Shutting down agent - ID: %s", self.agent_id)
            
            # Clean up current session if active
            if self._current_session:
                await self._cleanup_session()
            
            # Shutdown service layer components
            if self._session_service:
                try:
                    await self._session_service.shutdown()
                    self.logger.info("Session service shutdown completed")
                except Exception as e:
                    self.logger.warning("Session service shutdown failed: %s", str(e))
            
            if self._memory_service:
                try:
                    await self._memory_service.shutdown()
                    self.logger.info("Memory service shutdown completed")
                except Exception as e:
                    self.logger.warning("Memory service shutdown failed: %s", str(e))
            
            if self._model_service:
                try:
                    await self._model_service.shutdown()
                    self.logger.info("Model service shutdown completed")
                except Exception as e:
                    self.logger.warning("Model service shutdown failed: %s", str(e))
            
            # Clear agent state
            self.status = AgentStatus.CANCELLED
            self._tools.clear()
            self._tool_registry.clear()
            self._function_tools.clear()
            self._session_data.clear()
            
            self.logger.info("Agent shutdown completed - ID: %s", self.agent_id)
            
        except Exception as e:
            self.logger.error("Agent shutdown failed - ID: %s, Error: %s", self.agent_id, str(e))
    
    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics from all service layer components and configuration-driven behavior."""
        try:
            metrics = {
                'agent_metrics': self._metrics,
                'session_service_metrics': None,
                'memory_service_metrics': None, 
                'model_service_metrics': None,
                'configuration_metrics': {
                    'execution_timeout_seconds': self._execution_timeout or 0,
                    'execution_priority': self._execution_priority or 0,
                    'memory_limit_mb': self._max_memory_mb or 0,
                    'concurrent_operations_limit': self._max_concurrent_operations or 0,
                    'max_execution_time_seconds': self._max_execution_time or 0,
                    'retry_attempts_configured': self._max_retries or 0,
                    'retry_strategy': self._retry_backoff_strategy or 'not_configured',
                    'retry_base_delay_seconds': self._retry_base_delay or 0.0,
                    'retry_max_delay_seconds': self._retry_max_delay or 0.0,
                    'metrics_collection_enabled': self._collect_metrics or False,
                    'performance_tracking_enabled': self._performance_tracking or False,
                    'resource_monitoring_enabled': self._resource_monitoring or False,
                    'health_check_interval_seconds': self._health_check_interval or 0,
                    'health_timeout_seconds': self._health_timeout or 0,
                    'max_failed_health_checks': self._max_failed_health_checks or 0,
                    'input_validation_enabled': self._validate_inputs or False,
                    'output_sanitization_enabled': self._sanitize_outputs or False,
                    'max_input_size_bytes': self._max_input_size or 0,
                    'allowed_file_types_count': len(self._allowed_file_types or []),
                    'model_configuration': {
                        'provider': self._model_config.get('provider', 'not_configured'),
                        'model_name': self._model_config.get('model_name', 'not_configured'),
                        'temperature': self._model_config.get('temperature', 0.0),
                        'max_tokens': self._model_config.get('max_tokens', 0)
                    }
                }
            }
            
            # Get session service metrics
            if self._session_service:
                try:
                    metrics['session_service_metrics'] = self._session_service.metrics
                except Exception as e:
                    self.logger.warning("Failed to get session service metrics: %s", str(e))
            
            # Get memory service metrics
            if self._memory_service:
                try:
                    metrics['memory_service_metrics'] = self._memory_service.stats
                except Exception as e:
                    self.logger.warning("Failed to get memory service metrics: %s", str(e))
            
            # Get model service metrics
            if self._model_service:
                try:
                    metrics['model_service_metrics'] = self._model_service.metrics
                except Exception as e:
                    self.logger.warning("Failed to get model service metrics: %s", str(e))
            
            return metrics
            
        except Exception as e:
            self.logger.error("Failed to get service metrics: %s", str(e))
            return {'error': str(e), 'agent_metrics': self._metrics}
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration-driven behavior settings."""
        return {
            'agent_info': {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type.value,
                'status': self.status.value,
                'configuration_applied': True
            },
            'execution_configuration': {
                'timeout_seconds': self._execution_timeout or 0,
                'priority': self._execution_priority or 0,
                'max_execution_time_seconds': self._max_execution_time or 0,
                'max_concurrent_operations': self._max_concurrent_operations or 0
            },
            'resource_configuration': {
                'max_memory_mb': self._max_memory_mb or 0,
                'max_input_size_mb': (self._max_input_size or 0) / 1048576,
                'allowed_file_types': self._allowed_file_types or []
            },
            'retry_configuration': {
                'max_retries': self._max_retries or 0,
                'strategy': self._retry_backoff_strategy or 'not_configured',
                'base_delay_seconds': self._retry_base_delay or 0.0,
                'max_delay_seconds': self._retry_max_delay or 0.0,
                'backoff_base': self._retry_backoff_base or 0
            },
            'model_configuration': self._model_config,
            'monitoring_configuration': {
                'collect_metrics': self._collect_metrics or False,
                'metrics_interval_seconds': self._metrics_interval or 0,
                'performance_tracking': self._performance_tracking or False,
                'resource_monitoring': self._resource_monitoring or False,
                'health_check_interval_seconds': self._health_check_interval or 0,
                'health_timeout_seconds': self._health_timeout or 0,
                'max_failed_health_checks': self._max_failed_health_checks or 0
            },
            'security_configuration': {
                'input_validation': self._validate_inputs or False,
                'output_sanitization': self._sanitize_outputs or False,
                'max_input_size_bytes': self._max_input_size or 0,
                'allowed_file_types_count': len(self._allowed_file_types or [])
            }
        }
    
    def get_execution_timeout(self) -> int:
        """Get the configured execution timeout for this agent."""
        if self._execution_timeout is None:
            self.logger.warning("Execution timeout not configured, returning default")
            return DEFAULT_AGENT_TIMEOUT
        return self._execution_timeout
    
    def get_execution_priority(self) -> int:
        """Get the configured execution priority for this agent."""
        if self._execution_priority is None:
            self.logger.warning("Execution priority not configured, returning default")
            return AGENT_PRIORITY_MEDIUM
        return self._execution_priority
    
    def get_model_configuration(self) -> Dict[str, Any]:
        """Get the model configuration for LLM integration."""
        return self._model_config.copy()
    
    def get_retry_configuration(self) -> Dict[str, Any]:
        """Get the retry strategy configuration."""
        return {
            'max_retries': self._max_retries or DEFAULT_RETRY_ATTEMPTS,
            'strategy': self._retry_backoff_strategy or 'exponential',
            'base_delay': self._retry_base_delay or 1.0,
            'max_delay': self._retry_max_delay or 60.0,
            'backoff_base': self._retry_backoff_base or RETRY_BACKOFF_BASE
        }
    
    def get_resource_limits(self) -> Dict[str, Any]:
        """Get the resource limits configuration."""
        return {
            'max_memory_mb': self._max_memory_mb or MAX_AGENT_MEMORY_MB,
            'max_execution_time_seconds': self._max_execution_time or 600,
            'max_concurrent_operations': self._max_concurrent_operations or 3,
            'max_input_size_bytes': self._max_input_size or 10485760
        }
    
    def is_metrics_collection_enabled(self) -> bool:
        """Check if metrics collection is enabled."""
        return self._collect_metrics if self._collect_metrics is not None else True
    
    def is_performance_tracking_enabled(self) -> bool:
        """Check if performance tracking is enabled."""
        return self._performance_tracking if self._performance_tracking is not None else True
    
    def is_input_validation_enabled(self) -> bool:
        """Check if input validation is enabled."""
        return self._validate_inputs if self._validate_inputs is not None else True
    
    def is_output_sanitization_enabled(self) -> bool:
        """Check if output sanitization is enabled."""
        return self._sanitize_outputs if self._sanitize_outputs is not None else True
    
    def get_allowed_file_types(self) -> List[str]:
        """Get the list of allowed file types."""
        if self._allowed_file_types is None:
            self.logger.warning("Allowed file types not configured, returning default")
            return ALLOWED_FILE_TYPES.copy()
        return self._allowed_file_types.copy()
    
    def validate_input_size(self, input_size: int) -> bool:
        """Validate if input size is within configured limits."""
        max_size = self._max_input_size if self._max_input_size is not None else 10485760  # 10MB default
        return input_size <= max_size
    
    def validate_file_type(self, file_extension: str) -> bool:
        """Validate if file type is allowed based on configuration."""
        allowed_types = self._allowed_file_types if self._allowed_file_types is not None else ALLOWED_FILE_TYPES
        return file_extension.lower() in [ft.lower() for ft in allowed_types]
