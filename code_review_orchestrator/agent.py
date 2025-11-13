"""
ADK-Compliant Code Review Orchestrator Agent
Following Google ADK tutorial patterns with ModelService integration
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from services.model_service import ModelService


load_dotenv()

# Add project root to Python path for absolute imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


OLLAMA_API_BASE = os.environ["OLLAMA_API_BASE"]
LLM_ENDPOINT = f"{OLLAMA_API_BASE}/api/generate"
LLM_MODEL = os.environ["OLLAMA_MODEL"]

# Import sub-agent
from .sub_agents.code_quality_agent.agent import code_quality_agent

sub_agents = [code_quality_agent]

agent_model = LiteLlm(model=LLM_MODEL, endpoint=LLM_ENDPOINT)

system_prompt = """
    You are a code review orchestrator that coordinates specialized analysis through sub-agents.
    
    Your primary responsibility is to manage code review requests and delegate to appropriate specialists.
    
    You have access to specialized sub-agents:
    - 'code_quality_agent': Handles code quality, maintainability, and technical analysis
    
    When you receive user input:
    1. If it's a simple greeting like "hello" or general question, respond directly WITHOUT transferring
    2. If the user provides actual CODE for review, then delegate to 'code_quality_agent'
    3. If the user asks about capabilities, explain your services directly
    4. Only transfer when you have actual code content to analyze
    
    For greetings and general questions:
    - Respond directly and warmly without any agent transfers
    - Explain what kind of code review help you can provide
    - Be conversational and friendly
    - Ask for code to review if they want analysis
    
    For code analysis:
    - Only transfer to code_quality_agent when you have actual code content
    - Wait for sub-agent results before responding to user
    - Synthesize sub-agent findings into comprehensive recommendations
    
    Session State Usage:
    - Track overall review progress and coordination status
    - Store user preferences and conversation context
    - Aggregate results from sub-agents for comprehensive reporting
    - Maintain conversation history and analysis outcomes
    
    CRITICAL: Do NOT transfer for greetings, questions, or general conversation.
    Only transfer when you have actual code to analyze.
    """

tools_list=[]  # Tools are handled by sub-agents
    
# Create the root code review agent
code_review_orchestrator_agent = None

try:
    code_review_orchestrator_agent = Agent(
        name="code_review_orchestrator",
        description="Code review orchestrator that coordinates specialized analysis agents with ModelService integration and session state management.",
        model=agent_model,
        instruction=system_prompt,
        sub_agents=sub_agents,
        tools=tools_list,
        output_key="orchestrator_analysis_result",  # Auto-save final response to session state
    )
except Exception as e:
    print(f"❌ Error initializing code_review_orchestrator_agent: {e}", file=sys.stderr)
    sys.exit(1)

