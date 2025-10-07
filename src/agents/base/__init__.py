"""
Base agent classes and interfaces for ADK integration.
Native Google ADK patterns - no custom framework.
"""

from .adk_agents import ADKAgentRegistry, ADKWorkflowManager, create_adk_system
from .base_classes import Finding, FindingSeverity, AnalysisContext, AnalysisResult

__all__ = [
    'Finding',
    'FindingSeverity', 
    'AnalysisContext',
    'AnalysisResult',
    'ADKAgentRegistry',
    'ADKWorkflowManager', 
    'create_adk_system'
]