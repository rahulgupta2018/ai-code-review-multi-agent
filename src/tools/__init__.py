"""
ADK-compatible tools for AI-powered code analysis.

This package provides a comprehensive suite of analysis tools designed to work
with Google ADK (Agent Development Kit) using FunctionTool and BaseToolset patterns.

Tool Categories:
- base: Core toolset framework and shared utilities
- code_analysis: General code structure and quality analysis
- security: Security vulnerability detection and compliance
- quality: Code quality metrics and maintainability scoring  
- architecture: Dependency analysis and design pattern recognition
- carbon_efficiency: Environmental impact and resource optimization
- cloud_native: Cloud-native architecture and container practices
- microservices: Service boundaries and communication patterns
- engineering_practices: Development processes and best practices
"""

__version__ = "0.1.0"

# Import core components (will be available as we implement them)
try:
    from .base.analysis_toolset import AnalysisToolset
    from .base.tool_schemas import (
        CodeAnalysisInput,
        CodeAnalysisOutput,
        SecurityAnalysisInput,
        SecurityAnalysisOutput,
        QualityAnalysisInput,
        QualityAnalysisOutput,
    )
    
    __all__ = [
        "AnalysisToolset",
        "CodeAnalysisInput",
        "CodeAnalysisOutput", 
        "SecurityAnalysisInput",
        "SecurityAnalysisOutput",
        "QualityAnalysisInput",
        "QualityAnalysisOutput",
    ]
except ImportError:
    # Components not yet implemented
    __all__ = []