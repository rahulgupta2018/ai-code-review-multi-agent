"""
Global service registry for artifact and session services.

This module provides a way for agents to access runner services
(artifact_service, session_service) without tight coupling.
"""

from typing import Optional
from google.adk.artifacts import BaseArtifactService
from google.adk.sessions import BaseSessionService


class ServiceRegistry:
    """Singleton registry for runner services."""
    
    _instance: Optional['ServiceRegistry'] = None
    _artifact_service: Optional[BaseArtifactService] = None
    _session_service: Optional[BaseSessionService] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register_artifact_service(cls, service: BaseArtifactService) -> None:
        """Register artifact service for agent access."""
        instance = cls()
        instance._artifact_service = service
    
    @classmethod
    def register_session_service(cls, service: BaseSessionService) -> None:
        """Register session service for agent access."""
        instance = cls()
        instance._session_service = service
    
    @classmethod
    def get_artifact_service(cls) -> Optional[BaseArtifactService]:
        """Get registered artifact service."""
        instance = cls()
        return instance._artifact_service
    
    @classmethod
    def get_session_service(cls) -> Optional[BaseSessionService]:
        """Get registered session service."""
        instance = cls()
        return instance._session_service
    
    @classmethod
    def clear(cls) -> None:
        """Clear registry (useful for testing)."""
        instance = cls()
        instance._artifact_service = None
        instance._session_service = None


# Convenience functions
def register_services(
    artifact_service: Optional[BaseArtifactService] = None,
    session_service: Optional[BaseSessionService] = None
) -> None:
    """Register services in one call."""
    if artifact_service:
        ServiceRegistry.register_artifact_service(artifact_service)
    if session_service:
        ServiceRegistry.register_session_service(session_service)


def get_artifact_service() -> Optional[BaseArtifactService]:
    """Get artifact service from registry."""
    return ServiceRegistry.get_artifact_service()


def get_session_service() -> Optional[BaseSessionService]:
    """Get session service from registry."""
    return ServiceRegistry.get_session_service()
