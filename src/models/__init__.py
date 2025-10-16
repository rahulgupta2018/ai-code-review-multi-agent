"""
Pydantic models module for ADK Multi-Agent Code Review MVP.

This module provides comprehensive data models for all system components
including analysis, sessions, agents, workflows, tools, and reports.
"""

# Analysis models
from .analysis_models import (
    # Code models
    CodeFileModel,
    ComplexityMetricsModel,
    
    # Finding models
    QualityFindingModel,
    SecurityFindingModel,
    PerformanceFindingModel,
    FindingLocationModel,
    
    # Request/Response models
    AnalysisRequestModel,
    AnalysisResponseModel,
    FileAnalysisRequestModel,
    FileAnalysisResponseModel,
    BatchAnalysisRequestModel,
    BatchAnalysisResponseModel,
)

# Session models
from .session_models import (
    # Session core models
    SessionInfoModel,
    SessionConfigModel,
    SessionProgressModel,
    
    # Workflow execution models
    WorkflowExecutionModel,
    StepExecutionModel,
    
    # Request/Response models
    SessionCreateRequestModel,
    SessionResponseModel,
    SessionListRequestModel,
    SessionListResponseModel,
    SessionUpdateRequestModel,
)

# Agent models
from .agent_models import (
    # Configuration models
    AgentCapabilityModel,
    AgentModelConfigModel,
    AgentToolConfigModel,
    AgentConfigModel,
    
    # State models
    AgentStateModel,
    AgentExecutionContextModel,
    AgentResultModel,
    
    # Registry models
    AgentRegistryEntryModel,
    AgentMessageModel,
    
    # Request/Response models
    AgentExecutionRequestModel,
    AgentListRequestModel,
    AgentListResponseModel,
)

# Workflow models
from .workflow_models import (
    # Definition models
    WorkflowStepConditionModel,
    WorkflowStepModel,
    WorkflowDefinitionModel,
    
    # Execution models
    WorkflowStepExecutionModel,
    WorkflowExecutionModel,
    
    # Template models
    WorkflowTemplateModel,
    
    # Request/Response models
    WorkflowExecutionRequestModel,
    WorkflowStatusRequestModel,
    WorkflowListRequestModel,
    WorkflowListResponseModel,
)

# Tool models
from .tool_models import (
    # Configuration models
    ToolParameterModel,
    ToolCapabilityModel,
    ToolConfigModel,
    
    # Execution models
    ToolExecutionRequestModel,
    ToolExecutionResultModel,
    
    # Registry models
    ToolRegistryEntryModel,
    
    # Request/Response models
    ToolListRequestModel,
    ToolListResponseModel,
    ToolExecutionListRequestModel,
    ToolExecutionListResponseModel,
)

# Report models
from .report_models import (
    # Core models
    ReportMetadataModel,
    ReportSummaryModel,
    ReportFindingModel,
    ReportMetricsModel,
    ReportRecommendationModel,
    ReportModel,
    
    # Request/Response models
    ReportGenerationRequestModel,
    ReportGenerationResponseModel,
)


# Export all models for easy access
__all__ = [
    # Analysis models
    "CodeFileModel",
    "ComplexityMetricsModel",
    "QualityFindingModel",
    "SecurityFindingModel",
    "PerformanceFindingModel",
    "FindingLocationModel",
    "AnalysisRequestModel",
    "AnalysisResponseModel",
    "FileAnalysisRequestModel",
    "FileAnalysisResponseModel",
    "BatchAnalysisRequestModel",
    "BatchAnalysisResponseModel",
    
    # Session models
    "SessionInfoModel",
    "SessionConfigModel",
    "SessionProgressModel",
    "WorkflowExecutionModel",
    "StepExecutionModel",
    "SessionCreateRequestModel",
    "SessionResponseModel",
    "SessionListRequestModel",
    "SessionListResponseModel",
    "SessionUpdateRequestModel",
    
    # Agent models
    "AgentCapabilityModel",
    "AgentModelConfigModel",
    "AgentToolConfigModel",
    "AgentConfigModel",
    "AgentStateModel",
    "AgentExecutionContextModel",
    "AgentResultModel",
    "AgentRegistryEntryModel",
    "AgentMessageModel",
    "AgentExecutionRequestModel",
    "AgentListRequestModel",
    "AgentListResponseModel",
    
    # Workflow models
    "WorkflowStepConditionModel",
    "WorkflowStepModel",
    "WorkflowDefinitionModel",
    "WorkflowStepExecutionModel",
    "WorkflowExecutionModel",
    "WorkflowTemplateModel",
    "WorkflowExecutionRequestModel",
    "WorkflowStatusRequestModel",
    "WorkflowListRequestModel",
    "WorkflowListResponseModel",
    
    # Tool models
    "ToolParameterModel",
    "ToolCapabilityModel",
    "ToolConfigModel",
    "ToolExecutionRequestModel",
    "ToolExecutionResultModel",
    "ToolRegistryEntryModel",
    "ToolListRequestModel",
    "ToolListResponseModel",
    "ToolExecutionListRequestModel",
    "ToolExecutionListResponseModel",
    
    # Report models
    "ReportMetadataModel",
    "ReportSummaryModel",
    "ReportFindingModel",
    "ReportMetricsModel",
    "ReportRecommendationModel",
    "ReportModel",
    "ReportGenerationRequestModel",
    "ReportGenerationResponseModel",
]


# Model registry for dynamic access
MODEL_REGISTRY = {
    # Analysis models
    'analysis': {
        'CodeFileModel': CodeFileModel,
        'ComplexityMetricsModel': ComplexityMetricsModel,
        'QualityFindingModel': QualityFindingModel,
        'SecurityFindingModel': SecurityFindingModel,
        'PerformanceFindingModel': PerformanceFindingModel,
        'FindingLocationModel': FindingLocationModel,
        'AnalysisRequestModel': AnalysisRequestModel,
        'AnalysisResponseModel': AnalysisResponseModel,
    },
    
    # Session models
    'session': {
        'SessionInfoModel': SessionInfoModel,
        'SessionConfigModel': SessionConfigModel,
        'SessionProgressModel': SessionProgressModel,
        'WorkflowExecutionModel': WorkflowExecutionModel,
        'StepExecutionModel': StepExecutionModel,
    },
    
    # Agent models
    'agent': {
        'AgentConfigModel': AgentConfigModel,
        'AgentStateModel': AgentStateModel,
        'AgentResultModel': AgentResultModel,
        'AgentRegistryEntryModel': AgentRegistryEntryModel,
    },
    
    # Workflow models
    'workflow': {
        'WorkflowDefinitionModel': WorkflowDefinitionModel,
        'WorkflowExecutionModel': WorkflowExecutionModel,
        'WorkflowStepModel': WorkflowStepModel,
        'WorkflowTemplateModel': WorkflowTemplateModel,
    },
    
    # Tool models
    'tool': {
        'ToolConfigModel': ToolConfigModel,
        'ToolExecutionResultModel': ToolExecutionResultModel,
        'ToolRegistryEntryModel': ToolRegistryEntryModel,
    },
    
    # Report models
    'report': {
        'ReportModel': ReportModel,
        'ReportSummaryModel': ReportSummaryModel,
        'ReportFindingModel': ReportFindingModel,
        'ReportMetricsModel': ReportMetricsModel,
    },
}


def get_model_by_name(category: str, model_name: str):
    """
    Get a model class by category and name.
    
    Args:
        category: Model category (analysis, session, agent, workflow, tool, report)
        model_name: Model class name
        
    Returns:
        Model class or None if not found
    """
    return MODEL_REGISTRY.get(category, {}).get(model_name)


def get_models_by_category(category: str):
    """
    Get all models in a category.
    
    Args:
        category: Model category
        
    Returns:
        Dictionary of model classes or empty dict if category not found
    """
    return MODEL_REGISTRY.get(category, {})


def list_model_categories():
    """
    List all available model categories.
    
    Returns:
        List of category names
    """
    return list(MODEL_REGISTRY.keys())


def list_models_in_category(category: str):
    """
    List all model names in a category.
    
    Args:
        category: Model category
        
    Returns:
        List of model names or empty list if category not found
    """
    return list(MODEL_REGISTRY.get(category, {}).keys())
