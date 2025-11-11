"""
Pydantic models for analysis requests and responses in ADK Multi-Agent Code Review MVP.

This module defines comprehensive data models with validation for all analysis-related
operations including requests, responses, findings, and metrics.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import StrictStr, StrictInt, StrictFloat, StrictBool

from ..utils.constants import (
    AgentType, Priority, MAX_FILE_SIZE, MAX_FINDINGS_PER_AGENT
)


class BaseTimestampedModel(BaseModel):
    """Base model with timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z'
        }


# File and Content Models
class CodeFileModel(BaseModel):
    """Model for code file input."""
    filename: StrictStr = Field(..., min_length=1, max_length=MAX_FILENAME_LENGTH, description="File name")
    language: SupportedLanguage = Field(..., description="Programming language")
    content: StrictStr = Field(..., min_length=1, description="File content")
    size_bytes: StrictInt = Field(..., ge=1, le=MAX_FILE_SIZE_BYTES, description="File size in bytes")
    encoding: StrictStr = Field(default="utf-8", description="File encoding")
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename for security."""
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("Filename contains invalid path characters")
        if any(char in v for char in ['<', '>', ':', '"', '|', '?', '*']):
            raise ValueError("Filename contains invalid characters")
        return v
    
    @validator('content')
    def validate_content(cls, v):
        """Validate content."""
        if '\0' in v:
            raise ValueError("Binary content is not supported")
        try:
            v.encode('utf-8')
        except UnicodeEncodeError:
            raise ValueError("Content contains invalid UTF-8 characters")
        return v
    
    @validator('size_bytes')
    def validate_size_matches_content(cls, v, values):
        """Validate that size_bytes matches actual content size."""
        if 'content' in values:
            actual_size = len(values['content'].encode('utf-8'))
            if abs(v - actual_size) > 10:  # Allow small variance for encoding differences
                raise ValueError(f"Declared size ({v}) doesn't match actual size ({actual_size})")
        return v


class FileMetadataModel(BaseModel):
    """Model for file metadata."""
    filename: StrictStr = Field(..., description="File name")
    language: SupportedLanguage = Field(..., description="Programming language")
    size_bytes: StrictInt = Field(..., ge=0, description="File size in bytes")
    lines_count: StrictInt = Field(..., ge=0, description="Number of lines")
    encoding: StrictStr = Field(default="utf-8", description="File encoding")
    last_modified: Optional[datetime] = Field(default=None, description="Last modification time")
    checksum: Optional[StrictStr] = Field(default=None, description="File checksum")


# Complexity and Metrics Models
class ComplexityMetricsModel(BaseModel):
    """Model for code complexity metrics."""
    cyclomatic: StrictInt = Field(ge=0, description="Cyclomatic complexity")
    cognitive: StrictInt = Field(ge=0, description="Cognitive complexity")
    halstead_volume: Optional[StrictFloat] = Field(default=None, ge=0, description="Halstead volume")
    halstead_difficulty: Optional[StrictFloat] = Field(default=None, ge=0, description="Halstead difficulty")
    maintainability_index: Optional[StrictFloat] = Field(default=None, ge=0, le=100, description="Maintainability index")
    lines_of_code: StrictInt = Field(ge=0, description="Lines of code")
    logical_lines: StrictInt = Field(ge=0, description="Logical lines of code")
    comment_lines: StrictInt = Field(ge=0, description="Comment lines")
    blank_lines: StrictInt = Field(ge=0, description="Blank lines")
    nesting_depth: StrictInt = Field(ge=0, description="Maximum nesting depth")
    
    @validator('logical_lines')
    def validate_logical_lines(cls, v, values):
        """Validate logical lines doesn't exceed total lines."""
        if 'lines_of_code' in values and v > values['lines_of_code']:
            raise ValueError("Logical lines cannot exceed total lines of code")
        return v
    
    @root_validator
    def validate_line_counts(cls, values):
        """Validate that line counts are consistent."""
        loc = values.get('lines_of_code', 0)
        logical = values.get('logical_lines', 0)
        comments = values.get('comment_lines', 0)
        blanks = values.get('blank_lines', 0)
        
        # Total lines should be at least the sum of logical + comment + blank
        # (allowing for some overlap in counting methods)
        if logical + comments + blanks > loc * 1.5:  # Allow 50% overlap
            raise ValueError("Line count components are inconsistent")
        
        return values


# Finding Models
class BaseFindingModel(BaseTimestampedModel):
    """Base model for analysis findings."""
    title: StrictStr = Field(..., min_length=1, max_length=200, description="Finding title")
    description: StrictStr = Field(..., min_length=1, max_length=2000, description="Finding description")
    severity: Severity = Field(..., description="Finding severity")
    file_path: StrictStr = Field(..., description="File path where finding was detected")
    line_number: Optional[StrictInt] = Field(default=None, ge=1, description="Line number")
    column_number: Optional[StrictInt] = Field(default=None, ge=1, description="Column number")
    code_snippet: Optional[StrictStr] = Field(default=None, max_length=1000, description="Code snippet")
    recommendation: StrictStr = Field(..., min_length=1, max_length=1000, description="Recommendation")
    confidence: StrictFloat = Field(ge=0.0, le=1.0, description="Confidence score")


class QualityFindingModel(BaseFindingModel):
    """Model for code quality findings."""
    metrics: ComplexityMetricsModel = Field(..., description="Associated complexity metrics")
    suggestion: StrictStr = Field(..., max_length=500, description="Improvement suggestion")
    impact: StrictStr = Field(..., max_length=300, description="Impact description")
    category: StrictStr = Field(..., description="Quality category")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "High Cyclomatic Complexity",
                "description": "Function has cyclomatic complexity of 15, exceeding threshold of 10",
                "severity": "warning",
                "file_path": "src/complex_function.py",
                "line_number": 25,
                "code_snippet": "def complex_function(x, y, z):",
                "recommendation": "Break down function into smaller, more focused functions",
                "confidence": 0.9,
                "metrics": {
                    "cyclomatic": 15,
                    "cognitive": 18,
                    "lines_of_code": 45,
                    "logical_lines": 35,
                    "comment_lines": 5,
                    "blank_lines": 5,
                    "nesting_depth": 4
                },
                "suggestion": "Extract complex logic into separate functions",
                "impact": "Reduces maintainability and testability",
                "category": "complexity"
            }
        }


class SecurityFindingModel(BaseFindingModel):
    """Model for security findings."""
    category: SecurityCategory = Field(..., description="Security category")
    cwe_id: Optional[StrictStr] = Field(default=None, description="CWE identifier")
    owasp_category: Optional[StrictStr] = Field(default=None, description="OWASP category")
    risk_score: StrictFloat = Field(ge=0.0, le=10.0, description="Risk score (0-10)")
    
    @validator('cwe_id')
    def validate_cwe_id(cls, v):
        """Validate CWE ID format."""
        if v and not v.startswith('CWE-'):
            raise ValueError("CWE ID must start with 'CWE-'")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Potential SQL Injection",
                "description": "SQL query constructed using string concatenation",
                "severity": "high",
                "file_path": "src/database.py",
                "line_number": 42,
                "code_snippet": "query = 'SELECT * FROM users WHERE id = ' + user_id",
                "recommendation": "Use parameterized queries or ORM",
                "confidence": 0.85,
                "category": "injection",
                "cwe_id": "CWE-89",
                "owasp_category": "A03:2021 – Injection",
                "risk_score": 8.5
            }
        }


class EngineeringPracticeFindingModel(BaseFindingModel):
    """Model for engineering practice findings."""
    category: EngineeringPracticeCategory = Field(..., description="Engineering practice category")
    impact: StrictStr = Field(..., max_length=300, description="Impact on engineering practices")
    effort: StrictStr = Field(..., max_length=200, description="Effort required to fix")
    best_practice: StrictStr = Field(..., max_length=500, description="Best practice guidance")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Missing Error Handling",
                "description": "Function lacks proper error handling for network operations",
                "severity": "warning",
                "file_path": "src/api_client.py",
                "line_number": 30,
                "code_snippet": "response = requests.get(url)",
                "recommendation": "Add try-catch blocks for network errors",
                "confidence": 0.8,
                "category": "error_handling",
                "impact": "Potential application crashes from unhandled exceptions",
                "effort": "Low - Add try-catch block",
                "best_practice": "Always handle exceptions for external dependencies"
            }
        }


# Analysis Request Models
class AnalysisOptionsModel(BaseModel):
    """Model for analysis options."""
    include_metrics: StrictBool = Field(default=True, description="Include complexity metrics")
    include_suggestions: StrictBool = Field(default=True, description="Include improvement suggestions")
    severity_threshold: Severity = Field(default=Severity.INFO, description="Minimum severity to report")
    max_findings_per_file: StrictInt = Field(default=50, ge=1, le=1000, description="Maximum findings per file")
    enable_security_scan: StrictBool = Field(default=True, description="Enable security scanning")
    enable_best_practices: StrictBool = Field(default=True, description="Enable best practices checking")
    custom_rules: List[StrictStr] = Field(default_factory=list, description="Custom analysis rules")


class AnalysisRequestModel(BaseTimestampedModel):
    """Model for analysis request."""
    files: List[CodeFileModel] = Field(..., min_items=1, max_items=MAX_FILES_PER_REQUEST, description="Files to analyze")
    analysis_types: List[AnalysisType] = Field(default_factory=lambda: [AnalysisType.COMPREHENSIVE], description="Types of analysis to perform")
    options: AnalysisOptionsModel = Field(default_factory=AnalysisOptionsModel, description="Analysis options")
    correlation_id: StrictStr = Field(..., min_length=1, max_length=100, description="Request correlation ID")
    priority: Priority = Field(default=Priority.MEDIUM, description="Request priority")
    callback_url: Optional[StrictStr] = Field(default=None, description="Callback URL for async results")
    
    @validator('files')
    def validate_total_file_size(cls, v):
        """Validate total size of all files."""
        total_size = sum(file.size_bytes for file in v)
        max_total = MAX_FILES_PER_REQUEST * MAX_FILE_SIZE_BYTES
        if total_size > max_total:
            raise ValueError(f"Total file size ({total_size}) exceeds limit ({max_total})")
        return v
    
    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        """Validate analysis types."""
        if not v:
            raise ValueError("At least one analysis type must be specified")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "files": [
                    {
                        "filename": "example.py",
                        "language": "python",
                        "content": "def hello_world():\n    print('Hello, World!')\n",
                        "size_bytes": 45,
                        "encoding": "utf-8"
                    }
                ],
                "analysis_types": ["comprehensive"],
                "options": {
                    "include_metrics": True,
                    "include_suggestions": True,
                    "severity_threshold": "info",
                    "max_findings_per_file": 50
                },
                "correlation_id": "req-12345-67890",
                "priority": "medium"
            }
        }


# Analysis Result Models
class AgentResultModel(BaseTimestampedModel):
    """Base model for agent analysis results."""
    agent_id: StrictStr = Field(..., description="Agent identifier")
    agent_type: AgentType = Field(..., description="Type of agent")
    status: StrictStr = Field(..., description="Execution status")
    execution_time_seconds: StrictFloat = Field(ge=0, description="Execution time in seconds")
    error_message: Optional[StrictStr] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CodeQualityResultModel(AgentResultModel):
    """Model for code quality analysis results."""
    findings: List[QualityFindingModel] = Field(default_factory=list, description="Quality findings")
    overall_metrics: ComplexityMetricsModel = Field(..., description="Overall complexity metrics")
    quality_score: StrictFloat = Field(ge=0.0, le=100.0, description="Overall quality score")
    summary: StrictStr = Field(..., description="Analysis summary")
    recommendations: List[StrictStr] = Field(default_factory=list, description="Overall recommendations")
    files_analyzed: StrictInt = Field(ge=0, description="Number of files analyzed")
    
    @validator('quality_score')
    def validate_quality_score(cls, v):
        """Validate quality score is reasonable."""
        if v < 0 or v > 100:
            raise ValueError("Quality score must be between 0 and 100")
        return v


class SecurityResultModel(AgentResultModel):
    """Model for security analysis results."""
    findings: List[SecurityFindingModel] = Field(default_factory=list, description="Security findings")
    risk_score: StrictFloat = Field(ge=0.0, le=10.0, description="Overall risk score")
    summary: StrictStr = Field(..., description="Security analysis summary")
    critical_issues_count: StrictInt = Field(ge=0, description="Number of critical issues")
    high_issues_count: StrictInt = Field(ge=0, description="Number of high severity issues")
    recommendations: List[StrictStr] = Field(default_factory=list, description="Security recommendations")
    compliance_status: Dict[str, bool] = Field(default_factory=dict, description="Compliance check results")


class EngineeringPracticesResultModel(AgentResultModel):
    """Model for engineering practices analysis results."""
    findings: List[EngineeringPracticeFindingModel] = Field(default_factory=list, description="Practice findings")
    practice_score: StrictFloat = Field(ge=0.0, le=100.0, description="Overall practices score")
    summary: StrictStr = Field(..., description="Practices analysis summary")
    areas_for_improvement: List[StrictStr] = Field(default_factory=list, description="Areas needing improvement")
    recommendations: List[StrictStr] = Field(default_factory=list, description="Practice recommendations")
    coverage_metrics: Dict[str, StrictFloat] = Field(default_factory=dict, description="Coverage metrics")


# Comprehensive Analysis Response
class AnalysisResponseModel(BaseTimestampedModel):
    """Model for complete analysis response."""
    session_id: StrictStr = Field(..., description="Session identifier")
    correlation_id: StrictStr = Field(..., description="Request correlation identifier")
    status: StrictStr = Field(..., description="Overall analysis status")
    results: Dict[AgentType, Union[CodeQualityResultModel, SecurityResultModel, EngineeringPracticesResultModel]] = Field(
        default_factory=dict, description="Results from each agent"
    )
    summary: StrictStr = Field(..., description="Overall analysis summary")
    overall_score: StrictFloat = Field(ge=0.0, le=100.0, description="Overall code score")
    execution_time_seconds: StrictFloat = Field(ge=0, description="Total execution time")
    files_processed: StrictInt = Field(ge=0, description="Number of files processed")
    total_findings: StrictInt = Field(ge=0, description="Total number of findings")
    
    @root_validator
    def validate_results_consistency(cls, values):
        """Validate that results are consistent with status."""
        status = values.get('status')
        results = values.get('results', {})
        
        if status == 'completed' and not results:
            raise ValueError("Completed analysis must have results")
        
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "sess-12345-67890",
                "correlation_id": "req-12345-67890",
                "status": "completed",
                "results": {},
                "summary": "Analysis completed successfully with 5 findings",
                "overall_score": 85.5,
                "execution_time_seconds": 45.2,
                "files_processed": 3,
                "total_findings": 5
            }
        }


# Export all models
__all__ = [
    # Base models
    "BaseTimestampedModel",
    
    # File models
    "CodeFileModel",
    "FileMetadataModel",
    
    # Metrics models
    "ComplexityMetricsModel",
    
    # Finding models
    "BaseFindingModel",
    "QualityFindingModel",
    "SecurityFindingModel",
    "EngineeringPracticeFindingModel",
    
    # Request models
    "AnalysisOptionsModel",
    "AnalysisRequestModel",
    
    # Result models
    "AgentResultModel",
    "CodeQualityResultModel",
    "SecurityResultModel",
    "EngineeringPracticesResultModel",
    "AnalysisResponseModel",
]
