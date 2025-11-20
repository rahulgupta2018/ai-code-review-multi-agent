"""
Intelligent input classifier agent that selects appropriate analysis sub-agents
based on the characteristics of the submitted code.

"""

import sys
import logging
from pathlib import Path
from google.adk.agents import LlmAgent

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add project root to Python path for absolute imports
# __file__ is in agent_workspace/orchestrator_agent/sub_agents/carbon_emission_agent/
# We need to go up 5 levels to reach the project root (agentic-codereview/)
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import centralized model configuration
from util.llm_model import get_sub_agent_model
from util.llm_model import get_agent_model

# Initialize services at module level so they're available for adk web/api commands


# Get the centralized model instance
logger.info("🔧 [classifier_agent] Initializing Classifier Agent")
agent_model = get_agent_model()
logger.info(f"🔧 [classifier_agent] Model configured: {agent_model}")

logger.info("🔧 [classifier_agent] Creating LlmAgent for request classification")
classifier_agent = LlmAgent(
    name="classifier_agent",
    model=agent_model,
    description="Classifies user requests to determine appropriate code analysis sub-agents",

    instruction="""You are an intelligent request classifier for a code review system.

    Analyze the user's input and classify it into one of these categories:

    1. **general_query**: User asking about system capabilities, general questions
    Examples: "What can you do?", "How does this work?", "Help me"
    
    2. **code_review_full**: User wants comprehensive analysis (all aspects)
    Examples: "Review this code", "Analyze this", "Check everything"
    
    3. **code_review_security**: User wants security-focused analysis only
    Examples: "Is this secure?", "Check for vulnerabilities", "Security review"
    
    4. **code_review_quality**: User wants code quality analysis only
    Examples: "Check code quality", "Is this maintainable?", "Complexity analysis"
    
    5. **code_review_engineering**: User wants engineering practices review only
    Examples: "SOLID principles?", "Best practices?", "Design patterns?"
    
    6. **code_review_carbon**: User wants environmental impact analysis only
    Examples: "Carbon footprint?", "Energy efficiency?", "Performance optimization?"
    
    7. **code_review_custom**: User specifies multiple specific areas
    Examples: "Check security and quality", "Review for SOLID and performance"

    Your task:
    1. Detect if code is present in the input (look for code patterns, functions, classes)
    2. Identify the request type
    3. Extract focus areas if user mentions specific aspects
    4. Return structured classification

    Output Format (JSON):
    {
    "type": "code_review_security",
    "has_code": true,
    "focus_areas": ["security", "vulnerability"],
    "confidence": "high",
    "reasoning": "User explicitly asks about security, code snippet present"
    }

    Analyze the user's message from the current conversation context and classify their request.
    """.strip(),
    input_schema=None,
    output_key="request_classification",
)

logger.info("✅ [classifier_agent] Classifier Agent created successfully")
logger.info("🔧 [classifier_agent] No tools configured - uses LLM reasoning only")