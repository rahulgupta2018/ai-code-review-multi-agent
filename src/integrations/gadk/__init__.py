"""
GADK Integration Module for Google Cloud Agent Development

This module provides the main interface for Google GADK (Agent Development Kit) integration
with Vertex AI Agents, Discovery Engine, and Dialogflow CX services.

Main Components:
- GADKRuntimeFactory: Factory for creating and managing GADK runtime instances
- GADKCredentialManager: Secure credential management for Google Cloud services
- GADKSession: Session management for agent interactions
- Configuration utilities for environment and config-driven setup

Usage:
    from src.integrations.gadk import (
        GADKRuntimeFactory, 
        GADKCredentialManager,
        create_runtime_config_from_env
    )
    
    # Initialize credentials
    credential_manager = GADKCredentialManager()
    credential_manager.load_credentials()
    
    # Create runtime factory
    factory = GADKRuntimeFactory(config_manager)
    
    # Create runtime configuration
    config = create_runtime_config_from_env()
    
    # Initialize and use GADK runtime
    await factory.initialize_runtime(config)
"""

from .runtime.factory import (
    GADKRuntimeFactory,
    GADKRuntimeConfig, 
    GADKSession,
    create_runtime_config_from_env,
    create_runtime_config_from_config_manager
)

from .auth.credentials import (
    GADKCredentialManager,
    CredentialInfo,
    get_credentials_from_environment,
    validate_credentials_file,
    create_credential_manager_from_config,
    ensure_credentials_available
)

# Version information
__version__ = "0.1.0"
__author__ = "AI Code Review Team"
__description__ = "Google GADK Integration for Multi-Agent Code Review System"

# Main exports for external use
__all__ = [
    # Runtime factory and configuration
    "GADKRuntimeFactory",
    "GADKRuntimeConfig", 
    "GADKSession",
    "create_runtime_config_from_env",
    "create_runtime_config_from_config_manager",
    
    # Credential management
    "GADKCredentialManager",
    "CredentialInfo",
    "get_credentials_from_environment",
    "validate_credentials_file", 
    "create_credential_manager_from_config",
    "ensure_credentials_available",
    
    # Module metadata
    "__version__",
    "__author__",
    "__description__"
]


def get_module_info():
    """
    Get information about the GADK integration module.
    
    Returns:
        dict: Module information including version, components, and status
    """
    return {
        "name": "GADK Integration",
        "version": __version__,
        "description": __description__,
        "author": __author__,
        "components": {
            "runtime_factory": "Google Cloud service initialization and session management",
            "credential_manager": "Secure authentication and credential handling",
            "configuration": "Environment and config-driven setup utilities"
        },
        "supported_services": [
            "Google Cloud Vertex AI Agents",
            "Google Cloud Discovery Engine", 
            "Google Cloud Dialogflow CX"
        ],
        "features": [
            "Production-ready Google Cloud integration",
            "Session-based agent management",
            "Secure credential handling",
            "Configuration-driven setup",
            "Comprehensive error handling and logging",
            "Tool registration and lifecycle management"
        ]
    }


def validate_module_dependencies():
    """
    Validate that required dependencies are available for GADK integration.
    
    Returns:
        dict: Validation results with status and missing dependencies
    """
    validation_results = {
        "status": "valid",
        "missing_dependencies": [],
        "warnings": []
    }
    
    # Check for Google Cloud libraries
    try:
        import google.cloud.aiplatform
        import google.cloud.discoveryengine  
        import google.cloud.dialogflow_v2
        import google.auth
    except ImportError as e:
        validation_results["status"] = "invalid"
        validation_results["missing_dependencies"].append(f"Google Cloud libraries: {e}")
    
    # Check for required environment variables
    import os
    required_env_vars = ["GOOGLE_CLOUD_PROJECT_ID"]
    for var in required_env_vars:
        if not os.getenv(var):
            validation_results["warnings"].append(f"Environment variable {var} not set")
    
    return validation_results


# Initialize module-level logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"GADK Integration Module {__version__} loaded")

# Validate dependencies on import
dependency_status = validate_module_dependencies()
if dependency_status["status"] == "invalid":
    logger.warning(f"GADK module has missing dependencies: {dependency_status['missing_dependencies']}")
if dependency_status["warnings"]:
    logger.info(f"GADK module warnings: {dependency_status['warnings']}")