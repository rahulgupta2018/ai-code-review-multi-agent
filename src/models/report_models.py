"""
Pydantic models for report generation in ADK Multi-Agent Code Review MVP.

This module defines models for comprehensive code review reports, findings
aggregation, and presentation formatting.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import StrictStr, StrictInt, StrictFloat, StrictBool

from ..core.constants import (
    ReportType, ReportFormat, Priority, Severity, FindingCategory,
    SupportedLanguage
)


class ReportMetadataModel(BaseModel):
    """Model for report metadata."""
    report_id: StrictStr = Field(..., description="Unique report identifier")
    title: StrictStr = Field(..., description="Report title")
    description: Optional[StrictStr] = Field(default=None, description="Report description")
    
    # Generation info
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Report generation timestamp")
    generated_by: StrictStr = Field(..., description="Generator identifier")
    generator_version: StrictStr = Field(..., description="Generator version")
    
    # Source information
    session_id: StrictStr = Field(..., description="Source session ID")
    workflow_execution_id: Optional[StrictStr] = Field(default=None, description="Source workflow execution")
    correlation_id: Optional[StrictStr] = Field(default=None, description="Request correlation ID")
    
    # Report configuration
    report_type: ReportType = Field(..., description="Type of report")
    report_format: ReportFormat = Field(..., description="Report format")
    template_id: Optional[StrictStr] = Field(default=None, description="Template used")
    
    # Content scope
    include_summary: StrictBool = Field(default=True, description="Include executive summary")
    include_details: StrictBool = Field(default=True, description="Include detailed findings")
    include_metrics: StrictBool = Field(default=True, description="Include metrics and statistics")
    include_recommendations: StrictBool = Field(default=True, description="Include recommendations")
    include_charts: StrictBool = Field(default=False, description="Include charts and graphs")
    
    # Filtering criteria
    severity_filter: Optional[List[Severity]] = Field(default=None, description="Severity levels included")
    category_filter: Optional[List[FindingCategory]] = Field(default=None, description="Categories included")
    language_filter: Optional[List[SupportedLanguage]] = Field(default=None, description="Languages included")
    
    # Access and distribution
    access_level: StrictStr = Field(default="internal", description="Report access level")
    distribution_list: List[StrictStr] = Field(default_factory=list, description="Distribution list")
    expiry_date: Optional[datetime] = Field(default=None, description="Report expiry date")
    
    # Versioning
    version: StrictStr = Field(default="1.0.0", description="Report version")
    revision_notes: Optional[StrictStr] = Field(default=None, description="Revision notes")
    
    # Tags and classification
    tags: List[StrictStr] = Field(default_factory=list, description="Report tags")
    classification: Optional[StrictStr] = Field(default=None, description="Security classification")
    
    @validator('report_id')
    def validate_report_id(cls, v):
        """Validate report ID format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Report ID must be alphanumeric with underscores/hyphens")
        return v
    
    @validator('version')
    def validate_version(cls, v):
        """Validate version format."""
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError("Version must be in format x.y.z")
        return v
    
    @validator('access_level')
    def validate_access_level(cls, v):
        """Validate access level."""
        valid_levels = ['public', 'internal', 'confidential', 'restricted']
        if v not in valid_levels:
            raise ValueError(f"Access level must be one of: {valid_levels}")
        return v


class ReportSummaryModel(BaseModel):
    """Model for report executive summary."""
    # Overall assessment
    overall_score: StrictFloat = Field(ge=0.0, le=100.0, description="Overall quality score")
    grade: StrictStr = Field(..., description="Letter grade (A-F)")
    risk_level: StrictStr = Field(..., description="Overall risk level")
    
    # Statistics
    total_files_analyzed: StrictInt = Field(ge=0, description="Total files analyzed")
    total_lines_of_code: StrictInt = Field(ge=0, description="Total lines of code")
    total_findings: StrictInt = Field(ge=0, description="Total number of findings")
    
    # Findings breakdown
    critical_findings: StrictInt = Field(default=0, ge=0, description="Critical severity findings")
    high_findings: StrictInt = Field(default=0, ge=0, description="High severity findings")
    medium_findings: StrictInt = Field(default=0, ge=0, description="Medium severity findings")
    low_findings: StrictInt = Field(default=0, ge=0, description="Low severity findings")
    info_findings: StrictInt = Field(default=0, ge=0, description="Informational findings")
    
    # Category breakdown
    security_findings: StrictInt = Field(default=0, ge=0, description="Security findings")
    quality_findings: StrictInt = Field(default=0, ge=0, description="Code quality findings")
    performance_findings: StrictInt = Field(default=0, ge=0, description="Performance findings")
    maintainability_findings: StrictInt = Field(default=0, ge=0, description="Maintainability findings")
    compliance_findings: StrictInt = Field(default=0, ge=0, description="Compliance findings")
    
    # Key metrics
    complexity_score: Optional[StrictFloat] = Field(default=None, ge=0.0, description="Complexity score")
    maintainability_index: Optional[StrictFloat] = Field(default=None, ge=0.0, description="Maintainability index")
    test_coverage: Optional[StrictFloat] = Field(default=None, ge=0.0, le=100.0, description="Test coverage percentage")
    technical_debt_hours: Optional[StrictFloat] = Field(default=None, ge=0.0, description="Technical debt in hours")
    
    # Language distribution
    language_distribution: Dict[str, StrictInt] = Field(default_factory=dict, description="Lines of code by language")
    
    # Top issues
    top_issue_categories: List[Dict[str, Any]] = Field(default_factory=list, description="Top issue categories")
    most_affected_files: List[Dict[str, Any]] = Field(default_factory=list, description="Most affected files")
    
    # Recommendations summary
    priority_recommendations: List[StrictStr] = Field(default_factory=list, description="Priority recommendations")
    
    @validator('grade')
    def validate_grade(cls, v):
        """Validate letter grade."""
        valid_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F']
        if v not in valid_grades:
            raise ValueError(f"Grade must be one of: {valid_grades}")
        return v
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        """Validate risk level."""
        valid_levels = ['very_low', 'low', 'medium', 'high', 'very_high', 'critical']
        if v not in valid_levels:
            raise ValueError(f"Risk level must be one of: {valid_levels}")
        return v


class ReportFindingModel(BaseModel):
    """Model for report finding entry."""
    finding_id: StrictStr = Field(..., description="Unique finding identifier")
    title: StrictStr = Field(..., description="Finding title")
    description: StrictStr = Field(..., description="Detailed description")
    
    # Classification
    category: FindingCategory = Field(..., description="Finding category")
    severity: Severity = Field(..., description="Finding severity")
    confidence: StrictFloat = Field(ge=0.0, le=1.0, description="Confidence score")
    
    # Location information
    file_path: StrictStr = Field(..., description="File path")
    line_number: Optional[StrictInt] = Field(default=None, ge=1, description="Line number")
    column_number: Optional[StrictInt] = Field(default=None, ge=1, description="Column number")
    function_name: Optional[StrictStr] = Field(default=None, description="Function/method name")
    class_name: Optional[StrictStr] = Field(default=None, description="Class name")
    
    # Code context
    code_snippet: Optional[StrictStr] = Field(default=None, description="Relevant code snippet")
    context_lines: Optional[List[StrictStr]] = Field(default=None, description="Surrounding context lines")
    
    # Analysis details
    rule_id: Optional[StrictStr] = Field(default=None, description="Rule or check identifier")
    tool_name: StrictStr = Field(..., description="Analysis tool name")
    agent_id: Optional[StrictStr] = Field(default=None, description="Analyzing agent ID")
    
    # Impact assessment
    impact_description: Optional[StrictStr] = Field(default=None, description="Impact description")
    risk_score: Optional[StrictFloat] = Field(default=None, ge=0.0, le=100.0, description="Risk score")
    
    # Remediation
    recommendation: Optional[StrictStr] = Field(default=None, description="Remediation recommendation")
    fix_effort: Optional[StrictStr] = Field(default=None, description="Estimated fix effort")
    fix_priority: Optional[Priority] = Field(default=None, description="Fix priority")
    
    # References
    references: List[StrictStr] = Field(default_factory=list, description="Reference links")
    cwe_ids: List[StrictStr] = Field(default_factory=list, description="CWE identifiers")
    tags: List[StrictStr] = Field(default_factory=list, description="Finding tags")
    
    # Metadata
    first_detected: datetime = Field(default_factory=datetime.utcnow, description="First detection time")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    status: StrictStr = Field(default="open", description="Finding status")
    
    @validator('fix_effort')
    def validate_fix_effort(cls, v):
        """Validate fix effort."""
        if v is not None:
            valid_efforts = ['trivial', 'easy', 'medium', 'hard', 'very_hard']
            if v not in valid_efforts:
                raise ValueError(f"Fix effort must be one of: {valid_efforts}")
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate finding status."""
        valid_statuses = ['open', 'acknowledged', 'false_positive', 'fixed', 'wont_fix', 'duplicate']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v


class ReportMetricsModel(BaseModel):
    """Model for report metrics and statistics."""
    # Code metrics
    total_files: StrictInt = Field(ge=0, description="Total number of files")
    total_lines: StrictInt = Field(ge=0, description="Total lines of code")
    blank_lines: StrictInt = Field(default=0, ge=0, description="Blank lines")
    comment_lines: StrictInt = Field(default=0, ge=0, description="Comment lines")
    executable_lines: StrictInt = Field(default=0, ge=0, description="Executable lines")
    
    # Complexity metrics
    cyclomatic_complexity: Dict[str, StrictFloat] = Field(default_factory=dict, description="Cyclomatic complexity by file")
    cognitive_complexity: Dict[str, StrictFloat] = Field(default_factory=dict, description="Cognitive complexity by file")
    halstead_metrics: Dict[str, Any] = Field(default_factory=dict, description="Halstead complexity metrics")
    
    # Quality metrics
    maintainability_index: StrictFloat = Field(default=0.0, ge=0.0, description="Maintainability index")
    technical_debt_ratio: StrictFloat = Field(default=0.0, ge=0.0, description="Technical debt ratio")
    code_coverage: Optional[StrictFloat] = Field(default=None, ge=0.0, le=100.0, description="Test coverage")
    duplication_percentage: StrictFloat = Field(default=0.0, ge=0.0, le=100.0, description="Code duplication")
    
    # Language statistics
    language_breakdown: Dict[str, Dict[str, StrictInt]] = Field(
        default_factory=dict, description="Lines by language"
    )
    
    # Finding statistics
    findings_by_severity: Dict[str, StrictInt] = Field(default_factory=dict, description="Findings by severity")
    findings_by_category: Dict[str, StrictInt] = Field(default_factory=dict, description="Findings by category")
    findings_by_file: Dict[str, StrictInt] = Field(default_factory=dict, description="Findings by file")
    findings_by_tool: Dict[str, StrictInt] = Field(default_factory=dict, description="Findings by tool")
    
    # Performance metrics
    analysis_duration_seconds: StrictFloat = Field(ge=0.0, description="Total analysis duration")
    agent_execution_times: Dict[str, StrictFloat] = Field(default_factory=dict, description="Agent execution times")
    tool_execution_times: Dict[str, StrictFloat] = Field(default_factory=dict, description="Tool execution times")
    
    # Trend data
    trend_data: Dict[str, List[Any]] = Field(default_factory=dict, description="Trend analysis data")
    historical_comparison: Dict[str, Any] = Field(default_factory=dict, description="Historical comparison")
    
    # Custom metrics
    custom_metrics: Dict[str, Any] = Field(default_factory=dict, description="Custom metrics")


class ReportRecommendationModel(BaseModel):
    """Model for report recommendations."""
    recommendation_id: StrictStr = Field(..., description="Unique recommendation identifier")
    title: StrictStr = Field(..., description="Recommendation title")
    description: StrictStr = Field(..., description="Detailed description")
    
    # Classification
    category: StrictStr = Field(..., description="Recommendation category")
    priority: Priority = Field(..., description="Implementation priority")
    impact: StrictStr = Field(..., description="Expected impact level")
    
    # Implementation details
    effort_estimate: StrictStr = Field(..., description="Implementation effort estimate")
    timeline: StrictStr = Field(..., description="Suggested timeline")
    prerequisites: List[StrictStr] = Field(default_factory=list, description="Prerequisites")
    
    # Supporting evidence
    related_findings: List[StrictStr] = Field(default_factory=list, description="Related finding IDs")
    metrics_evidence: Dict[str, Any] = Field(default_factory=dict, description="Supporting metrics")
    
    # Implementation guidance
    implementation_steps: List[StrictStr] = Field(default_factory=list, description="Implementation steps")
    tools_suggested: List[StrictStr] = Field(default_factory=list, description="Suggested tools")
    best_practices: List[StrictStr] = Field(default_factory=list, description="Best practices")
    
    # References
    references: List[StrictStr] = Field(default_factory=list, description="Reference materials")
    
    # Tracking
    status: StrictStr = Field(default="open", description="Recommendation status")
    assignee: Optional[StrictStr] = Field(default=None, description="Assigned to")
    due_date: Optional[datetime] = Field(default=None, description="Due date")
    
    @validator('category')
    def validate_category(cls, v):
        """Validate recommendation category."""
        valid_categories = [
            'security', 'performance', 'maintainability', 'testing',
            'documentation', 'architecture', 'compliance', 'tooling'
        ]
        if v not in valid_categories:
            raise ValueError(f"Category must be one of: {valid_categories}")
        return v
    
    @validator('impact')
    def validate_impact(cls, v):
        """Validate impact level."""
        valid_impacts = ['low', 'medium', 'high', 'very_high']
        if v not in valid_impacts:
            raise ValueError(f"Impact must be one of: {valid_impacts}")
        return v
    
    @validator('effort_estimate')
    def validate_effort_estimate(cls, v):
        """Validate effort estimate."""
        valid_efforts = ['low', 'medium', 'high', 'very_high']
        if v not in valid_efforts:
            raise ValueError(f"Effort estimate must be one of: {valid_efforts}")
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate recommendation status."""
        valid_statuses = ['open', 'in_progress', 'completed', 'deferred', 'rejected']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v


class ReportModel(BaseModel):
    """Main model for comprehensive code review report."""
    # Core components
    metadata: ReportMetadataModel = Field(..., description="Report metadata")
    summary: ReportSummaryModel = Field(..., description="Executive summary")
    findings: List[ReportFindingModel] = Field(default_factory=list, description="Detailed findings")
    metrics: ReportMetricsModel = Field(..., description="Metrics and statistics")
    recommendations: List[ReportRecommendationModel] = Field(default_factory=list, description="Recommendations")
    
    # Additional sections
    appendices: Dict[str, Any] = Field(default_factory=dict, description="Additional appendices")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw analysis data")
    
    # Generation tracking
    generation_log: List[Dict[str, Any]] = Field(default_factory=list, description="Generation process log")
    errors_encountered: List[Dict[str, Any]] = Field(default_factory=list, description="Errors during generation")
    
    # Validation
    validation_status: StrictStr = Field(default="pending", description="Report validation status")
    validation_errors: List[StrictStr] = Field(default_factory=list, description="Validation errors")
    
    def add_finding(self, finding: ReportFindingModel) -> None:
        """Add a finding to the report."""
        self.findings.append(finding)
    
    def add_recommendation(self, recommendation: ReportRecommendationModel) -> None:
        """Add a recommendation to the report."""
        self.recommendations.append(recommendation)
    
    def get_findings_by_severity(self, severity: Severity) -> List[ReportFindingModel]:
        """Get findings by severity level."""
        return [f for f in self.findings if f.severity == severity]
    
    def get_findings_by_category(self, category: FindingCategory) -> List[ReportFindingModel]:
        """Get findings by category."""
        return [f for f in self.findings if f.category == category]
    
    def calculate_risk_score(self) -> float:
        """Calculate overall risk score."""
        if not self.findings:
            return 0.0
        
        severity_weights = {
            Severity.CRITICAL: 10.0,
            Severity.HIGH: 7.0,
            Severity.MEDIUM: 4.0,
            Severity.LOW: 2.0,
            Severity.INFO: 0.5
        }
        
        total_risk = sum(
            severity_weights.get(f.severity, 0.0) * f.confidence
            for f in self.findings
        )
        
        # Normalize to 0-100 scale
        max_possible_risk = len(self.findings) * 10.0
        return min(100.0, (total_risk / max_possible_risk) * 100.0) if max_possible_risk > 0 else 0.0


# Request/Response Models
class ReportGenerationRequestModel(BaseModel):
    """Model for report generation request."""
    session_id: StrictStr = Field(..., description="Source session ID")
    report_type: ReportType = Field(..., description="Type of report to generate")
    report_format: ReportFormat = Field(..., description="Output format")
    
    # Configuration
    template_id: Optional[StrictStr] = Field(default=None, description="Report template")
    title: Optional[StrictStr] = Field(default=None, description="Custom report title")
    
    # Content options
    include_summary: StrictBool = Field(default=True, description="Include summary")
    include_findings: StrictBool = Field(default=True, description="Include findings")
    include_metrics: StrictBool = Field(default=True, description="Include metrics")
    include_recommendations: StrictBool = Field(default=True, description="Include recommendations")
    include_charts: StrictBool = Field(default=False, description="Include charts")
    
    # Filters
    severity_filter: Optional[List[Severity]] = Field(default=None, description="Severity filter")
    category_filter: Optional[List[FindingCategory]] = Field(default=None, description="Category filter")
    
    # Distribution
    recipients: List[StrictStr] = Field(default_factory=list, description="Report recipients")
    delivery_method: StrictStr = Field(default="download", description="Delivery method")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Request metadata")


class ReportGenerationResponseModel(BaseModel):
    """Model for report generation response."""
    report_id: StrictStr = Field(..., description="Generated report ID")
    status: StrictStr = Field(..., description="Generation status")
    download_url: Optional[StrictStr] = Field(default=None, description="Download URL")
    preview_url: Optional[StrictStr] = Field(default=None, description="Preview URL")
    file_size_bytes: Optional[StrictInt] = Field(default=None, description="File size")
    generation_time_seconds: StrictFloat = Field(ge=0.0, description="Generation time")
    expires_at: Optional[datetime] = Field(default=None, description="Download expiration")


# Export all models
__all__ = [
    # Core models
    "ReportMetadataModel",
    "ReportSummaryModel",
    "ReportFindingModel",
    "ReportMetricsModel",
    "ReportRecommendationModel",
    "ReportModel",
    
    # Request/Response models
    "ReportGenerationRequestModel",
    "ReportGenerationResponseModel",
]
