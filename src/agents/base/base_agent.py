"""
Base Agent - Comprehensive Foundation

Enhanced foundation class for all analysis agents with memory integration,
AGDK support, and advanced learning capabilities. Provides a unified interface
for specialized agents with configurable feature sets.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FindingSeverity(Enum):
    """Severity levels for analysis findings."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


@dataclass
class Finding:
    """Represents an analysis finding."""
    id: str
    title: str
    description: str
    severity: FindingSeverity
    category: str
    file_path: str
    line_number: Optional[int]
    column_number: Optional[int]
    code_snippet: Optional[str]
    recommendation: str
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class AnalysisContext:
    """Context for analysis execution."""
    files: List[Dict[str, Any]]
    configuration: Dict[str, Any]
    session_id: str
    metadata: Dict[str, Any]


@dataclass
class AnalysisResult:
    """Result of agent analysis."""
    agent_name: str
    findings: List[Finding]
    metrics: Dict[str, float]
    execution_time: float
    success: bool
    errors: List[str]
    metadata: Dict[str, Any]


class BaseAgent(ABC):
    """
    Enhanced base class for all analysis agents with memory integration and AGDK support.
    
    Features:
    - Memory-aware analysis with pattern learning
    - AGDK integration for tool-based execution
    - Configurable feature enablement
    - Comprehensive quality control and bias prevention
    - Historical accuracy tracking and confidence calibration
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the enhanced base agent with configuration-driven setup."""
        self.name = name
        
        # Initialize configuration management
        self._load_agent_configuration(config)
        
        self.version = "2.0.0"  # Enhanced version with memory + AGDK
        
        # Agent capabilities
        self.capabilities = self._define_capabilities()
        
        # Analysis state
        self._current_context: Optional[AnalysisContext] = None
        self._findings: List[Finding] = []
        
        # Load configuration-driven features
        self._setup_configuration_driven_features()
        
        # Initialize components based on configuration
        if self.memory_enabled:
            self._initialize_memory_components()
        
        if self.agdk_enabled:
            self._initialize_agdk_components()
        
        logger.info(f"Initialized {self.name} v{self.version} - Memory: {self.memory_enabled}, AGDK: {self.agdk_enabled}")
    
    def _load_agent_configuration(self, provided_config: Optional[Dict[str, Any]] = None):
        """Load agent configuration from multiple sources with proper precedence."""
        try:
            # Initialize configuration manager
            from ...core.config.config_manager import ConfigManager
            self.config_manager = ConfigManager()
            
            # Load base agent configuration from YAML
            base_config = self.config_manager.get_agent_config("base_agent")
            
            # Merge with provided configuration (provided config takes precedence)
            self.config = base_config.copy() if base_config else {}
            if provided_config:
                self._deep_merge_config(self.config, provided_config)
            
            logger.debug(f"Loaded configuration for {self.name}: {len(self.config)} sections")
            
        except Exception as e:
            logger.warning(f"Failed to load configuration for {self.name}: {e}")
            # Fallback to provided config or empty config
            self.config = provided_config or {}
            self.config_manager = None
    
    def _deep_merge_config(self, base_config: Dict[str, Any], override_config: Dict[str, Any]):
        """Deep merge configuration dictionaries."""
        for key, value in override_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._deep_merge_config(base_config[key], value)
            else:
                base_config[key] = value
    
    def _setup_configuration_driven_features(self):
        """Setup features based on configuration with validation."""
        # Behavior configuration
        behavior_config = self.config.get("behavior", {})
        self.default_timeout = behavior_config.get("default_timeout", 300)
        self.max_retry_attempts = behavior_config.get("max_retry_attempts", 3)
        self.confidence_threshold = behavior_config.get("confidence_threshold", 0.7)
        self.max_findings_per_file = behavior_config.get("max_findings_per_file", 25)
        
        # Memory integration configuration
        self.memory_enabled = behavior_config.get("enable_memory_integration", True)
        self.memory_retrieval_limit = behavior_config.get("memory_retrieval_limit", 50)
        self.memory_confidence_threshold = behavior_config.get("memory_confidence_threshold", 0.6)
        
        # Learning configuration
        self.learning_enabled = behavior_config.get("enable_learning", True)
        self.pattern_storage_enabled = behavior_config.get("enable_pattern_storage", True)
        self.feedback_integration_enabled = behavior_config.get("enable_feedback_integration", True)
        
        # Quality control configuration
        quality_config = self.config.get("quality_control", {})
        self.hallucination_prevention_config = quality_config.get("hallucination_prevention", {})
        self.bias_prevention_config = quality_config.get("bias_prevention", {})
        self.output_validation_config = quality_config.get("output_validation", {})
        self.quality_gates_config = quality_config.get("quality_gates", {})
        
        # LLM interaction configuration
        llm_config = self.config.get("llm_interaction", {})
        self.prompting_config = llm_config.get("prompting", {})
        self.response_validation_config = llm_config.get("response_validation", {})
        self.error_handling_config = llm_config.get("error_handling", {})
        
        # Performance configuration
        performance_config = self.config.get("performance", {})
        self.caching_config = performance_config.get("caching", {})
        self.resource_management_config = performance_config.get("resource_management", {})
        self.parallel_processing_config = performance_config.get("parallel_processing", {})
        
        # Monitoring configuration
        monitoring_config = self.config.get("monitoring", {})
        self.execution_tracking_config = monitoring_config.get("execution_tracking", {})
        self.performance_metrics_config = monitoring_config.get("performance_metrics", {})
        self.error_reporting_config = monitoring_config.get("error_reporting", {})
        
        # Integration configuration
        integration_config = self.config.get("integration", {})
        self.memory_integration_config = integration_config.get("memory_integration", {})
        self.state_management_config = integration_config.get("state_management", {})
        self.orchestration_config = integration_config.get("orchestration", {})
        
        # AGDK configuration
        agdk_config = self.config.get("agdk", {})
        self.agdk_enabled = agdk_config.get("enabled", False)
        self.agdk_use_config_manager = agdk_config.get("use_config_manager", True)
        self.agdk_events_config = agdk_config.get("events", {})
        self.agdk_tools_config = agdk_config.get("tools", {})
        
        # Initialize state containers
        self._learned_patterns: List[Dict[str, Any]] = []
        self._historical_accuracy: Dict[str, float] = {}
        
        # AGDK state initialization
        self._agdk_session_id: Optional[str] = None
        self._agdk_session = None
        self._agdk_tools_registered = False
        self._agdk_event_handlers: Dict[str, Any] = {}
        self._agdk_session_state: Dict[str, Any] = {}
        self._agdk_events_processed = 0
        self._agdk_errors_count = 0
        self._agdk_event_stats: Dict[str, Dict[str, int]] = {}
        self._agdk_tool_instances: Dict[str, Any] = {}
        self._agdk_last_state = 'unknown'
        
        logger.debug(f"Feature setup completed for {self.name}")
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            "name": self.name,
            "version": self.version,
            "memory_enabled": self.memory_enabled,
            "agdk_enabled": self.agdk_enabled,
            "learning_enabled": self.learning_enabled,
            "confidence_threshold": self.confidence_threshold,
            "max_findings_per_file": self.max_findings_per_file,
            "default_timeout": self.default_timeout,
            "quality_controls": {
                "hallucination_prevention": self.hallucination_prevention_config.get("enable_fact_checking", False),
                "bias_prevention": self.bias_prevention_config.get("enable_diverse_perspectives", False),
                "output_validation": self.output_validation_config.get("validate_finding_structure", False)
            },
            "performance": {
                "caching_enabled": self.caching_config.get("enable_result_caching", False),
                "parallel_processing": self.parallel_processing_config.get("enable_file_level_parallelism", False)
            },
            "monitoring": {
                "execution_tracking": self.execution_tracking_config.get("log_analysis_start", False),
                "performance_metrics": self.performance_metrics_config.get("track_execution_time", False)
            }
        }
    
    def _initialize_memory_components(self):
        """Initialize memory integration components."""
        # TODO: Initialize actual memory components when implemented
        logger.debug(f"Memory components initialized for {self.name}")
    
    def _initialize_agdk_components(self):
        """Initialize AGDK integration components with real Google Cloud services."""
        try:
            # Import AGDK components
            from ...integrations.agdk import (
                AGDKRuntimeFactory,
                AGDKCredentialManager,
                create_runtime_config_from_config_manager
            )
            from ...core.config.config_manager import ConfigManager
            
            logger.info(f"Initializing AGDK components for {self.name}")
            
            # Ensure configuration manager is available
            if not self.config_manager:
                logger.error(f"No configuration manager available for AGDK initialization in {self.name}")
                self.agdk_enabled = False
                return
            
            # Initialize credential manager
            self._agdk_credential_manager = AGDKCredentialManager()
            
            # Load and validate credentials
            if not self._agdk_credential_manager.load_credentials():
                logger.error(f"Failed to load AGDK credentials for {self.name}")
                self.agdk_enabled = False
                return
            
            if not self._agdk_credential_manager.validate_credentials():
                logger.error(f"AGDK credentials validation failed for {self.name}")
                self.agdk_enabled = False
                return
            
            # Initialize runtime factory
            self._agdk_runtime_factory = AGDKRuntimeFactory(self.config_manager)
            
            # Create runtime configuration
            agdk_config = self.config.get('agdk', {})
            if agdk_config.get('use_config_manager', True):
                self._agdk_runtime_config = create_runtime_config_from_config_manager(self.config_manager)
            else:
                # Fallback to environment-based configuration
                from ...integrations.agdk import create_runtime_config_from_env
                self._agdk_runtime_config = create_runtime_config_from_env()
            
            # Initialize the AGDK runtime
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Initialize runtime in async context
            initialization_successful = loop.run_until_complete(
                self._agdk_runtime_factory.initialize_runtime(self._agdk_runtime_config)
            )
            
            if not initialization_successful:
                logger.error(f"AGDK runtime initialization failed for {self.name}")
                self.agdk_enabled = False
                return
            
            # Initialize agent-specific AGDK state
            self._agdk_session_id = None
            self._agdk_session = None
            self._agdk_tools_registered = False
            self._agdk_event_handlers = {}
            
            # Register default event handlers
            self._register_agdk_event_handlers()
            
            logger.info(f"AGDK components successfully initialized for {self.name}")
            
        except ImportError as e:
            logger.error(f"AGDK integration dependencies not available for {self.name}: {e}")
            self.agdk_enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize AGDK components for {self.name}: {e}")
            self.agdk_enabled = False
    
    @abstractmethod
    def _define_capabilities(self) -> List[str]:
        """Define the capabilities of this agent."""
        pass
    
    @abstractmethod
    def analyze(self, context: AnalysisContext) -> AnalysisResult:
        """Perform basic analysis on the given context."""
        pass
    
    def analyze_with_memory(self, context: AnalysisContext) -> AnalysisResult:
        """Perform memory-enhanced analysis."""
        try:
            # Store current context
            self._current_context = context
            self.clear_findings()
            
            # Retrieve relevant memory context
            memory_context = self._retrieve_memory_context(context)
            
            # Enhance context with memory
            enhanced_context = self._enhance_context_with_memory(context, memory_context)
            
            # Perform core analysis
            result = self.analyze(enhanced_context)
            
            # Learn from analysis results
            self._learn_from_analysis(context, result)
            
            # Enhance findings with memory insights
            enhanced_findings = self._enhance_findings_with_memory(result.findings, memory_context)
            
            # Update result with enhanced findings
            result.findings = enhanced_findings
            result.metadata.update({
                "memory_enhanced": True,
                "learned_patterns_count": len(self._learned_patterns),
                "memory_context_items": len(memory_context)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Memory-enhanced analysis failed for {self.name}: {e}")
            # Fallback to regular analysis
            return self.analyze(context)
    
    def execute_analysis(self, context: AnalysisContext) -> AnalysisResult:
        """Main analysis entry point with intelligent routing."""
        if self.memory_enabled:
            return self.analyze_with_memory(context)
        else:
            return self.analyze(context)
    
    # AGDK Integration Methods
    def on_session_started(self, session_data: Dict[str, Any]):
        """Handle AGDK session start event with real session initialization."""
        if not self.agdk_enabled:
            logger.debug(f"AGDK not enabled for {self.name}, skipping session start")
            return
        
        try:
            session_id = session_data.get('session_id')
            if not session_id:
                logger.error(f"No session_id provided in session_data for {self.name}")
                return
            
            logger.info(f"Starting AGDK session {session_id} for {self.name}")
            
            # Create AGDK session
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Create session with runtime factory
            self._agdk_session = loop.run_until_complete(
                self._agdk_runtime_factory.create_session(session_id, self._agdk_runtime_config)
            )
            
            if not self._agdk_session:
                logger.error(f"Failed to create AGDK session {session_id} for {self.name}")
                return
            
            self._agdk_session_id = session_id
            
            # Register agent-specific tools with the session
            self._register_agdk_tools()
            
            # Set up session-specific configuration
            self._configure_agdk_session(session_data)
            
            # Initialize session state
            self._agdk_session_state = {
                'started_at': self._get_timestamp(),
                'analysis_count': 0,
                'tools_registered': self._agdk_tools_registered,
                'session_metadata': session_data.get('metadata', {})
            }
            
            logger.info(f"AGDK session {session_id} successfully started for {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to start AGDK session for {self.name}: {e}")
            self._agdk_session = None
            self._agdk_session_id = None
    
    def on_session_finished(self, session_data: Dict[str, Any]):
        """Handle AGDK session finish event with proper cleanup and resource management."""
        if not self.agdk_enabled:
            logger.debug(f"AGDK not enabled for {self.name}, skipping session finish")
            return
        
        try:
            session_id = session_data.get('session_id', self._agdk_session_id)
            if not session_id:
                logger.warning(f"No session_id provided for session finish in {self.name}")
                return
            
            logger.info(f"Finishing AGDK session {session_id} for {self.name}")
            
            # Collect session statistics before cleanup
            session_stats = self._collect_agdk_session_stats()
            
            # Perform cleanup operations
            self._cleanup_agdk_session_resources()
            
            # Close the AGDK session
            if self._agdk_session and self._agdk_runtime_factory:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                session_closed = loop.run_until_complete(
                    self._agdk_runtime_factory.close_session(session_id)
                )
                
                if session_closed:
                    logger.info(f"AGDK session {session_id} successfully closed for {self.name}")
                else:
                    logger.warning(f"Failed to properly close AGDK session {session_id} for {self.name}")
            
            # Reset session state
            self._agdk_session = None
            self._agdk_session_id = None
            self._agdk_tools_registered = False
            self._agdk_session_state = {}
            
            # Log session completion with statistics
            logger.info(f"AGDK session {session_id} completed for {self.name}. Stats: {session_stats}")
            
        except Exception as e:
            logger.error(f"Error during AGDK session finish for {self.name}: {e}")
            # Force cleanup even if error occurred
            try:
                self._force_cleanup_agdk_session()
            except Exception as cleanup_error:
                logger.error(f"Force cleanup failed for {self.name}: {cleanup_error}")
    
    def handle_agdk_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle AGDK events with comprehensive event processing and tool coordination."""
        if not self.agdk_enabled:
            logger.debug(f"AGDK not enabled for {self.name}, ignoring event {event_type}")
            return
        
        try:
            logger.debug(f"Handling AGDK event '{event_type}' for {self.name}")
            
            # Get event handler configuration
            event_config = self.config.get('agdk', {}).get('events', {}).get(event_type, {})
            
            # Check if this event type is enabled for this agent
            if not event_config.get('enabled', True):
                logger.debug(f"Event type '{event_type}' disabled for {self.name}")
                return
            
            # Validate event data
            if not self._validate_agdk_event_data(event_type, event_data):
                logger.warning(f"Invalid event data for '{event_type}' in {self.name}")
                return
            
            # Handle different event types
            event_result = None
            
            if event_type == "tool_execution_requested":
                event_result = self._handle_tool_execution_event(event_data)
            elif event_type == "analysis_started":
                event_result = self._handle_analysis_started_event(event_data)
            elif event_type == "analysis_completed":
                event_result = self._handle_analysis_completed_event(event_data)
            elif event_type == "tool_result_available":
                event_result = self._handle_tool_result_event(event_data)
            elif event_type == "error_occurred":
                event_result = self._handle_error_event(event_data)
            elif event_type == "session_state_changed":
                event_result = self._handle_session_state_event(event_data)
            elif event_type == "coordination_request":
                event_result = self._handle_coordination_request_event(event_data)
            else:
                # Handle custom or unknown events
                event_result = self._handle_custom_agdk_event(event_type, event_data)
            
            # Log event processing result
            if event_result:
                logger.debug(f"Event '{event_type}' processed successfully for {self.name}: {event_result}")
            else:
                logger.debug(f"Event '{event_type}' processed for {self.name} (no result)")
            
            # Update event statistics
            self._update_agdk_event_stats(event_type, event_result is not None)
            
        except Exception as e:
            logger.error(f"Error handling AGDK event '{event_type}' for {self.name}: {e}")
            # Report error back to AGDK system if configured
            self._report_agdk_event_error(event_type, event_data, e)
    
    def get_agdk_tools(self) -> List[str]:
        """Get list of AGDK tools provided by this agent."""
        # Base implementation - to be overridden by specific agents
        return ["base_quality_validator", "base_bias_checker", "base_evidence_validator"]
    
    # AGDK Helper Methods
    def _register_agdk_event_handlers(self):
        """Register default AGDK event handlers."""
        self._agdk_event_handlers = {
            "tool_execution_requested": self._handle_tool_execution_event,
            "analysis_started": self._handle_analysis_started_event,
            "analysis_completed": self._handle_analysis_completed_event,
            "tool_result_available": self._handle_tool_result_event,
            "error_occurred": self._handle_error_event,
            "session_state_changed": self._handle_session_state_event,
            "coordination_request": self._handle_coordination_request_event
        }
        logger.debug(f"Registered {len(self._agdk_event_handlers)} AGDK event handlers for {self.name}")
    
    def _register_agdk_tools(self):
        """Register agent-specific tools with the AGDK session."""
        try:
            if not self._agdk_session or not self._agdk_runtime_factory:
                logger.warning(f"Cannot register tools - no active AGDK session for {self.name}")
                return
            
            # Get tools from agent implementation
            agent_tools = self.get_agdk_tools()
            
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Register each tool with the session
            registered_count = 0
            for tool_name in agent_tools:
                if not self._agdk_session_id:
                    logger.error(f"No session ID available for tool registration in {self.name}")
                    break
                    
                tool_instance = self._create_agdk_tool_instance(tool_name)
                if tool_instance:
                    success = loop.run_until_complete(
                        self._agdk_runtime_factory.register_tool(
                            self._agdk_session_id, tool_name, tool_instance
                        )
                    )
                    if success:
                        registered_count += 1
                        logger.debug(f"Registered AGDK tool '{tool_name}' for {self.name}")
                    else:
                        logger.warning(f"Failed to register AGDK tool '{tool_name}' for {self.name}")
                else:
                    logger.warning(f"Could not create tool instance for '{tool_name}' in {self.name}")
            
            self._agdk_tools_registered = registered_count > 0
            logger.info(f"Registered {registered_count}/{len(agent_tools)} AGDK tools for {self.name}")
            
        except Exception as e:
            logger.error(f"Error registering AGDK tools for {self.name}: {e}")
            self._agdk_tools_registered = False
    
    def _create_agdk_tool_instance(self, tool_name: str) -> Optional[Any]:
        """Create an instance of the specified AGDK tool."""
        # Base implementation - to be extended by specific agents
        if tool_name == "base_quality_validator":
            return self._create_quality_validator_tool()
        elif tool_name == "base_bias_checker":
            return self._create_bias_checker_tool()
        elif tool_name == "base_evidence_validator":
            return self._create_evidence_validator_tool()
        else:
            logger.warning(f"Unknown tool '{tool_name}' requested for {self.name}")
            return None
    
    def _create_quality_validator_tool(self) -> Any:
        """Create quality validator tool instance."""
        # Implementation will be added when tool framework is ready
        return {"name": "base_quality_validator", "type": "validator", "agent": self.name}
    
    def _create_bias_checker_tool(self) -> Any:
        """Create bias checker tool instance."""
        # Implementation will be added when tool framework is ready
        return {"name": "base_bias_checker", "type": "validator", "agent": self.name}
    
    def _create_evidence_validator_tool(self) -> Any:
        """Create evidence validator tool instance."""
        # Implementation will be added when tool framework is ready
        return {"name": "base_evidence_validator", "type": "validator", "agent": self.name}
    
    def _configure_agdk_session(self, session_data: Dict[str, Any]):
        """Configure AGDK session with agent-specific settings."""
        try:
            # Apply agent-specific configuration from config
            agdk_config = self.config.get('agdk', {})
            session_config = agdk_config.get('session', {})
            
            # Configure session timeout
            session_timeout = session_config.get('timeout', 3600)
            
            # Configure tool execution settings
            tool_config = session_config.get('tools', {})
            
            # Configure monitoring and logging
            monitoring_config = session_config.get('monitoring', {})
            
            # Store configuration in session state
            if hasattr(self, '_agdk_session_state'):
                self._agdk_session_state.update({
                    'session_timeout': session_timeout,
                    'tool_config': tool_config,
                    'monitoring_config': monitoring_config
                })
            
            logger.debug(f"AGDK session configured for {self.name}")
            
        except Exception as e:
            logger.error(f"Error configuring AGDK session for {self.name}: {e}")
    
    def _collect_agdk_session_stats(self) -> Dict[str, Any]:
        """Collect statistics from the current AGDK session."""
        try:
            if not hasattr(self, '_agdk_session_state'):
                return {}
            
            session_state = getattr(self, '_agdk_session_state', {})
            
            # Calculate session duration
            started_at = session_state.get('started_at', self._get_timestamp())
            current_time = self._get_timestamp()
            
            stats = {
                'session_id': self._agdk_session_id,
                'agent_name': self.name,
                'started_at': started_at,
                'finished_at': current_time,
                'analysis_count': session_state.get('analysis_count', 0),
                'tools_registered': session_state.get('tools_registered', False),
                'events_processed': getattr(self, '_agdk_events_processed', 0),
                'errors_encountered': getattr(self, '_agdk_errors_count', 0)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error collecting AGDK session stats for {self.name}: {e}")
            return {'error': str(e)}
    
    def _cleanup_agdk_session_resources(self):
        """Clean up AGDK session resources."""
        try:
            # Clear session-specific state
            if hasattr(self, '_agdk_session_state'):
                self._agdk_session_state.clear()
            
            # Reset counters
            self._agdk_events_processed = 0
            self._agdk_errors_count = 0
            
            # Clear tool instances
            if hasattr(self, '_agdk_tool_instances'):
                self._agdk_tool_instances.clear()
            
            logger.debug(f"AGDK session resources cleaned up for {self.name}")
            
        except Exception as e:
            logger.error(f"Error cleaning up AGDK session resources for {self.name}: {e}")
    
    def _force_cleanup_agdk_session(self):
        """Force cleanup of AGDK session (emergency cleanup)."""
        try:
            # Force reset all AGDK-related state
            self._agdk_session = None
            self._agdk_session_id = None
            self._agdk_tools_registered = False
            self._agdk_session_state = {}
            self._agdk_events_processed = 0
            self._agdk_errors_count = 0
            
            if hasattr(self, '_agdk_tool_instances'):
                self._agdk_tool_instances.clear()
            
            logger.warning(f"Force cleanup completed for AGDK session in {self.name}")
            
        except Exception as e:
            logger.error(f"Error during force cleanup for {self.name}: {e}")
    
    # AGDK Event Handlers
    def _validate_agdk_event_data(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Validate AGDK event data structure."""
        try:
            # Basic validation
            if not isinstance(event_data, dict):
                return False
            
            # Event-specific validation
            if event_type == "tool_execution_requested":
                return 'tool_name' in event_data and 'parameters' in event_data
            elif event_type == "analysis_started":
                return 'analysis_id' in event_data
            elif event_type == "analysis_completed":
                return 'analysis_id' in event_data and 'result' in event_data
            elif event_type == "tool_result_available":
                return 'tool_name' in event_data and 'result' in event_data
            elif event_type == "error_occurred":
                return 'error_type' in event_data and 'message' in event_data
            elif event_type == "session_state_changed":
                return 'state' in event_data
            elif event_type == "coordination_request":
                return 'request_type' in event_data
            else:
                # Custom events - minimal validation
                return True
                
        except Exception as e:
            logger.error(f"Error validating event data for {event_type}: {e}")
            return False
    
    def _handle_tool_execution_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution request event."""
        tool_name = event_data.get('tool_name')
        parameters = event_data.get('parameters', {})
        
        logger.debug(f"Tool execution requested: {tool_name} for {self.name}")
        
        # Prepare tool for execution
        result = {
            'tool_name': tool_name,
            'agent': self.name,
            'status': 'acknowledged',
            'timestamp': self._get_timestamp()
        }
        
        # Increment analysis count
        if hasattr(self, '_agdk_session_state'):
            self._agdk_session_state['analysis_count'] = self._agdk_session_state.get('analysis_count', 0) + 1
        
        return result
    
    def _handle_analysis_started_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analysis started event."""
        analysis_id = event_data.get('analysis_id')
        
        logger.debug(f"Analysis started: {analysis_id} for {self.name}")
        
        return {
            'analysis_id': analysis_id,
            'agent': self.name,
            'status': 'analysis_started',
            'timestamp': self._get_timestamp()
        }
    
    def _handle_analysis_completed_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analysis completed event."""
        analysis_id = event_data.get('analysis_id')
        result = event_data.get('result', {})
        
        logger.debug(f"Analysis completed: {analysis_id} for {self.name}")
        
        return {
            'analysis_id': analysis_id,
            'agent': self.name,
            'status': 'analysis_completed',
            'result_summary': {
                'findings_count': len(result.get('findings', [])),
                'success': result.get('success', False)
            },
            'timestamp': self._get_timestamp()
        }
    
    def _handle_tool_result_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool result available event."""
        tool_name = event_data.get('tool_name')
        result = event_data.get('result', {})
        
        logger.debug(f"Tool result available: {tool_name} for {self.name}")
        
        return {
            'tool_name': tool_name,
            'agent': self.name,
            'status': 'result_processed',
            'timestamp': self._get_timestamp()
        }
    
    def _handle_error_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle error event."""
        error_type = event_data.get('error_type')
        message = event_data.get('message', '')
        
        logger.warning(f"AGDK error event: {error_type} - {message} for {self.name}")
        
        # Increment error count
        self._agdk_errors_count = getattr(self, '_agdk_errors_count', 0) + 1
        
        return {
            'error_type': error_type,
            'agent': self.name,
            'status': 'error_acknowledged',
            'error_count': self._agdk_errors_count,
            'timestamp': self._get_timestamp()
        }
    
    def _handle_session_state_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle session state changed event."""
        new_state = event_data.get('state')
        
        logger.debug(f"Session state changed to: {new_state} for {self.name}")
        
        return {
            'previous_state': getattr(self, '_agdk_last_state', 'unknown'),
            'new_state': new_state,
            'agent': self.name,
            'timestamp': self._get_timestamp()
        }
    
    def _handle_coordination_request_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle coordination request event."""
        request_type = event_data.get('request_type')
        
        logger.debug(f"Coordination request: {request_type} for {self.name}")
        
        return {
            'request_type': request_type,
            'agent': self.name,
            'status': 'coordination_acknowledged',
            'timestamp': self._get_timestamp()
        }
    
    def _handle_custom_agdk_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom or unknown AGDK events."""
        logger.debug(f"Custom AGDK event: {event_type} for {self.name}")
        
        return {
            'event_type': event_type,
            'agent': self.name,
            'status': 'custom_event_processed',
            'timestamp': self._get_timestamp()
        }
    
    def _update_agdk_event_stats(self, event_type: str, success: bool):
        """Update AGDK event processing statistics."""
        try:
            if not hasattr(self, '_agdk_events_processed'):
                self._agdk_events_processed = 0
            
            self._agdk_events_processed += 1
            
            if not hasattr(self, '_agdk_event_stats'):
                self._agdk_event_stats = {}
            
            if event_type not in self._agdk_event_stats:
                self._agdk_event_stats[event_type] = {'total': 0, 'success': 0, 'failed': 0}
            
            self._agdk_event_stats[event_type]['total'] += 1
            if success:
                self._agdk_event_stats[event_type]['success'] += 1
            else:
                self._agdk_event_stats[event_type]['failed'] += 1
                
        except Exception as e:
            logger.error(f"Error updating AGDK event stats for {self.name}: {e}")
    
    def _report_agdk_event_error(self, event_type: str, event_data: Dict[str, Any], error: Exception):
        """Report AGDK event processing error."""
        try:
            error_report = {
                'agent': self.name,
                'event_type': event_type,
                'error_message': str(error),
                'error_type': type(error).__name__,
                'event_data_keys': list(event_data.keys()) if event_data else [],
                'timestamp': self._get_timestamp()
            }
            
            logger.error(f"AGDK event error report for {self.name}: {error_report}")
            
            # Could send to monitoring system here
            
        except Exception as report_error:
            logger.error(f"Failed to report AGDK event error for {self.name}: {report_error}")
    
    # AGDK Status and Information Methods
    def get_agdk_session_info(self) -> Dict[str, Any]:
        """Get current AGDK session information."""
        if not self.agdk_enabled:
            return {'agdk_enabled': False}
        
        return {
            'agdk_enabled': True,
            'session_id': self._agdk_session_id,
            'session_active': self._agdk_session is not None,
            'tools_registered': self._agdk_tools_registered,
            'events_processed': getattr(self, '_agdk_events_processed', 0),
            'errors_count': getattr(self, '_agdk_errors_count', 0),
            'event_stats': getattr(self, '_agdk_event_stats', {}),
            'session_state': getattr(self, '_agdk_session_state', {})
        }
    
    # Memory Enhancement Methods
    def _retrieve_memory_context(self, context: AnalysisContext) -> List[Dict[str, Any]]:
        """Retrieve relevant memory context for analysis."""
        if not self.memory_enabled:
            return []
        
        # TODO: Implement memory retrieval using MemoryRetrievalCoordinator
        logger.debug(f"Retrieving memory context for {self.name}")
        
        # Placeholder memory context
        return [
            {
                "type": "similar_pattern",
                "pattern": "high_complexity_function",
                "confidence": 0.85,
                "historical_accuracy": 0.92
            },
            {
                "type": "learned_threshold",
                "metric": "complexity_score",
                "threshold": 7.5,
                "accuracy": 0.88
            }
        ]
    
    def _enhance_context_with_memory(self, context: AnalysisContext, 
                                   memory_context: List[Dict[str, Any]]) -> AnalysisContext:
        """Enhance analysis context with memory insights."""
        enhanced_metadata = context.metadata.copy()
        enhanced_metadata["memory_context"] = memory_context
        enhanced_metadata["learned_patterns"] = self._learned_patterns
        
        return AnalysisContext(
            files=context.files,
            configuration=context.configuration,
            session_id=context.session_id,
            metadata=enhanced_metadata
        )
    
    def _enhance_findings_with_memory(self, findings: List[Finding], 
                                    memory_context: List[Dict[str, Any]]) -> List[Finding]:
        """Enhance findings with memory-based insights."""
        if not self.memory_enabled:
            return findings
        
        enhanced_findings = []
        
        for finding in findings:
            # Apply confidence calibration based on historical accuracy
            calibrated_confidence = self._calibrate_confidence(finding, memory_context)
            
            # Add supporting patterns from memory
            supporting_patterns = self._find_supporting_patterns(finding, memory_context)
            
            # Create enhanced finding
            enhanced_metadata = finding.metadata.copy()
            enhanced_metadata.update({
                "original_confidence": finding.confidence,
                "calibrated_confidence": calibrated_confidence,
                "supporting_patterns": supporting_patterns,
                "memory_enhanced": True
            })
            
            enhanced_finding = Finding(
                id=finding.id,
                title=finding.title,
                description=finding.description,
                severity=finding.severity,
                category=finding.category,
                file_path=finding.file_path,
                line_number=finding.line_number,
                column_number=finding.column_number,
                code_snippet=finding.code_snippet,
                recommendation=self._enhance_recommendation(finding, memory_context),
                confidence=calibrated_confidence,
                metadata=enhanced_metadata
            )
            
            enhanced_findings.append(enhanced_finding)
        
        return enhanced_findings
    
    def _calibrate_confidence(self, finding: Finding, 
                            memory_context: List[Dict[str, Any]]) -> float:
        """Calibrate finding confidence based on historical accuracy."""
        if not self.memory_enabled:
            return finding.confidence
        
        # TODO: Implement confidence calibration using ConfidenceScorer
        
        # Simple calibration based on historical accuracy
        category_accuracy = self._historical_accuracy.get(finding.category, 0.5)
        calibrated = finding.confidence * category_accuracy
        
        return min(max(calibrated, 0.0), 1.0)  # Clamp to [0, 1]
    
    def _find_supporting_patterns(self, finding: Finding, 
                                memory_context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find supporting patterns from memory for a finding."""
        supporting_patterns = []
        
        for context_item in memory_context:
            if context_item.get("type") == "similar_pattern":
                # Check if pattern supports this finding
                if self._pattern_matches_finding(context_item, finding):
                    supporting_patterns.append(context_item)
        
        return supporting_patterns
    
    def _pattern_matches_finding(self, pattern: Dict[str, Any], finding: Finding) -> bool:
        """Check if a memory pattern matches a finding."""
        # TODO: Implement sophisticated pattern matching
        # For now, simple category matching
        return finding.category.lower() in pattern.get("pattern", "").lower()
    
    def _enhance_recommendation(self, finding: Finding, 
                              memory_context: List[Dict[str, Any]]) -> str:
        """Enhance recommendation with memory-based insights."""
        base_recommendation = finding.recommendation
        
        # Find relevant historical solutions
        historical_solutions = [
            ctx for ctx in memory_context 
            if ctx.get("type") == "successful_solution"
        ]
        
        if historical_solutions:
            enhancement = "\n\nBased on historical data: "
            enhancement += "Similar issues were successfully resolved using these approaches."
            return base_recommendation + enhancement
        
        return base_recommendation
    
    def _learn_from_analysis(self, context: AnalysisContext, result: AnalysisResult):
        """Learn from analysis results to improve future analyses."""
        if not self.memory_enabled:
            return
        
        # TODO: Implement learning using PatternRecognitionEngine
        
        # Extract patterns from this analysis
        patterns = self._extract_patterns_from_analysis(context, result)
        self._learned_patterns.extend(patterns)
        
        # Update historical accuracy metrics
        self._update_accuracy_metrics(result)
        
        logger.debug(f"Learned {len(patterns)} new patterns from analysis")
    
    def _extract_patterns_from_analysis(self, context: AnalysisContext, 
                                      result: AnalysisResult) -> List[Dict[str, Any]]:
        """Extract learnable patterns from analysis results."""
        patterns = []
        
        for finding in result.findings:
            pattern = {
                "type": "finding_pattern",
                "category": finding.category,
                "severity": finding.severity.value,
                "confidence": finding.confidence,
                "file_context": {
                    "language": self._detect_file_language(finding.file_path),
                    "size": len(finding.code_snippet or "")
                },
                "timestamp": self._get_timestamp()
            }
            patterns.append(pattern)
        
        return patterns
    
    def _update_accuracy_metrics(self, result: AnalysisResult):
        """Update historical accuracy metrics."""
        # TODO: Implement accuracy tracking based on validation feedback
        for finding in result.findings:
            category = finding.category
            current_accuracy = self._historical_accuracy.get(category, 0.5)
            
            # Simple accuracy update (placeholder)
            # In real implementation, this would be based on user feedback
            updated_accuracy = (current_accuracy + 0.01) if current_accuracy < 0.95 else current_accuracy
            self._historical_accuracy[category] = updated_accuracy
    
    def _detect_file_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file path."""
        try:
            from ...core.config.language_config import language_config
            file_ext = Path(file_path).suffix
            return language_config.detect_language_from_extension(file_ext)
        except ImportError:
            # Fallback to simple extension mapping
            extension_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.java': 'java',
                '.go': 'go',
                '.rs': 'rust',
                '.cpp': 'cpp',
                '.c': 'c',
                '.cs': 'csharp',
                '.swift': 'swift'
            }
            return extension_map.get(Path(file_path).suffix.lower())
    
    # Learning and Memory Access Methods
    def get_learned_patterns(self) -> List[Dict[str, Any]]:
        """Get all learned patterns."""
        return self._learned_patterns.copy()
    
    def get_accuracy_metrics(self) -> Dict[str, float]:
        """Get historical accuracy metrics."""
        return self._historical_accuracy.copy()
    
    def reset_learning_state(self):
        """Reset learning state (for testing/debugging)."""
        self._learned_patterns.clear()
        self._historical_accuracy.clear()
        logger.info(f"Reset learning state for {self.name}")
    
    # Enhanced Feature Status Methods
    def is_memory_enabled(self) -> bool:
        """Check if memory features are enabled."""
        return self.memory_enabled
    
    def is_agdk_enabled(self) -> bool:
        """Check if AGDK features are enabled."""
        return self.agdk_enabled
    
    def get_feature_status(self) -> Dict[str, bool]:
        """Get status of all optional features."""
        return {
            "memory_enabled": self.memory_enabled,
            "agdk_enabled": self.agdk_enabled,
            "learning_active": len(self._learned_patterns) > 0,
            "accuracy_tracking": len(self._historical_accuracy) > 0
        }
    
    # Core Agent Interface Methods (preserved from original)
    def get_capabilities(self) -> List[str]:
        """Get the capabilities of this agent."""
        return self.capabilities.copy()
    
    def get_name(self) -> str:
        """Get the name of this agent."""
        return self.name
    
    def get_version(self) -> str:
        """Get the version of this agent."""
        return self.version
    
    def validate_context(self, context: AnalysisContext) -> bool:
        """Validate that the context is suitable for this agent."""
        if not context.files:
            logger.warning(f"No files provided for analysis in {self.name}")
            return False
            
        return True
    
    def create_finding(
        self,
        title: str,
        description: str,
        severity: FindingSeverity,
        category: str,
        file_path: str,
        recommendation: str,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
        code_snippet: Optional[str] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Finding:
        """Create a new finding."""
        finding_id = f"{self.name}_{len(self._findings) + 1}_{self._get_timestamp()}"
        
        return Finding(
            id=finding_id,
            title=title,
            description=description,
            severity=severity,
            category=category,
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            code_snippet=code_snippet,
            recommendation=recommendation,
            confidence=confidence,
            metadata=metadata or {}
        )
    
    def add_finding(self, finding: Finding):
        """Add a finding to the current analysis."""
        self._findings.append(finding)
        logger.debug(f"Added finding: {finding.title} [{finding.severity.value}]")
    
    def get_findings(self) -> List[Finding]:
        """Get all findings from the current analysis."""
        return self._findings.copy()
    
    def clear_findings(self):
        """Clear all findings."""
        self._findings.clear()
    
    def filter_findings_by_severity(self, severity: FindingSeverity) -> List[Finding]:
        """Filter findings by severity level."""
        return [f for f in self._findings if f.severity == severity]
    
    def get_metrics(self) -> Dict[str, float]:
        """Get enhanced analysis metrics with memory insights."""
        total_findings = len(self._findings)
        
        base_metrics = {
            "total_findings": float(total_findings),
            "critical_findings": float(len(self.filter_findings_by_severity(FindingSeverity.CRITICAL))),
            "warning_findings": float(len(self.filter_findings_by_severity(FindingSeverity.WARNING))),
            "info_findings": float(len(self.filter_findings_by_severity(FindingSeverity.INFO))),
            "average_confidence": self._calculate_average_confidence(),
            "analysis_coverage": self._calculate_coverage()
        }
        
        # Add memory-enhanced metrics if enabled
        if self.memory_enabled:
            base_metrics.update({
                "learned_patterns_count": float(len(self._learned_patterns)),
                "average_historical_accuracy": self._get_average_accuracy(),
                "memory_enhanced_findings": float(sum(1 for f in self._findings 
                                                   if f.metadata.get("memory_enhanced", False)))
            })
        
        return base_metrics
    
    def _get_average_accuracy(self) -> float:
        """Get average historical accuracy across all categories."""
        if not self._historical_accuracy:
            return 0.0
        return sum(self._historical_accuracy.values()) / len(self._historical_accuracy)
    
    def _calculate_average_confidence(self) -> float:
        """Calculate average confidence across all findings."""
        if not self._findings:
            return 0.0
        return sum(f.confidence for f in self._findings) / len(self._findings)
    
    def _calculate_coverage(self) -> float:
        """Calculate analysis coverage percentage."""
        # TODO: Implement actual coverage calculation
        return 100.0  # Placeholder
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def __str__(self) -> str:
        """Enhanced string representation of the agent."""
        feature_status = []
        if self.memory_enabled:
            feature_status.append("Memory")
        if self.agdk_enabled:
            feature_status.append("AGDK")
        
        features = f" [{', '.join(feature_status)}]" if feature_status else ""
        return f"{self.name} v{self.version} ({len(self.capabilities)} capabilities){features}"
    
    def __repr__(self) -> str:
        """Detailed representation of the agent."""
        return (f"BaseAgent(name='{self.name}', version='{self.version}', "
                f"capabilities={self.capabilities}, memory_enabled={self.memory_enabled}, "
                f"agdk_enabled={self.agdk_enabled})")