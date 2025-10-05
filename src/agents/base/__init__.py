"""
Base agent classes and interfaces.

Provides the comprehensive BaseAgent foundation with memory integration,
GADK support, and advanced learning capabilities for all specialized agents.
"""

from .base_agent import (
    BaseAgent,
    Finding,
    FindingSeverity,
    AnalysisContext,
    AnalysisResult
)

__all__ = [
    'BaseAgent',
    'Finding', 
    'FindingSeverity',
    'AnalysisContext',
    'AnalysisResult'
]