"""
ADK-Compliant Code Review Orchestrator Agent
Following Google ADK tutorial patterns with ModelService integration
"""
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
import sys
from pathlib import Path

# Add project root to Python path for absolute imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.model_service import ModelService

# Import sub-agent creation functions instead of instances to avoid parent conflicts
from .sub_agents.code_quality_agent.agent import create_code_quality_agent_async

async def get_sub_agents_list():
    """Get fresh sub-agent instances to avoid parent conflicts (async version)"""
    # Create fresh agent instances each time to avoid parent relationship conflicts
    code_quality_agent = await create_code_quality_agent_async()
    return [code_quality_agent]

def get_sub_agents_list_sync():
    """Get fresh sub-agent instances to avoid parent conflicts (sync version for module-level)"""
    from .sub_agents.code_quality_agent.agent import create_code_quality_agent
    # Create fresh agent instances each time
    code_quality_agent = create_code_quality_agent()
    return [code_quality_agent]


# Initialize ModelService for dynamic model selection
model_service = ModelService() if ModelService else None

# Function to get appropriate model for orchestrator
def get_orchestrator_model_sync():
    """Get orchestrator model from ModelService (simplified synchronous version)"""
    import os
    # Ensure Ollama base URL is set for container environments
    os.environ["OLLAMA_API_BASE"] = "http://host.docker.internal:11434"
    
    # Simplified approach - use direct configuration instead of complex async/sync mixing
    # This avoids event loop conflicts and is more reliable for ADK agent patterns
    return LiteLlm(model="ollama/llama3.1:8b")

# Async version for use in async contexts
async def get_orchestrator_model_async():
    """Get orchestrator model from ModelService (asynchronous version)"""
    import os
    # Ensure Ollama base URL is set for container environments
    os.environ["OLLAMA_API_BASE"] = "http://host.docker.internal:11434"
    
    model_service = ModelService()
    
    # Create context for model selection
    context = {
        "agent_name": "code_review_orchestrator",
        "analysis_type": "orchestration", 
        "environment": "development",
        "complexity_score": 50
    }
    
    try:
        return await model_service.get_model_for_agent("code_review_orchestrator", context)
    except Exception as e:
        print(f"❌ Error in async model resolution: {e}")
        # Fallback to direct model
        return LiteLlm(model="ollama/llama3.1:8b")

# Main orchestrator agent following ADK patterns with ModelService integration
async def create_orchestrator_agent():
    """Create orchestrator agent with dynamic model from ModelService"""
    orchestrator_model = await get_orchestrator_model_async()
    sub_agents = await get_sub_agents_list()  # Use async version
    return Agent(
        name="code_review_orchestrator",
        model=orchestrator_model,
        description="Code review orchestrator that coordinates specialized analysis agents with ModelService integration and session state management.",
        instruction="""
    You are a code review orchestrator that coordinates specialized analysis.
    
    Your primary responsibility is to analyze code review requests and delegate to appropriate specialist agents.
    
    You have specialized sub-agents:
    - 'code_quality_agent': Handles code quality and maintainability analysis
    
    When you receive a code review request:
    - If it's a code quality or maintainability request, delegate to 'code_quality_agent'
    - For general code review requests, delegate to the most appropriate specialist
    - Do not try to analyze code directly - always delegate to sub-agents
    - Synthesize results from sub-agents into comprehensive recommendations
    
    Maintain conversation context and user preferences across interactions.
    """,
        sub_agents=sub_agents,
        output_key="orchestrator_analysis_result"  # Auto-save final response to session state
    )

# Synchronous version for module-level initialization
def create_orchestrator_agent_sync():
    """Create orchestrator agent with dynamic model from ModelService (synchronous)"""
    orchestrator_model = get_orchestrator_model_sync()
    sub_agents = get_sub_agents_list_sync()  # Use sync version
    return Agent(
        name="code_review_orchestrator",
        model=orchestrator_model,
        description="Code review orchestrator that coordinates specialized analysis agents with ModelService integration and session state management.",
        instruction="""
    You are a code review orchestrator that coordinates specialized analysis.
    
    Your primary responsibility is to analyze code review requests and delegate to appropriate specialist agents.
    
    You have specialized sub-agents:
    - 'code_quality_agent': Handles code quality and maintainability analysis
    
    When you receive a code review request:
    - If it's a code quality or maintainability request, delegate to 'code_quality_agent'
    - For general code review requests, delegate to the most appropriate specialist
    - Do not try to analyze code directly - always delegate to sub-agents
    - Synthesize results from sub-agents into comprehensive recommendations
    
    Maintain conversation context and user preferences across interactions.
    """,
        sub_agents=sub_agents,
        output_key="orchestrator_analysis_result"  # Auto-save final response to session state
    )

# Initialize the agent (will be created dynamically)
agent = None

# ADK Runner execution pattern with ModelService integration
async def execute_code_review_analysis(user_query: str, user_id: str = "default_user"):
    """
    Execute code review analysis using ADK patterns with ModelService integration.
    Demonstrates proper integration of ModelService with ADK agents.
    
    Args:
        user_query: The code review request from user
        user_id: User identifier for session management
        
    Returns:
        Analysis result from orchestrator with model information
    """
    # Create orchestrator agent with dynamic model from ModelService
    orchestrator_agent = await create_orchestrator_agent()
    orchestrator_model = orchestrator_agent.model
    
    print(f"🤖 Orchestrator using model: {orchestrator_model}")
    
    # Create ADK SessionService (following tutorial pattern)
    session_service = InMemorySessionService()
    
    # Create session with initial state including model info
    import uuid
    session_id = str(uuid.uuid4())
    
    session = await session_service.create_session(
        app_name="agentic_code_review_system",
        user_id=user_id,
        session_id=session_id,
        state={
            "analysis_progress": "initialized",
            "completed_agents": [],
            "review_focus": ["quality", "security", "practices"],
            "orchestrator_model": str(orchestrator_model),
            "model_service_status": "active",
            "user_preferences": {
                "detail_level": "comprehensive",
                "include_examples": True
            }
        }
    )
    
    # Create Runner with proper SessionService integration
    runner = Runner(
        agent=orchestrator_agent,  # Use the dynamically created orchestrator agent
        app_name="agentic_code_review_system",
        session_service=session_service
    )
    
    # Prepare user message in ADK format
    content = types.Content(
        role='user',
        parts=[types.Part(text=user_query)]
    )
    
    # Execute agent using ADK Runner pattern
    final_response = "Agent did not produce a final response."
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_response = f"Agent escalated: {event.error_message or 'Analysis escalated.'}"
            break
    
    return {
        "response": final_response,
        "session_id": session_id,
        "user_id": user_id,
        "model_used": str(orchestrator_model),
        "model_service_active": True
    }

# For module-level export, we need a synchronous version
# This is used by ADK discovery system
def get_default_agent():
    """Get default orchestrator agent (synchronous wrapper)"""
    return create_orchestrator_agent_sync()

# Create the default agent instance for backwards compatibility
agent = get_default_agent()

# Export the agent creation function and execution function for ADK discovery
__all__ = ["create_orchestrator_agent", "execute_code_review_analysis", "agent"]