"""
Configuration management for AI Code Review Multi-Agent System.

This module handles loading and managing configuration from various YAML files
in the project's config directory. It provides centralized access to all
configuration settings while maintaining separation of concerns.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configuration-specific exceptions
class ConfigurationError(Exception):
    """Configuration-related errors."""
    pass


# Configuration types for this module
ConfigDict = Dict[str, Any]


# Configuration constants
CONFIG_KEYS = {
    'APPLICATION': 'application',
    'API': 'api',
    'OBSERVABILITY': 'observability',
    'LLM': 'llm',
    'AGENTS': 'agents',
    'ENVIRONMENTS': 'environments',
    'TREE_SITTER': 'tree_sitter',
    'RULES': 'rules',
    'INTEGRATIONS': 'integrations',
    'REPORTING': 'reporting'
}

DEFAULT_VALUES = {
    'environment': 'development',
    'debug': False,
    'log_level': 'INFO'
}

# Set up logging
logger = logging.getLogger(__name__)

# Global configuration cache
_CONFIG_CACHE: Optional[Dict[str, Any]] = None


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    current_file = Path(__file__)
    repo_root = current_file.parent.parent.parent  # Go up to repo root
    return repo_root / "config"


def load_config() -> Dict[str, Any]:
    """
    Load configuration from specialized config directories.
    Each domain has its own authoritative configuration directory.
    """
    global _CONFIG_CACHE
    
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    
    try:
        config_dir = get_config_dir()
        
        # Load configurations from specialized directories
        config = {}
        
        # Load API/Application configuration
        api_config_dir = config_dir / "api"
        if api_config_dir.exists():
            for config_file in api_config_dir.glob("*.yaml"):
                with open(config_file, 'r', encoding='utf-8') as file:
                    file_config = yaml.safe_load(file) or {}
                    config = _deep_merge(config, file_config)
        
        # Load observability configuration
        obs_config_dir = config_dir / "observability"
        if obs_config_dir.exists():
            for config_file in obs_config_dir.glob("*.yaml"):
                with open(config_file, 'r', encoding='utf-8') as file:
                    file_config = yaml.safe_load(file) or {}
                    config = _deep_merge(config, file_config)
        
        # Environment detection and override
        environment = os.getenv("ENVIRONMENT", "development")
        config["environment"] = environment
        
        # Apply environment-specific overrides (direct load to avoid circular dependency)
        env_config_dir = config_dir / "environments"
        env_path = env_config_dir / f"{environment}.yaml"
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as file:
                env_config = yaml.safe_load(file) or {}
                config = _deep_merge(config, env_config)
        
        _CONFIG_CACHE = config
        
        logger.info(f"Configuration loaded for environment: {environment}, sources: api, observability, environments")
        
        return config
        
    except Exception as e:
        logger.error(f"Config load error: {e}")
        # Return minimal fallback config
        return {
            "environment": "development",
            "application": {"name": "AI Code Review Multi-Agent"},
            "api": {"timeouts": {"api": 30, "agent": 300}},
            "logging": {"level": "INFO"}
        }


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_config() -> Dict[str, Any]:
    """Get the complete configuration."""
    return load_config()


def get_app_config() -> Dict[str, Any]:
    """Get application configuration."""
    return get_config().get('application', {})


def get_llm_config() -> Dict[str, Any]:
    """
    Get comprehensive LLM configuration by merging specialized LLM config files.
    
    Returns:
        Dict containing complete LLM configuration from config/llm/ directory
    """
    try:
        config_dir = Path(__file__).parent.parent.parent / "config" / "llm"
        
        # Load all LLM configuration files
        llm_config = {}
        
        # Load models configuration (authoritative for models and providers)
        models_path = config_dir / "models.yaml"
        if models_path.exists():
            with open(models_path, 'r', encoding='utf-8') as file:
                models_config = yaml.safe_load(file) or {}
                llm_config.update(models_config)
        
        # Load cost optimization configuration
        cost_path = config_dir / "cost_optimization.yaml"
        if cost_path.exists():
            with open(cost_path, 'r', encoding='utf-8') as file:
                cost_config = yaml.safe_load(file) or {}
                llm_config["cost_optimization"] = cost_config
        
        # Load output validation configuration
        validation_path = config_dir / "output_validation.yaml"
        if validation_path.exists():
            with open(validation_path, 'r', encoding='utf-8') as file:
                validation_config = yaml.safe_load(file) or {}
                llm_config["output_validation"] = validation_config
        
        # Load system protection configuration
        protection_path = config_dir / "system_protection.yaml"
        if protection_path.exists():
            with open(protection_path, 'r', encoding='utf-8') as file:
                protection_config = yaml.safe_load(file) or {}
                llm_config["system_protection"] = protection_config
        
        # Merge with basic LLM config from unified config.yaml
        unified_config = get_config()
        basic_llm = unified_config.get("llm", {})
        
        # Use specialized configs as primary, unified config as fallback
        final_config = {**basic_llm, **llm_config}
        
        providers = list(final_config.get("providers", {}).keys())
        models_count = len(final_config.get("providers", {}).get("ollama", {}).get("models", {}))
        logger.info(f"LLM configuration loaded - providers: {providers}, models: {models_count}, features: {list(final_config.keys())}")
        
        return final_config
        
    except Exception as e:
        logger.error(f"LLM config load error: {e}")
        # Fallback to basic config from unified config.yaml
        return get_config().get("llm", {})


def get_ollama_config() -> Dict[str, Any]:
    """Get Ollama configuration from specialized LLM configs."""
    llm_config = get_llm_config()
    return llm_config.get('providers', {}).get('ollama', {})


def get_gemini_config() -> Dict[str, Any]:
    """Get Gemini configuration from specialized LLM configs."""
    llm_config = get_llm_config()
    return llm_config.get('providers', {}).get('google_gemini', {})


def get_openai_config() -> Dict[str, Any]:
    """Get OpenAI configuration from specialized LLM configs."""
    llm_config = get_llm_config()
    return llm_config.get('providers', {}).get('openai', {})


def get_llm_cost_config() -> Dict[str, Any]:
    """Get LLM cost optimization configuration."""
    llm_config = get_llm_config()
    return llm_config.get('cost_optimization', {})


def get_llm_validation_config() -> Dict[str, Any]:
    """Get LLM output validation configuration."""
    llm_config = get_llm_config()
    return llm_config.get('output_validation', {})


def get_llm_security_config() -> Dict[str, Any]:
    """Get LLM system protection configuration."""
    llm_config = get_llm_config()
    return llm_config.get('system_protection', {})


def get_model_selection_config() -> Dict[str, Any]:
    """Get model selection and routing configuration."""
    llm_config = get_llm_config()
    return llm_config.get('model_selection', {})


def get_agent_registry_config() -> Dict[str, Any]:
    """Get agent registry configuration (enabled agents, priorities, execution strategy)."""
    agents_config = get_agents_config()
    return {
        "enabled_agents": agents_config.get("agents", {}).get("enabled_agents", []),
        "agent_priorities": agents_config.get("agents", {}).get("agent_priorities", {}),
        "execution_strategy": agents_config.get("agents", {}).get("execution_strategy", {}),
        "agent_configs": agents_config.get("agents", {}).get("agent_configs", {})
    }


def get_specific_agent_config(agent_name: str) -> Dict[str, Any]:
    """Get configuration for a specific agent."""
    agents_config = get_agents_config()
    agent_configurations = agents_config.get("agent_configurations", {})
    return agent_configurations.get(agent_name, {})


def get_environment_config(environment: Optional[str] = None) -> Dict[str, Any]:
    """
    Get environment-specific configuration.
    
    Args:
        environment: Environment name (development, staging, production). 
                    If None, will detect from main config.
    
    Returns:
        Dict containing environment-specific configuration
    """
    try:
        if environment is None:
            # Detect environment from main config or environment variable
            main_config = get_config()
            environment = main_config.get("environment", os.getenv("ENVIRONMENT", "development"))
        
        config_dir = Path(__file__).parent.parent.parent / "config" / "environments"
        env_path = config_dir / f"{environment}.yaml"
        
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as file:
                env_config = yaml.safe_load(file) or {}
                
                logger.info(f"Environment configuration loaded for {environment} with sections: {list(env_config.keys())}")
                
                return env_config
        else:
            logger.warning(f"Environment config not found: {environment}")
            return {}
            
    except Exception as e:
        logger.error(f"Environment config load error for {environment}: {e}")
        return {}


def get_analysis_config() -> Dict[str, Any]:
    """Get analysis configuration."""
    return get_config().get('analysis', {})


def get_security_patterns() -> Dict[str, List[str]]:
    """Get security patterns configuration."""
    return get_config().get('security_patterns', {})


def get_engineering_patterns() -> Dict[str, List[str]]:
    """Get engineering practices patterns."""
    return get_config().get('engineering_practices_patterns', {})


def get_agents_config() -> Dict[str, Any]:
    """
    Get comprehensive agents configuration by merging specialized agent config files.
    
    Returns:
        Dict containing complete agent configuration from config/agents/ directory
    """
    try:
        config_dir = Path(__file__).parent.parent.parent / "config" / "agents"
        
        # Load all agent configuration files
        agents_config = {}
        registry_config = {}
        
        # Load agent registry (authoritative for enabled agents and execution strategy)
        registry_path = config_dir / "agent_registry.yaml"
        if registry_path.exists():
            with open(registry_path, 'r', encoding='utf-8') as file:
                registry_config = yaml.safe_load(file) or {}
                agents_config.update(registry_config)
        
        # Load individual agent configurations
        agent_files = [
            "code_quality.yaml",
            "security_standards.yaml", 
            "architecture.yaml",
            "performance.yaml",
            "engineering_practices.yaml",
            "orchestrator.yaml",
            "specialized_agents.yaml",
            "custom_agents.yaml",
            "api_design.yaml",
            "cloud_native.yaml",
            "microservices.yaml",
            "sustainability.yaml"
        ]
        
        agent_configs = {}
        for agent_file in agent_files:
            agent_path = config_dir / agent_file
            if agent_path.exists():
                with open(agent_path, 'r', encoding='utf-8') as file:
                    agent_config = yaml.safe_load(file) or {}
                    if agent_config:  # Only add non-empty configs
                        agent_name = agent_file.replace('.yaml', '')
                        agent_configs[agent_name] = agent_config
        
        # Add individual agent configs to the main config
        if agent_configs:
            agents_config["agent_configurations"] = agent_configs
        
        # Merge with basic agent config from unified config.yaml
        unified_config = get_config()
        basic_agents = unified_config.get("agents", {})
        
        # Use specialized configs as primary, unified config as fallback
        final_config = {**basic_agents, **agents_config}
        
        enabled_agents = final_config.get("agents", {}).get("enabled_agents", [])
        logger.info(f"Agents configuration loaded - enabled agents: {enabled_agents}, total configs: {len(agent_configs)}, registry loaded: {bool(registry_config)}")
        
        return final_config
        
    except Exception as e:
        logger.error(f"Agents config load error: {e}")
        # Fallback to basic config from unified config.yaml
        return get_config().get("agents", {})


def get_session_config() -> Dict[str, Any]:
    """Get session configuration."""
    return get_config().get('session', {})


def get_http_config() -> Dict[str, Any]:
    """Get HTTP configuration."""
    return get_config().get('http', {})


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration."""
    return get_config().get('logging', {})


def get_monitoring_config() -> Dict[str, Any]:
    """Get monitoring configuration."""
    return get_config().get('monitoring', {})


def get_timeouts() -> Dict[str, int]:
    """Get timeout configuration."""
    return get_config().get('timeouts', {})


def get_rate_limits() -> Dict[str, Any]:
    """Get rate limiting configuration."""
    return get_config().get('rate_limiting', {})


def get_file_processing_config() -> Dict[str, Any]:
    """Get file processing configuration."""
    return get_config().get('file_processing', {})


def get_supported_languages() -> List[str]:
    """Get list of supported languages."""
    return get_analysis_config().get('supported_languages', [])


def get_language_extensions() -> Dict[str, List[str]]:
    """Get language to file extensions mapping."""
    return get_analysis_config().get('language_extensions', {})


def get_tree_sitter_languages() -> Dict[str, str]:
    """Get tree-sitter language mapping."""
    return get_analysis_config().get('tree_sitter_languages', {})


def get_complexity_thresholds() -> Dict[str, Dict[str, int]]:
    """Get complexity thresholds by language."""
    return get_analysis_config().get('language_thresholds', {})


def get_messages() -> Dict[str, Any]:
    """Get message templates."""
    return get_config().get('messages', {})


# Environment helpers
def is_development() -> bool:
    """Check if running in development environment."""
    return get_config().get('environment') == 'development'


def is_production() -> bool:
    """Check if running in production environment."""
    return get_config().get('environment') == 'production'


def get_environment() -> str:
    """Get current environment."""
    return get_config().get('environment', 'development')


def reload_config():
    """Reload configuration from disk."""
    global _CONFIG_CACHE
    _CONFIG_CACHE = None
    load_config()


# Export the main loader for backward compatibility
# Export all functions for use by other modules
__all__ = [
    # Core configuration functions
    "get_config",
    "get_app_config", 
    
    # Comprehensive LLM configuration functions  
    "get_llm_config",
    "get_ollama_config",
    "get_gemini_config", 
    "get_openai_config",
    "get_llm_cost_config",
    "get_llm_validation_config",
    "get_llm_security_config",
    "get_model_selection_config",
    
    # Other configuration functions
    "get_analysis_config",
    "get_security_patterns",
    "get_engineering_patterns", 
    "get_agents_config",
    "get_agent_registry_config",
    "get_specific_agent_config",
    "get_environment_config",
    "get_session_config",
    "get_http_config",
    "get_logging_config",
    "get_monitoring_config",
    "get_timeouts",
    "get_rate_limits",
]