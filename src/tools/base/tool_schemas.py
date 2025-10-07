"""
Input/output schemas for ADK FunctionTools
Type definitions for tool parameters and return values
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class AnalysisLanguage(Enum):
    """Supported programming languages for analysis"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    CSHARP = "csharp"


@dataclass
class CodeFileInput:
    """Input schema for code file analysis"""
    file_path: str
    content: str
    language: AnalysisLanguage
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AnalysisOutput:
    """Base output schema for analysis results"""
    file_path: str
    findings: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    confidence: float
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SecurityFinding:
    """Security analysis finding schema"""
    vulnerability_type: str
    severity: str
    cwe_id: Optional[str]
    line_number: int
    code_snippet: str
    recommendation: str
    confidence: float


@dataclass
class QualityMetric:
    """Code quality metric schema"""
    metric_name: str
    value: Union[int, float, str]
    threshold: Union[int, float]
    status: str  # "pass", "warning", "fail"
    description: str


@dataclass
class ArchitectureIssue:
    """Architecture analysis issue schema"""
    issue_type: str
    component: str
    description: str
    impact: str
    recommendation: str
    effort_estimate: str


__all__ = [
    'AnalysisLanguage',
    'CodeFileInput',
    'AnalysisOutput',
    'SecurityFinding',
    'QualityMetric',
    'ArchitectureIssue'
]