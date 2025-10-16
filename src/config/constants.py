"""
Configuration constants for AI Code Review Multi-Agent System.

This module contains constants related to configuration infrastructure,
paths, and loading mechanisms.
"""

from pathlib import Path
from typing import Dict, Any

# Configuration file names and paths
CONFIG_DIR_NAME = "config"
CONFIG_FILE_EXTENSIONS = [".yaml", ".yml", ".json"]
DEFAULT_CONFIG_FILENAME = "application.yaml"

# Configuration keys for loading
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

# Default configuration values
DEFAULT_VALUES = {
    'environment': 'development',
    'debug': False,
    'log_level': 'INFO',
    'api_version': 'v1',
    'api_prefix': '/api/v1'
}

# Configuration validation constants
REQUIRED_CONFIG_SECTIONS = ['application', 'api', 'observability']
OPTIONAL_CONFIG_SECTIONS = ['llm', 'agents', 'environments']

# Environment variable constants
ENV_VAR_PREFIX = "ACRMA_"  # AI Code Review Multi-Agent
CONFIG_FILE_ENV_VAR = f"{ENV_VAR_PREFIX}CONFIG_FILE"
ENVIRONMENT_ENV_VAR = f"{ENV_VAR_PREFIX}ENVIRONMENT"
DEBUG_ENV_VAR = f"{ENV_VAR_PREFIX}DEBUG"

# Configuration loading timeouts (seconds)
CONFIG_LOAD_TIMEOUT = 30
CONFIG_VALIDATION_TIMEOUT = 10

# Configuration file size limits (bytes)
MAX_CONFIG_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def get_config_dir() -> Path:
    """Get the configuration directory path."""
    current_file = Path(__file__)
    # Go up to src, then src parent, then config
    repo_root = current_file.parent.parent.parent
    return repo_root / CONFIG_DIR_NAME


def get_default_config_paths() -> Dict[str, Path]:
    """Get default configuration file paths."""
    config_dir = get_config_dir()
    return {
        'application': config_dir / 'api' / 'application.yaml',
        'observability': config_dir / 'observability' / 'monitoring.yaml',
        'llm': config_dir / 'llm',
        'agents': config_dir / 'agents',
        'environments': config_dir / 'environments',
        'tree_sitter': config_dir / 'tree_sitter',
        'rules': config_dir / 'rules',
        'integrations': config_dir / 'integrations',
        'reporting': config_dir / 'reporting'
    }