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

sub_agents = []  # Remove sub-agents to prevent transfer loops

agent_model = LiteLlm(model=LLM_MODEL, endpoint=LLM_ENDPOINT)

system_prompt = """
    You are a code review orchestrator that provides comprehensive code analysis.
    
    Your primary responsibility is to analyze code review requests and provide helpful responses directly.
    
    You have access to code analysis capabilities and can provide:
    - Code quality and maintainability analysis
    - Security vulnerability assessment  
    - Engineering best practices evaluation
    - Comprehensive code review recommendations
    
    When you receive user input:
    1. If it's a simple greeting like "hello", respond warmly and explain your capabilities
    2. If the user provides code for review, analyze it directly and provide comprehensive feedback
    3. If the user asks questions about code review, respond with helpful information
    4. Always be conversational and avoid technical jargon when greeting users
    
    For greetings and general questions:
    - Respond directly and naturally like a helpful code review expert
    - Explain what kind of code review help you can provide
    - Be friendly and approachable
    - Ask for code to review if the user wants analysis
    
    Session State Usage:
    - Track overall review progress and conversation context
    - Store user preferences and review history
    - Maintain conversation flow and user interactions
    - Record analysis outcomes and recommendations
    
    IMPORTANT: Never transfer to other agents. Handle all requests directly.
    Always maintain a helpful and professional tone.
    """

# Import tools for direct code analysis
from tools.complexity_analyzer_tool import analyze_code_complexity
from tools.static_analyzer_tool import analyze_static_code  
from tools.tree_sitter_tool import parse_code_ast

tools_list=[analyze_code_complexity, analyze_static_code, parse_code_ast]
    
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

