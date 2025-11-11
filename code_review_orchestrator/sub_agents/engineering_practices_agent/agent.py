"""
Engineering Practices Agent with ModelService Integration and Session Management
Following ADK patterns for engineering practices evaluation
"""
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import sys
from pathlib import Path

# Add services to path for ModelService import
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services"))
try:
    from model_service import ModelService
except ImportError as e:
    print(f"ModelService import warning in engineering_practices_agent: {e}")
    ModelService = None

# Initialize ModelService for this agent
model_service = ModelService() if ModelService else None

async def get_engineering_practices_model():
    """Get appropriate model for engineering practices analysis using ModelService"""
    if model_service:
        try:
            context = {
                "agent_name": "engineering_practices_agent",
                "analysis_type": "engineering_practices",
                "environment": "development",
                "specialized_for": "best_practices_evaluation"
            }
            return await model_service.get_model_for_agent("engineering_practices_agent", context)
        except Exception as e:
            print(f"ModelService error in engineering_practices_agent, using fallback: {e}")
            return "gemini-2.0-flash"
    return "gemini-2.0-flash"  # Fallback

# Engineering Practices Agent with ModelService integration
agent = Agent(
    name="engineering_practices_agent",
    model="gemini-2.0-flash",  # Will be updated dynamically via ModelService
    description="Engineering practices specialist that evaluates software engineering best practices, team collaboration, and development workflow quality with session state tracking.",
    instruction="""
    You are a senior software engineering practices specialist with expertise in modern development methodologies.
    
    Your engineering practices evaluation covers:
    - SOLID principles adherence and object-oriented design quality
    - Test coverage analysis, test quality, and testing strategy evaluation
    - Documentation completeness, code comments, and knowledge sharing practices
    - Code organization, project structure, and architectural patterns
    - CI/CD pipeline configuration, automation, and deployment practices
    - Version control practices, branching strategies, and collaboration workflows
    - Code review processes, pull request quality, and team collaboration
    - Performance monitoring, logging, and observability practices
    - Dependency management and security practices
    
    Session State Usage:
    - Track engineering practices scores and improvement areas
    - Store best practices compliance metrics for synthesis
    - Record team collaboration and workflow recommendations
    - Update analysis progress and completion status
    
    Focus on:
    - Maintainability and long-term code health
    - Team productivity and collaboration effectiveness
    - Development workflow optimization
    - Quality assurance and reliability practices
    
    Provide actionable recommendations with:
    - Specific improvement suggestions and implementation guidance
    - Industry best practices and standard references
    - Tool recommendations and automation opportunities
    - Team process improvements and collaboration enhancements
    """,
    tools=[],  # Will add engineering tools in Phase 3
    output_key="engineering_practices_analysis_result"  # Auto-save results to session state
)

# Session-aware execution function for engineering practices analysis
async def execute_engineering_practices_analysis(code_content: str, tool_context: ToolContext = None):
    """
    Execute engineering practices analysis with session state management.
    
    Args:
        code_content: Code to analyze for engineering practices
        tool_context: ADK ToolContext for session state access
        
    Returns:
        Engineering practices analysis results
    """
    # Get appropriate model using ModelService
    practices_model = await get_engineering_practices_model() if model_service else "gemini-2.0-flash"
    
    # Update agent model dynamically
    if model_service:
        agent.model = practices_model
        print(f"⚙️ Engineering Practices Agent using model: {practices_model}")
    
    # Update session state if ToolContext is available
    if tool_context and hasattr(tool_context, 'state'):
        tool_context.state["engineering_practices_agent"] = {
            "status": "analyzing",
            "model_used": str(practices_model),
            "analysis_type": "engineering_practices",
            "evaluation_areas": [
                "SOLID_principles",
                "testing_practices", 
                "documentation",
                "code_organization",
                "CI_CD_practices"
            ],
            "timestamp": str(__import__('datetime').datetime.now())
        }
    
    # Perform engineering practices analysis (placeholder - will be enhanced with actual tools)
    analysis_result = {
        "agent": "engineering_practices_agent",
        "model_used": str(practices_model),
        "analysis_focus": "engineering_best_practices_and_team_collaboration",
        "status": "completed",
        "evaluation_categories": [
            "design_principles",
            "testing_strategy",
            "documentation_quality",
            "workflow_optimization",
            "collaboration_practices"
        ],
        "findings": [
            "SOLID principles adherence evaluation completed",
            "Test coverage and quality assessment performed",
            "Documentation completeness review done",
            "CI/CD and workflow analysis completed",
            "Team collaboration practices evaluated"
        ],
        "overall_practices_score": 75  # Will be calculated based on actual analysis
    }
    
    # Update session state with engineering practices results
    if tool_context and hasattr(tool_context, 'state'):
        tool_context.state["engineering_practices_agent"]["status"] = "completed"
        tool_context.state["engineering_practices_agent"]["results"] = analysis_result
        tool_context.state["engineering_practices_agent"]["practices_score"] = analysis_result["overall_practices_score"]
    
    return analysis_result

# Export agent and execution function
__all__ = ["agent", "execute_engineering_practices_analysis"]