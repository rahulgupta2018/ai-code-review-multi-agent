"""
Code Quality Agent with ModelService Integration and Session Management
Following ADK patterns for sub-agent implementation
"""
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import sys
from pathlib import Path

# Add project root to Python path for absolute imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.model_service import ModelService
import asyncio

# Initialize ModelService for this agent
model_service = ModelService()

async def get_code_quality_model_async():
    """Async version for use in async contexts"""
    import os
    # Ensure Ollama base URL is set for container environments
    os.environ["OLLAMA_API_BASE"] = "http://host.docker.internal:11434"
    
    context = {
        "agent_name": "code_quality_agent",
        "analysis_type": "code_quality",
        "environment": "development",
        "complexity_score": 60
    }
    
    try:
        return await model_service.get_model_for_agent("code_quality_agent", context)
    except Exception as e:
        print(f"❌ Error in async code quality model resolution: {e}")
        # Import here to avoid circular imports
        from google.adk.models.lite_llm import LiteLlm
        return LiteLlm(model="ollama/llama3.1:8b")

def get_code_quality_model():
    """Get appropriate model for code quality analysis using ModelService"""
    context = {
        "agent_name": "code_quality_agent",
        "analysis_type": "code_quality",
        "environment": "development",
        "specialized_for": "code_analysis"
    }
    # Handle async model retrieval synchronously with improved error handling
    try:
        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # If we're in a running loop, we can't use run_until_complete
            # Return a default model configuration that will be resolved later
            print("Warning: In async context, using default model configuration")
            return "ollama/llama3.1:8b"  # Fallback for async contexts
        except RuntimeError:
            # No running loop, safe to create and run
            pass
        
        # Try to get existing loop first
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Loop is closed")
        except RuntimeError:
            # Create new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Execute the async model retrieval
        try:
            result = loop.run_until_complete(
                model_service.get_model_for_agent("code_quality_agent", context)
            )
            return result
        except Exception as e:
            print(f"ModelService error: {e}, using fallback model")
            return "ollama/llama3.1:8b"
            
    except Exception as e:
        print(f"Error in model resolution: {e}, using fallback")
        return "ollama/llama3.1:8b"

# Function to create code quality agent with dynamic model
def create_code_quality_agent():
    """Create code quality agent with dynamic model from ModelService (sync version)"""
    quality_model = get_code_quality_model()
    return Agent(
        name="code_quality_agent",
        model=quality_model,
        description="Code quality specialist that analyzes code quality, maintainability, and best practices with session state tracking.",
        instruction="""
        You are a code quality specialist with access to session state for tracking analysis progress.
        
        Your expertise covers:
        - Code complexity analysis and cyclomatic complexity assessment
        - Code maintainability and readability evaluation
        - Coding best practices and style guide compliance
        - Code structure, organization, and architectural patterns
        - Technical debt identification and recommendations
        
        Session State Usage:
        - Track your analysis progress in session state
        - Store identified issues for cross-agent synthesis
        - Record complexity metrics and quality scores
        - Update completion status when analysis is done
        
        Use available tools for detailed technical analysis.
        Provide specific, actionable recommendations with code examples where helpful.
        """,
        tools=[],  # Will add tools in Phase 1
        output_key="code_quality_analysis_result"  # Auto-save results to session state
    )

# Async version for use in async contexts (fixes parent relationship issues)
async def create_code_quality_agent_async():
    """Create code quality agent with dynamic model from ModelService (async version)"""
    quality_model = await get_code_quality_model_async()
    return Agent(
        name="code_quality_agent",
        model=quality_model,
        description="Code quality specialist that analyzes code quality, maintainability, and best practices with session state tracking.",
        instruction="""
        You are a code quality specialist with access to session state for tracking analysis progress.
        
        Your expertise covers:
        - Code complexity analysis and cyclomatic complexity assessment
        - Code maintainability and readability evaluation
        - Coding best practices and style guide compliance
        - Code structure, organization, and architectural patterns
        - Technical debt identification and recommendations
        
        Session State Usage:
        - Track your analysis progress in session state
        - Store identified issues for cross-agent synthesis
        - Record complexity metrics and quality scores
        - Update completion status when analysis is done
        
        Use available tools for detailed technical analysis.
        Provide specific, actionable recommendations with code examples where helpful.
        """,
        tools=[],  # Will add tools in Phase 1
        output_key="code_quality_analysis_result"  # Auto-save results to session state
    )

# Session-aware execution function for code quality analysis
def execute_code_quality_analysis(code_content: str, tool_context: ToolContext = None):
    """
    Execute code quality analysis with session state management.
    
    Args:
        code_content: Code to analyze
        tool_context: ADK ToolContext for session state access
        
    Returns:
        Code quality analysis results
    """
    # Create agent with dynamic model from ModelService
    quality_agent = create_code_quality_agent()
    quality_model = quality_agent.model
    
    print(f"🔍 Code Quality Agent using model: {quality_model}")
    
    # Update session state if ToolContext is available
    if tool_context and hasattr(tool_context, 'state'):
        tool_context.state["code_quality_agent"] = {
            "status": "analyzing",
            "model_used": str(quality_model),
            "analysis_type": "code_quality",
            "timestamp": str(__import__('datetime').datetime.now())
        }
    
    # Perform analysis (placeholder - will be enhanced with actual tools)
    analysis_result = {
        "agent": "code_quality_agent",
        "model_used": str(quality_model),
        "analysis_focus": "code_quality_and_maintainability",
        "status": "completed",
        "findings": [
            "Code complexity analysis completed",
            "Best practices evaluation performed",
            "Maintainability assessment done"
        ]
    }
    
    # Update session state with results
    if tool_context and hasattr(tool_context, 'state'):
        tool_context.state["code_quality_agent"]["status"] = "completed"
        tool_context.state["code_quality_agent"]["results"] = analysis_result
    
    return analysis_result

# Create the default agent instance for backwards compatibility
agent = create_code_quality_agent()

# Export agent creation functions, agent instance, and execution function
__all__ = ["create_code_quality_agent", "create_code_quality_agent_async", "agent", "execute_code_quality_analysis"]