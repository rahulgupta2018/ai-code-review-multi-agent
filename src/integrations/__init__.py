"""
Integration modules for external services and tools.

This package contains integration modules for various external services
used by the agentic code review system.

Available integrations:
- agdk: Google AGDK (Agent Development Kit) integration for Vertex AI Agents,
        Discovery Engine, and Dialogflow CX
"""

from . import agdk

__all__ = ["agdk"]