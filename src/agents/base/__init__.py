"""
Base agent classes and interfaces for ADK integration.
Native Google ADK patterns - no custom framework.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class FindingSeverity(Enum):
    """Severity levels for findings"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Finding:
    """Data class for analysis findings"""
    title: str
    description: str
    severity: FindingSeverity
    category: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: Optional[str] = None
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass 
class AnalysisContext:
    """Context for analysis operations"""
    files: List[Dict[str, Any]]
    configuration: Dict[str, Any]
    session_id: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AnalysisResult:
    """Result of analysis operation"""
    agent_name: str
    findings: List[Finding]
    metrics: Dict[str, Any]
    execution_time: float
    success: bool
    errors: List[str]
    metadata: Dict[str, Any]


__all__ = [
    'Finding',
    'FindingSeverity', 
    'AnalysisContext',
    'AnalysisResult'
]