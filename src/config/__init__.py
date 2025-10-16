"""
Configuration management for AI Code Review Multi-Agent System.

This module provides infrastructure configuration loading and management.
Separated from domain-specific concerns for better maintainability.
"""

from .loader import get_config, get_llm_config, get_agents_config, get_environment_config
from .settings import ConfigSettings

__all__ = [
    "get_config",
    "get_llm_config", 
    "get_agents_config",
    "get_environment_config",
    "ConfigSettings",
]