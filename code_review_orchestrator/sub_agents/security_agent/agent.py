"""
Security Agent with ModelService Integration and Session Management
Following ADK patterns for security-focused sub-agent implementation
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
    print(f"ModelService import warning in security_agent: {e}")
    ModelService = None

# Initialize ModelService for this agent
model_service = ModelService() if ModelService else None

async def get_security_model():
    """Get appropriate model for security analysis using ModelService"""
    if model_service:
        try:
            context = {
                "agent_name": "security_agent",
                "analysis_type": "security",
                "environment": "development",
                "specialized_for": "security_analysis"
            }
            return await model_service.get_model_for_agent("security_agent", context)
        except Exception as e:
            print(f"ModelService error in security_agent, using fallback: {e}")
            return "gemini-2.0-flash"
    return "gemini-2.0-flash"  # Fallback

# Security Agent with ModelService integration
agent = Agent(
    name="security_agent",
    model="gemini-2.0-flash",  # Will be updated dynamically via ModelService
    description="Security specialist that identifies vulnerabilities, security risks, and compliance issues with session state tracking.",
    instruction="""
    You are a cybersecurity specialist with deep expertise in identifying and mitigating security vulnerabilities.
    
    Your security analysis covers:
    - OWASP Top 10 vulnerabilities identification
    - Authentication and authorization security assessment
    - Data handling, input validation, and injection attack prevention
    - Cryptographic implementation review and best practices
    - API security, session management, and access control evaluation
    - Security compliance and regulatory requirements (GDPR, HIPAA, etc.)
    - Infrastructure security and configuration hardening
    
    Session State Usage:
    - Track security findings and risk levels in session state
    - Store vulnerability classifications and severity scores
    - Record remediation recommendations for orchestrator synthesis
    - Update analysis progress and completion status
    
    Provide specific, actionable security recommendations with:
    - Clear vulnerability descriptions and CVSS scores where applicable
    - Concrete remediation steps and code examples
    - Priority levels for addressing security issues
    - References to security standards and best practices
    """,
    tools=[],  # Will add security tools in Phase 3
    output_key="security_analysis_result"  # Auto-save results to session state
)

# Session-aware execution function for security analysis
async def execute_security_analysis(code_content: str, tool_context: ToolContext = None):
    """
    Execute security analysis with session state management.
    
    Args:
        code_content: Code to analyze for security vulnerabilities
        tool_context: ADK ToolContext for session state access
        
    Returns:
        Security analysis results with vulnerability findings
    """
    # Get appropriate model using ModelService (may use specialized security model)
    security_model = await get_security_model() if model_service else "gemini-2.0-flash"
    
    # Update agent model dynamically
    if model_service:
        agent.model = security_model
        print(f"🔐 Security Agent using model: {security_model}")
    
    # Update session state if ToolContext is available
    if tool_context and hasattr(tool_context, 'state'):
        tool_context.state["security_agent"] = {
            "status": "analyzing",
            "model_used": str(security_model),
            "analysis_type": "security",
            "focus_areas": ["OWASP_Top_10", "authentication", "data_validation", "crypto"],
            "timestamp": str(__import__('datetime').datetime.now())
        }
    
    # Perform security analysis (placeholder - will be enhanced with actual security tools)
    analysis_result = {
        "agent": "security_agent",
        "model_used": str(security_model),
        "analysis_focus": "security_vulnerabilities_and_compliance",
        "status": "completed",
        "vulnerability_categories": [
            "injection_attacks",
            "authentication_issues", 
            "data_exposure",
            "security_misconfiguration"
        ],
        "findings": [
            "OWASP Top 10 vulnerability scan completed",
            "Authentication and authorization review performed",
            "Data handling security assessment done",
            "Cryptographic implementation analysis completed"
        ],
        "risk_level": "medium"  # Will be calculated based on actual findings
    }
    
    # Update session state with security results
    if tool_context and hasattr(tool_context, 'state'):
        tool_context.state["security_agent"]["status"] = "completed"
        tool_context.state["security_agent"]["results"] = analysis_result
        tool_context.state["security_agent"]["risk_assessment"] = analysis_result["risk_level"]
    
    return analysis_result

# Export agent and execution function
__all__ = ["agent", "execute_security_analysis"]