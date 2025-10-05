"""
Integration modules for external services and tools.

This package contains integration modules for various external services
used by the agentic code review system.

Available integrations:
- gadk: Google GADK (Google Agent Development Kit) integration for Vertex AI Agents,
        Discovery Engine, and Dialogflow CX
"""

from . import gadk

__all__ = ["gadk"]