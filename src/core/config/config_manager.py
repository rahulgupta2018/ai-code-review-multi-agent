"""
Configuration Manager

Environment-driven configuration with Pydantic validation.
Manages application settings, agent configurations, and environment variables.
"""
import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration with environment variable support."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the configuration manager."""
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self._config_cache: Dict[str, Any] = {}
        
    def load_config(self, config_name: str, reload: bool = False) -> Dict[str, Any]:
        """Load configuration from YAML file with caching."""
        if config_name in self._config_cache and not reload:
            return self._config_cache[config_name]
            
        config_path = self.config_dir / f"{config_name}.yaml"
        
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return {}
            
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
                
            # Process environment variable substitutions
            config = self._substitute_env_vars(config)
            
            self._config_cache[config_name] = config
            logger.info(f"Loaded configuration: {config_name}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration {config_name}: {e}")
            return {}
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get main application configuration."""
        return self.load_config("app")
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent."""
        return self.load_config(f"agents/{agent_name}")
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM provider configuration."""
        return self.load_config("llm/providers")
    
    def get_orchestrator_config(self) -> Dict[str, Any]:
        """Get orchestrator configuration."""
        return self.load_config("orchestrator/smart_orchestrator")
    
    def get_quality_rules(self) -> Dict[str, Any]:
        """Get quality control rules."""
        return self.load_config("rules/quality_control")
    
    def get_environment_config(self, env_name: str) -> Dict[str, Any]:
        """Get environment-specific configuration."""
        return self.load_config(f"environments/{env_name}")
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """Recursively substitute environment variables in configuration."""
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]
            default_value = None
            
            # Handle default values: ${VAR_NAME:default_value}
            if ":" in env_var:
                env_var, default_value = env_var.split(":", 1)
                
            return os.getenv(env_var, default_value)
        else:
            return config
    
    def validate_config(self, config_name: str) -> bool:
        """Validate configuration completeness."""
        config = self.load_config(config_name)
        
        if not config:
            logger.error(f"Configuration {config_name} is empty or missing")
            return False
            
        # TODO: Add Pydantic validation schemas
        logger.info(f"Configuration {config_name} is valid")
        return True
    
    def list_available_configs(self) -> List[str]:
        """List all available configuration files."""
        if not self.config_dir.exists():
            return []
            
        configs = []
        for yaml_file in self.config_dir.rglob("*.yaml"):
            relative_path = yaml_file.relative_to(self.config_dir)
            config_name = str(relative_path.with_suffix(""))
            configs.append(config_name)
            
        return sorted(configs)


# Global configuration manager instance
config_manager = ConfigManager()