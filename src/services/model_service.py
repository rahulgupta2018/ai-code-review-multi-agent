"""
Model Service Implementation

This module provides model management and routing for the ADK multi-agent system.
It handles LLM provider selection, model routing, request optimization, and
cost management with comprehensive monitoring and error handling.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
import json
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
    from google.adk.core import ModelService as ADKModelService
    HAS_ADK = True
except ImportError:
    # Mock ModelService for development/testing
    class ADKModelService:
        def __init__(self):
            pass
            
        async def get_model(self, model_id: str):
            return None
            
        async def list_models(self):
            return []
    HAS_ADK = False

from utils.config_loader import get_config, get_llm_config
from utils.exceptions import (
    ADKCodeReviewError, AgentError, AgentConfigurationError, AgentExecutionError
)
from utils.common import generate_correlation_id
from utils.constants import (
    DEFAULT_AGENT_TIMEOUT, MAX_TOOL_EXECUTION_TIME, MAX_RETRY_ATTEMPTS
)
from utils.types import AgentType


# Constants for model service
DEFAULT_MODEL_TIMEOUT = 30.0


class ModelSelectionStrategy(Enum):
    """Model selection strategies."""
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    BALANCED = "balanced"
    ROUND_ROBIN = "round_robin"


class ADKModelService:
    """
    ADK-compatible model service with enhanced functionality.
    
    Features:
    - Configuration-driven model selection (no hardcoding)
    - Multi-provider support (Gemini, OpenAI, Ollama)
    - Cost optimization and budget management
    - Request routing and load balancing
    - Performance monitoring and metrics
    - Error handling and fallback models
    - Rate limiting and quota management
    """
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """
        Initialize the ADK model service.
        
        Args:
            config_override: Optional configuration overrides
        """
        # Initialize ADK base functionality if available
        self._adk_model_service = None
        if HAS_ADK:
            try:
                from google.adk.core import ModelService as ADKModelServiceCore
                self._adk_model_service = ADKModelServiceCore()
            except Exception:
                pass
        
        # Load configuration
        self._load_configuration(config_override)
        
        # Set up logging
        self.logger = get_structured_logger(self.__class__.__name__)
        
        # Initialize provider clients (will be loaded on-demand)
        self._provider_clients: Dict[str, Any] = {}
        self._provider_status: Dict[str, Dict[str, Any]] = {}
        
        # Model routing and selection
        self._available_models: Dict[str, Dict[str, Any]] = {}
        self._model_performance: Dict[str, Dict[str, float]] = {}
        self._request_counts: Dict[str, int] = {}
        
        # Cost tracking
        self._cost_tracking: Dict[str, Dict[str, float]] = {}
        self._budget_limits: Dict[str, float] = {}
        
        # Rate limiting
        self._rate_limits: Dict[str, Dict[str, Any]] = {}
        self._request_history: Dict[str, List[float]] = {}
        
        # Initialize providers
        asyncio.create_task(self._initialize_providers())
        
        self.logger.info(
            "ADK Model Service initialized - Providers: %s, Strategy: %s",
            list(self._config.get('providers', {}).keys()),
            self._config.get('model_selection', {}).get('strategy', 'balanced')
        )
    
    def _load_configuration(self, config_override: Optional[Dict[str, Any]] = None) -> None:
        """Load configuration from YAML files."""
        try:
            # Get comprehensive LLM configuration
            llm_config = get_llm_config()
            
            if not llm_config:
                raise AgentConfigurationError("LLM configuration not found")
            
            # Merge with overrides
            self._config = {
                **llm_config,
                **(config_override or {})
            }
            
            # Validate configuration
            self._validate_configuration()
            
        except Exception as e:
            raise AgentConfigurationError(f"Failed to load model configuration: {e}") from e
    
    def _validate_configuration(self) -> None:
        """Validate the model service configuration."""
        # Check providers configuration
        providers = self._config.get('providers', {})
        if not providers:
            raise AgentConfigurationError("No LLM providers configured")
        
        # Validate each provider
        for provider_name, provider_config in providers.items():
            if not isinstance(provider_config, dict):
                raise AgentConfigurationError(f"Invalid provider configuration for {provider_name}")
            
            if 'models' not in provider_config:
                raise AgentConfigurationError(f"No models configured for provider {provider_name}")
        
        # Validate model selection strategy
        selection_config = self._config.get('model_selection', {})
        strategy = selection_config.get('strategy', 'balanced')
        if strategy not in [s.value for s in ModelSelectionStrategy]:
            raise AgentConfigurationError(f"Invalid model selection strategy: {strategy}")
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the model service configuration."""
        return self._config.copy()
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Get model service metrics."""
        return {
            'available_models': len(self._available_models),
            'provider_count': len(self._provider_clients),
            'total_requests': sum(self._request_counts.values()),
            'cost_tracking': self._cost_tracking.copy(),
            'provider_status': self._provider_status.copy(),
            'model_performance': self._model_performance.copy()
        }
    
    async def _initialize_providers(self) -> None:
        """Initialize LLM provider clients."""
        try:
            providers = self._config.get('providers', {})
            
            for provider_name, provider_config in providers.items():
                try:
                    await self._initialize_provider(provider_name, provider_config)
                    self.logger.info(
                        "Provider initialized successfully - Name: %s",
                        provider_name
                    )
                    
                except Exception as e:
                    self.logger.error(
                        "Failed to initialize provider - Name: %s, Error: %s",
                        provider_name,
                        str(e)
                    )
                    
                    # Mark provider as unavailable
                    self._provider_status[provider_name] = {
                        'status': 'unavailable',
                        'error': str(e),
                        'last_check': time.time()
                    }
            
            # Load available models
            await self._discover_available_models()
            
        except Exception as e:
            self.logger.error(
                "Provider initialization failed - Error: %s",
                str(e)
            )
    
    async def _initialize_provider(self, provider_name: str, provider_config: Dict[str, Any]) -> None:
        """Initialize a specific LLM provider."""
        try:
            # For now, we'll create a mock client since actual LLM integration is in Phase 2
            # This establishes the interface for real implementation
            
            provider_client = {
                'name': provider_name,
                'config': provider_config,
                'models': provider_config.get('models', {}),
                'rate_limits': provider_config.get('rate_limits', {}),
                'initialized_at': time.time()
            }
            
            self._provider_clients[provider_name] = provider_client
            
            # Initialize provider status
            self._provider_status[provider_name] = {
                'status': 'available',
                'models_count': len(provider_config.get('models', {})),
                'last_check': time.time(),
                'error': None
            }
            
            # Initialize rate limiting for provider
            rate_limits = provider_config.get('rate_limits', {})
            self._rate_limits[provider_name] = {
                'requests_per_minute': rate_limits.get('requests_per_minute', 60),
                'tokens_per_minute': rate_limits.get('tokens_per_minute', 10000),
                'current_requests': 0,
                'current_tokens': 0,
                'reset_time': time.time() + 60
            }
            
            # Initialize cost tracking
            cost_config = provider_config.get('cost', {})
            if cost_config:
                self._cost_tracking[provider_name] = {
                    'total_cost': 0.0,
                    'request_count': 0,
                    'token_usage': 0
                }
                
                budget_limit = cost_config.get('daily_budget', 100.0)
                self._budget_limits[provider_name] = budget_limit
            
        except Exception as e:
            self.logger.error(
                "Provider initialization failed - Provider: %s, Error: %s",
                provider_name,
                str(e)
            )
            raise
    
    async def _discover_available_models(self) -> None:
        """Discover available models from all providers."""
        try:
            self._available_models.clear()
            
            for provider_name, provider_client in self._provider_clients.items():
                try:
                    models = provider_client.get('models', {})
                    
                    for model_name, model_config in models.items():
                        model_id = f"{provider_name}:{model_name}"
                        
                        self._available_models[model_id] = {
                            'provider': provider_name,
                            'model_name': model_name,
                            'config': model_config,
                            'capabilities': model_config.get('capabilities', []),
                            'cost_per_token': model_config.get('cost_per_token', 0.0),
                            'max_tokens': model_config.get('max_tokens', 4096),
                            'context_window': model_config.get('context_window', 4096)
                        }
                        
                        # Initialize performance tracking
                        self._model_performance[model_id] = {
                            'avg_response_time': 0.0,
                            'success_rate': 1.0,
                            'error_count': 0,
                            'total_requests': 0
                        }
                        
                        self._request_counts[model_id] = 0
                
                except Exception as e:
                    self.logger.warning(
                        "Failed to discover models for provider - Provider: %s, Error: %s",
                        provider_name,
                        str(e)
                    )
            
            self.logger.info(
                "Model discovery completed - Available models: %d",
                len(self._available_models)
            )
            
        except Exception as e:
            self.logger.error(
                "Model discovery failed - Error: %s",
                str(e)
            )
    
    async def select_model(
        self,
        task_type: str,
        requirements: Optional[Dict[str, Any]] = None,
        strategy: Optional[str] = None
    ) -> Optional[str]:
        """
        Select the best model for a given task.
        
        Args:
            task_type: Type of task (code_analysis, security_scan, etc.)
            requirements: Task-specific requirements (max_tokens, etc.)
            strategy: Model selection strategy override
            
        Returns:
            Selected model ID or None if no suitable model found
        """
        try:
            if not self._available_models:
                await self._discover_available_models()
            
            if not self._available_models:
                self.logger.error("No available models for selection")
                return None
            
            # Get selection strategy
            selection_strategy = strategy or self._config.get('model_selection', {}).get('strategy', 'balanced')
            
            # Filter models based on requirements
            suitable_models = await self._filter_suitable_models(task_type, requirements)
            
            if not suitable_models:
                self.logger.warning(
                    "No suitable models found - Task: %s, Requirements: %s",
                    task_type,
                    requirements
                )
                return None
            
            # Apply selection strategy
            selected_model = await self._apply_selection_strategy(
                suitable_models,
                selection_strategy
            )
            
            self.logger.info(
                "Model selected - Model: %s, Task: %s, Strategy: %s",
                selected_model,
                task_type,
                selection_strategy
            )
            
            return selected_model
            
        except Exception as e:
            self.logger.error(
                "Model selection failed - Task: %s, Error: %s",
                task_type,
                str(e)
            )
            return None
    
    async def _filter_suitable_models(
        self,
        task_type: str,
        requirements: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Filter models based on task requirements."""
        suitable_models = []
        requirements = requirements or {}
        
        try:
            for model_id, model_info in self._available_models.items():
                # Check provider availability
                provider = model_info['provider']
                if self._provider_status.get(provider, {}).get('status') != 'available':
                    continue
                
                # Check capabilities
                required_capabilities = requirements.get('capabilities', [])
                model_capabilities = model_info.get('capabilities', [])
                
                if required_capabilities:
                    if not all(cap in model_capabilities for cap in required_capabilities):
                        continue
                
                # Check token limits
                required_tokens = requirements.get('max_tokens', 0)
                model_max_tokens = model_info.get('max_tokens', 4096)
                
                if required_tokens > model_max_tokens:
                    continue
                
                # Check rate limits
                if not await self._check_rate_limits(provider):
                    continue
                
                # Check budget limits
                if not await self._check_budget_limits(provider):
                    continue
                
                suitable_models.append(model_id)
            
            return suitable_models
            
        except Exception as e:
            self.logger.error(
                "Model filtering failed - Error: %s",
                str(e)
            )
            return []
    
    async def _apply_selection_strategy(
        self,
        suitable_models: List[str],
        strategy: str
    ) -> Optional[str]:
        """Apply model selection strategy."""
        try:
            if not suitable_models:
                return None
            
            if strategy == ModelSelectionStrategy.COST_OPTIMIZED.value:
                # Select model with lowest cost per token
                return min(
                    suitable_models,
                    key=lambda m: self._available_models[m].get('cost_per_token', 0.0)
                )
            
            elif strategy == ModelSelectionStrategy.PERFORMANCE_OPTIMIZED.value:
                # Select model with best performance metrics
                return min(
                    suitable_models,
                    key=lambda m: self._model_performance[m].get('avg_response_time', float('inf'))
                )
            
            elif strategy == ModelSelectionStrategy.BALANCED.value:
                # Balance cost and performance
                def score_model(model_id: str) -> float:
                    model_info = self._available_models[model_id]
                    perf_info = self._model_performance[model_id]
                    
                    cost_score = model_info.get('cost_per_token', 0.0)
                    perf_score = perf_info.get('avg_response_time', 1.0)
                    
                    # Lower is better for both cost and response time
                    return cost_score + (perf_score / 1000)  # Normalize response time
                
                return min(suitable_models, key=score_model)
            
            elif strategy == ModelSelectionStrategy.ROUND_ROBIN.value:
                # Simple round-robin selection
                total_requests = sum(self._request_counts[m] for m in suitable_models)
                return min(suitable_models, key=lambda m: self._request_counts[m])
            
            else:
                # Default to first suitable model
                return suitable_models[0]
                
        except Exception as e:
            self.logger.error(
                "Strategy application failed - Strategy: %s, Error: %s",
                strategy,
                str(e)
            )
            return suitable_models[0] if suitable_models else None
    
    async def _check_rate_limits(self, provider: str) -> bool:
        """Check if provider rate limits allow new requests."""
        try:
            rate_limit_info = self._rate_limits.get(provider, {})
            current_time = time.time()
            
            # Reset counters if time window has passed
            if current_time > rate_limit_info.get('reset_time', 0):
                rate_limit_info['current_requests'] = 0
                rate_limit_info['current_tokens'] = 0
                rate_limit_info['reset_time'] = current_time + 60
            
            # Check request limit
            max_requests = rate_limit_info.get('requests_per_minute', 60)
            current_requests = rate_limit_info.get('current_requests', 0)
            
            return current_requests < max_requests
            
        except Exception as e:
            self.logger.warning(
                "Rate limit check failed - Provider: %s, Error: %s",
                provider,
                str(e)
            )
            return True  # Allow request if check fails
    
    async def _check_budget_limits(self, provider: str) -> bool:
        """Check if provider budget limits allow new requests."""
        try:
            budget_limit = self._budget_limits.get(provider, float('inf'))
            current_cost = self._cost_tracking.get(provider, {}).get('total_cost', 0.0)
            
            return current_cost < budget_limit
            
        except Exception as e:
            self.logger.warning(
                "Budget check failed - Provider: %s, Error: %s",
                provider,
                str(e)
            )
            return True  # Allow request if check fails
    
    async def execute_model_request(
        self,
        model_id: str,
        request: Dict[str, Any],
        timeout: Optional[float] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Execute a model request with error handling and retries.
        
        Args:
            model_id: The model ID to use
            request: The request payload
            timeout: Request timeout in seconds
            retry_count: Current retry count
            
        Returns:
            Model response
        """
        start_time = time.time()
        correlation_id = request.get('correlation_id', generate_correlation_id())
        
        self.logger.info(
            "Executing model request - Model: %s, Correlation: %s",
            model_id,
            correlation_id
        )
        
        try:
            # Validate model availability
            if model_id not in self._available_models:
                raise AgentExecutionError(f"Model not available: {model_id}")
            
            model_info = self._available_models[model_id]
            provider = model_info['provider']
            
            # Check provider status
            provider_status = self._provider_status.get(provider, {})
            if provider_status.get('status') != 'available':
                raise AgentExecutionError(f"Provider unavailable: {provider}")
            
            # Update rate limiting
            await self._update_rate_limits(provider)
            
            # Execute request (mock implementation for now)
            response = await self._execute_provider_request(
                provider,
                model_info,
                request,
                timeout or DEFAULT_MODEL_TIMEOUT
            )
            
            # Update metrics
            execution_time = time.time() - start_time
            await self._update_model_metrics(model_id, execution_time, success=True)
            
            # Update cost tracking
            await self._update_cost_tracking(provider, request, response)
            
            self.logger.info(
                "Model request completed - Model: %s, Time: %.2fs",
                model_id,
                execution_time
            )
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            await self._update_model_metrics(model_id, execution_time, success=False)
            
            self.logger.error(
                "Model request failed - Model: %s, Time: %.2fs, Error: %s",
                model_id,
                execution_time,
                str(e)
            )
            
            # Retry logic
            max_retries = self._config.get('error_handling', {}).get('max_retries', MAX_RETRY_ATTEMPTS)
            if retry_count < max_retries:
                self.logger.info(
                    "Retrying model request - Model: %s, Retry: %d/%d",
                    model_id,
                    retry_count + 1,
                    max_retries
                )
                
                # Exponential backoff
                await asyncio.sleep(2 ** retry_count)
                
                return await self.execute_model_request(
                    model_id,
                    request,
                    timeout,
                    retry_count + 1
                )
            
            raise AgentExecutionError(f"Model request failed after {max_retries} retries: {e}") from e
    
    async def _execute_provider_request(
        self,
        provider: str,
        model_info: Dict[str, Any],
        request: Dict[str, Any],
        timeout: float
    ) -> Dict[str, Any]:
        """Execute request with specific provider (mock implementation)."""
        # This is a mock implementation - real LLM integration will be in Phase 2
        
        # Simulate request processing time
        await asyncio.sleep(0.1)
        
        # Mock response based on provider
        if provider == 'gemini':
            return {
                'provider': provider,
                'model': model_info['model_name'],
                'response': 'Mock Gemini response for code analysis',
                'tokens_used': 150,
                'cost': 0.003,
                'timestamp': datetime.now().isoformat()
            }
        elif provider == 'openai':
            return {
                'provider': provider,
                'model': model_info['model_name'],
                'response': 'Mock OpenAI response for code analysis',
                'tokens_used': 120,
                'cost': 0.004,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'provider': provider,
                'model': model_info['model_name'],
                'response': f'Mock response from {provider} for code analysis',
                'tokens_used': 100,
                'cost': 0.001,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _update_rate_limits(self, provider: str) -> None:
        """Update rate limiting counters."""
        rate_limit_info = self._rate_limits.get(provider, {})
        rate_limit_info['current_requests'] = rate_limit_info.get('current_requests', 0) + 1
    
    async def _update_model_metrics(self, model_id: str, execution_time: float, success: bool) -> None:
        """Update model performance metrics."""
        metrics = self._model_performance.get(model_id, {})
        
        total_requests = metrics.get('total_requests', 0) + 1
        
        if success:
            # Update average response time
            current_avg = metrics.get('avg_response_time', 0.0)
            new_avg = ((current_avg * (total_requests - 1)) + execution_time) / total_requests
            metrics['avg_response_time'] = new_avg
            
            # Update success rate
            current_success_rate = metrics.get('success_rate', 1.0)
            new_success_rate = ((current_success_rate * (total_requests - 1)) + 1.0) / total_requests
            metrics['success_rate'] = new_success_rate
        else:
            metrics['error_count'] = metrics.get('error_count', 0) + 1
            
            # Update success rate
            current_success_rate = metrics.get('success_rate', 1.0)
            new_success_rate = ((current_success_rate * (total_requests - 1)) + 0.0) / total_requests
            metrics['success_rate'] = new_success_rate
        
        metrics['total_requests'] = total_requests
        self._model_performance[model_id] = metrics
        
        # Update request count
        self._request_counts[model_id] = self._request_counts.get(model_id, 0) + 1
    
    async def _update_cost_tracking(
        self,
        provider: str,
        request: Dict[str, Any],
        response: Dict[str, Any]
    ) -> None:
        """Update cost tracking information."""
        try:
            cost_info = self._cost_tracking.get(provider, {})
            
            request_cost = response.get('cost', 0.0)
            tokens_used = response.get('tokens_used', 0)
            
            cost_info['total_cost'] = cost_info.get('total_cost', 0.0) + request_cost
            cost_info['request_count'] = cost_info.get('request_count', 0) + 1
            cost_info['token_usage'] = cost_info.get('token_usage', 0) + tokens_used
            
            self._cost_tracking[provider] = cost_info
            
        except Exception as e:
            self.logger.warning(
                "Cost tracking update failed - Provider: %s, Error: %s",
                provider,
                str(e)
            )
    
    async def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        return self._available_models.get(model_id)
    
    async def list_available_models(
        self,
        task_type: Optional[str] = None,
        provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List available models with optional filtering."""
        try:
            models = []
            
            for model_id, model_info in self._available_models.items():
                # Filter by provider if specified
                if provider and model_info['provider'] != provider:
                    continue
                
                # Filter by task type if specified (check capabilities)
                if task_type:
                    capabilities = model_info.get('capabilities', [])
                    if task_type not in capabilities:
                        continue
                
                # Add performance metrics
                model_data = {
                    'model_id': model_id,
                    **model_info,
                    'performance': self._model_performance.get(model_id, {}),
                    'request_count': self._request_counts.get(model_id, 0)
                }
                
                models.append(model_data)
            
            return models
            
        except Exception as e:
            self.logger.error(
                "Failed to list models - Error: %s",
                str(e)
            )
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on model service."""
        try:
            # Check provider health
            healthy_providers = 0
            total_providers = len(self._provider_status)
            
            for provider, status in self._provider_status.items():
                if status.get('status') == 'available':
                    healthy_providers += 1
            
            # Check model availability
            available_models = len(self._available_models)
            
            # Check budget status
            budget_healthy = True
            for provider, limit in self._budget_limits.items():
                current_cost = self._cost_tracking.get(provider, {}).get('total_cost', 0.0)
                if current_cost > (limit * 0.9):  # 90% threshold
                    budget_healthy = False
                    break
            
            status = 'healthy'
            if healthy_providers == 0 or available_models == 0 or not budget_healthy:
                status = 'unhealthy'
            elif healthy_providers < total_providers:
                status = 'degraded'
            
            health_data = {
                'status': status,
                'healthy_providers': healthy_providers,
                'total_providers': total_providers,
                'available_models': available_models,
                'budget_healthy': budget_healthy,
                'provider_status': self._provider_status.copy(),
                'cost_tracking': self._cost_tracking.copy(),
                'last_check': datetime.now()
            }
            
            self.logger.info(
                "Model service health check - Status: %s, Providers: %d/%d, Models: %d",
                status,
                healthy_providers,
                total_providers,
                available_models
            )
            
            return health_data
            
        except Exception as e:
            self.logger.error(
                "Model service health check failed - Error: %s",
                str(e)
            )
            
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now()
            }
    
    async def shutdown(self) -> None:
        """Shutdown the model service."""
        try:
            # Close provider connections
            for provider_name, provider_client in self._provider_clients.items():
                try:
                    # In real implementation, close actual connections
                    self.logger.info(
                        "Shutting down provider - Name: %s",
                        provider_name
                    )
                except Exception as e:
                    self.logger.warning(
                        "Provider shutdown failed - Name: %s, Error: %s",
                        provider_name,
                        str(e)
                    )
            
            # Clear all data
            self._provider_clients.clear()
            self._available_models.clear()
            self._provider_status.clear()
            self._model_performance.clear()
            self._request_counts.clear()
            self._cost_tracking.clear()
            self._rate_limits.clear()
            self._request_history.clear()
            
            self.logger.info("Model service shutdown completed")
            
        except Exception as e:
            self.logger.error(
                "Model service shutdown failed - Error: %s",
                str(e)
            )