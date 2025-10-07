"""$tool FunctionTool for architecture analysis"""
from google.cloud.aiplatform.adk.tools import FunctionTool
from ..base.tool_schemas import CodeFileInput, AnalysisOutput

def ${tool}_tool(file_input: CodeFileInput) -> AnalysisOutput:
    """TODO: Implement real $tool in Milestone 0.2"""
    return AnalysisOutput(
        file_path=file_input.file_path, findings=[], metrics={}, 
        confidence=0.0, processing_time=0.0,
        metadata={"tool": "$tool", "version": "0.1.0"}
    )

${tool^}Tool = FunctionTool(name="$tool", description="$tool analysis", function=${tool}_tool)
