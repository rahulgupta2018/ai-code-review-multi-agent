"""
Consolidated Model Service - Phase 1 Implementation
All-in-one service for LLM configuration, routing, and model management
"""
import os
import yaml
import aiohttp
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from google.adk.models.lite_llm import LiteLlm


class ModelService:
    """Consolidated model service handling configuration, routing, and model management"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_cache: Dict[str, Any] = {}
        self.config_dir = Path(config_dir)
        self.model_instances = {}
        
        # Set Ollama base URL immediately on initialization for container environments
        os.environ["OLLAMA_API_BASE"] = "http://host.docker.internal:11434"
        print(f"🔧 ModelService initialized with OLLAMA_API_BASE: {os.environ['OLLAMA_API_BASE']}")
    
    # ============ Configuration Management ============
    
    async def load_config(self) -> Dict[str, Any]:
        """Load configuration from config/llm/models.yaml"""
        if self.config_cache:
            return self.config_cache
            
        config_path = self.config_dir / "llm" / "models.yaml"
        
        try:
            with open(config_path, 'r') as file:
                config_data = yaml.safe_load(file)
                self.config_cache = config_data
                return config_data
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file {config_path} not found")
        except Exception as e:
            raise RuntimeError(f"Error loading config: {e}")
    
    async def get_development_model(self) -> Tuple[str, str]:
        """Get development model and provider from configuration"""
        config = await self.load_config()
        dev_config = config.get("development", {})
        
        provider = dev_config.get("preferred_provider", "ollama")
        model = dev_config.get("preferred_model", "llama3_1_8b")
        
        return provider, model
    
    async def get_model_config(self, provider: str, model_key: str) -> Dict[str, Any]:
        """Get specific model configuration"""
        config = await self.load_config()
        providers = config.get("providers", {})
        
        if provider in providers:
            models = providers[provider].get("models", {})
            return models.get(model_key, {})
        
        return {}
    
    async def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider"""
        config = await self.load_config()
        providers = config.get("providers", {})
        return providers.get(provider, {})
    
    async def get_routing_rules(self) -> list:
        """Get model routing rules from configuration"""
        config = await self.load_config()
        model_selection = config.get("model_selection", {})
        return model_selection.get("routing_rules", [])
    
    # ============ Provider Setup and Health Checking ============
    
    async def configure_provider_for_litellm(self, provider: str):
        """Configure LiteLLM for any provider based on configuration"""
        provider_config = await self.get_provider_config(provider)
        endpoints = provider_config.get("endpoints", {})
        
        # Set environment variables based on provider configuration
        if provider == "ollama" and "base_url" in endpoints:
            os.environ["OLLAMA_API_BASE"] = endpoints["base_url"]
        elif provider == "openai" and "base_url" in endpoints:
            os.environ["OPENAI_API_BASE"] = endpoints["base_url"]
            
    async def health_check_provider(self, provider: str) -> bool:
        """Generic health check for any provider"""
        provider_config = await self.get_provider_config(provider)
        endpoints = provider_config.get("endpoints", {})
        base_url = endpoints.get("base_url")
        
        if not base_url:
            return True  # Some providers don't need health checks
            
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Generic health check endpoint
                if provider == "ollama":
                    health_endpoint = f"{base_url}/api/tags"
                else:
                    health_endpoint = f"{base_url}/health"
                    
                async with session.get(health_endpoint) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ {provider} not accessible: {e}")
            return False
    
    async def health_check_all_providers(self) -> Dict[str, bool]:
        """Check health of all configured providers"""
        config = await self.load_config()
        providers = config.get("providers", {})
        
        health_status = {}
        for provider_name in providers.keys():
            health_status[provider_name] = await self.health_check_provider(provider_name)
            
        return health_status
    
    # ============ Model Creation and Management ============
    
    def create_litellm_model(self, provider: str, model_name: str):
        """Create LiteLLM instance for any provider/model combination"""
        if provider == "ollama":
            return LiteLlm(model=f"ollama/{model_name}")
        elif provider == "openai":
            return LiteLlm(model=f"openai/{model_name}")
        elif provider == "anthropic":
            return LiteLlm(model=f"anthropic/{model_name}")
        elif provider == "google_gemini":
            # Direct ADK support for Gemini
            return model_name
        else:
            # Generic LiteLLM wrapper
            return LiteLlm(model=model_name)
    
    async def get_model_for_agent(self, agent_name: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """Get model instance based on configuration and context"""
        context = context or {}
        
        # Simplified approach for development - use direct Ollama model
        # For production, this could be enhanced with the full routing logic
        return self.create_simple_ollama_model()
    
    def create_simple_ollama_model(self):
        """Create a simple Ollama model instance for development"""
        # Set the environment variable for LiteLLM to use the correct Ollama base URL
        os.environ["OLLAMA_API_BASE"] = "http://host.docker.internal:11434"
        
        # Direct model creation without complex routing
        # This ensures reliability and simplicity for local development
        return LiteLlm(model="ollama/llama3.1:8b")
        
    async def _determine_model(self, context: Dict[str, Any]) -> Tuple[str, str]:
        """Determine provider and model based on routing rules"""
        routing_rules = await self.get_routing_rules()
        
        # Check routing rules in order
        for rule in routing_rules:
            condition = rule.get("condition", "")
            if self._evaluate_condition(condition, context):
                return rule.get("provider"), rule.get("model")
        
        # Fallback to development configuration
        dev_provider, dev_model = await self.get_development_model()
        return dev_provider, dev_model
        
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate routing condition against context"""
        # Simple condition evaluation - can be enhanced
        environment = context.get("environment", "development")
        analysis_type = context.get("analysis_type", "general")
        
        condition = condition.lower()
        
        if "environment == 'development'" in condition:
            return environment == "development"
        elif "environment == 'production'" in condition:
            return environment == "production"
        elif "analysis_type == 'security'" in condition:
            return analysis_type == "security"
        elif "analysis_type == 'code_quality'" in condition:
            return analysis_type == "code_quality"
        elif "analysis_type == 'engineering_practices'" in condition:
            return analysis_type == "engineering_practices"
        
        return False
    
    # ============ Utility Methods ============
    
    async def get_available_models(self) -> Dict[str, list]:
        """Get list of available models from configuration"""
        config = await self.load_config()
        providers = config.get("providers", {})
        
        available_models = {}
        for provider_name, provider_config in providers.items():
            models = provider_config.get("models", {})
            available_models[provider_name] = list(models.keys())
            
        return available_models
    
    async def get_available_models_for_provider(self, provider: str) -> list:
        """Get available models for a specific provider from configuration"""
        provider_config = await self.get_provider_config(provider)
        models = provider_config.get("models", {})
        return list(models.keys())