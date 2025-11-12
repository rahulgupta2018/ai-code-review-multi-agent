"""
Code Quality Agent with ModelService Integration and Session Management
Following ADK patterns for sub-agent implementation
"""

import sys
import os

from pathlib import Path
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

# Add project root to Python path for absolute imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.model_service import ModelService
from tools.complexity_analyzer_tool import analyze_code_complexity
from tools.static_analyzer_tool import analyze_static_code
from tools.tree_sitter_tool import parse_code_ast

load_dotenv()

# Initialize ModelService for this agent
model_service = ModelService()

OLLAMA_API_BASE = os.environ["OLLAMA_API_BASE"]
LLM_ENDPOINT = f"{OLLAMA_API_BASE}/api/generate"
LLM_MODEL = os.environ["OLLAMA_MODEL"]
agent_model = LiteLlm(model=LLM_MODEL, endpoint=LLM_ENDPOINT)
tools_list=[analyze_code_complexity, analyze_static_code, parse_code_ast]

system_prompt = """
        You are a code quality specialist with access to session state for tracking analysis progress.
        
        Your expertise covers:
        - Code complexity analysis and cyclomatic complexity assessment
        - Code maintainability and readability evaluation
        - Coding best practices and style guide compliance
        - Code structure, organization, and architectural patterns
        - Technical debt identification and recommendations
        
        Important: You should only be invoked when there is actual code to analyze.
        If you receive a simple greeting or non-code request, politely redirect back to the orchestrator.
        
        Session State Usage:
        - Track your analysis progress in session state
        - Store identified issues for cross-agent synthesis
        - Record complexity metrics and quality scores
        - Update completion status when analysis is done
        
        Use available tools for detailed technical analysis when you have code to review.
        Provide specific, actionable recommendations with code examples where helpful.
        
        Do not transfer back to other agents unless specifically needed for your analysis.
        """

code_quality_agent = None

try:
    code_quality_agent = Agent(
        name="code_quality_agent",
        model=agent_model,
        description="Code quality specialist that analyzes code quality, maintainability, and best practices with session state tracking.",
        instruction=system_prompt,
        tools=tools_list,  
        output_key="code_quality_analysis_result",  # Auto-save results to session state
    )
except Exception as e:
    print(f"❌ Error initializing code_quality_agent: {e}", file=sys.stderr)
    sys.exit(1)


