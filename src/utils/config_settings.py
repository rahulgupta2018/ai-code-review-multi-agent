"""
Configuration settings classes for AI Code Review Multi-Agent System.

This module defines settings classes and configuration models
for structured access to configuration data.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ConfigSettings:
    """Main configuration settings class."""
    
    environment: str
    application: Dict[str, Any]
    api: Dict[str, Any]
    logging: Dict[str, Any]
    monitoring: Dict[str, Any]
    session: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ConfigSettings":
        """Create ConfigSettings from dictionary."""
        return cls(
            environment=config_dict.get("environment", "development"),
            application=config_dict.get("application", {}),
            api=config_dict.get("api", {}),
            logging=config_dict.get("logging", {}),
            monitoring=config_dict.get("monitoring", {}),
            session=config_dict.get("session", {}),
        )


@dataclass
class LLMSettings:
    """LLM configuration settings."""
    
    default_provider: str
    providers: Dict[str, Any]
    cost_optimization: Dict[str, Any]
    output_validation: Dict[str, Any]
    system_protection: Dict[str, Any]
    model_selection: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, llm_dict: Dict[str, Any]) -> "LLMSettings":
        """Create LLMSettings from dictionary."""
        return cls(
            default_provider=llm_dict.get("default_provider", "ollama"),
            providers=llm_dict.get("providers", {}),
            cost_optimization=llm_dict.get("cost_optimization", {}),
            output_validation=llm_dict.get("output_validation", {}),
            system_protection=llm_dict.get("system_protection", {}),
            model_selection=llm_dict.get("model_selection", {}),
        )


@dataclass
class AgentsSettings:
    """Agents configuration settings."""
    
    enabled_agents: List[str]
    agent_priorities: Dict[str, float]
    execution_strategy: Dict[str, Any]
    agent_configurations: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, agents_dict: Dict[str, Any]) -> "AgentsSettings":
        """Create AgentsSettings from dictionary."""
        agents_config = agents_dict.get("agents", {})
        return cls(
            enabled_agents=agents_config.get("enabled_agents", []),
            agent_priorities=agents_config.get("agent_priorities", {}),
            execution_strategy=agents_config.get("execution_strategy", {}),
            agent_configurations=agents_dict.get("agent_configurations", {}),
        )


@dataclass
class EnvironmentSettings:
    """Environment-specific configuration settings."""
    
    environment: str
    agents: Dict[str, Any]
    llm: Dict[str, Any]
    session: Dict[str, Any]
    quality_control: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, env_dict: Dict[str, Any]) -> "EnvironmentSettings":
        """Create EnvironmentSettings from dictionary."""
        return cls(
            environment=env_dict.get("environment", "development"),
            agents=env_dict.get("agents", {}),
            llm=env_dict.get("llm", {}),
            session=env_dict.get("session", {}),
            quality_control=env_dict.get("quality_control", {}),
        )