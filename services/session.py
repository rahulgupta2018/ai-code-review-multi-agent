"""
ADK-Compliant Session Management
Implements proper Google ADK SessionService patterns for code review system
"""
from typing import Dict, Any, Optional
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import logging

# Configure logging
logger = logging.getLogger(__name__)

class CodeReviewSessionService:
    """
    ADK-compliant session service for code review orchestration.
    Follows Google ADK tutorial patterns from: https://google.github.io/adk-docs/tutorials/agent-team/
    """
    
    def __init__(self):
        # Use ADK's proper SessionService
        self.session_service = InMemorySessionService()
        
        # ADK session configuration constants
        self.APP_NAME = "agentic_code_review_system"
        
        logger.info("ADK CodeReviewSessionService initialized")
        
    async def create_session(self, 
                           user_id: str, 
                           session_id: Optional[str] = None,
                           initial_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create ADK session following proper patterns.
        
        Args:
            user_id: User identifier for session
            session_id: Optional session ID, will generate if not provided
            initial_state: Optional initial session state
            
        Returns:
            Dict containing session information
        """
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            
        # Set default initial state for code review
        if initial_state is None:
            initial_state = {
                "analysis_results": {},
                "current_step": "initialized",
                "agent_progress": {},
                "review_preferences": {
                    "focus_areas": ["quality", "security", "practices"],
                    "detail_level": "comprehensive"
                }
            }
            
        try:
            # Create session using ADK SessionService pattern
            session = await self.session_service.create_session(
                app_name=self.APP_NAME,
                user_id=user_id,
                session_id=session_id,
                state=initial_state
            )
            
            logger.info(f"ADK Session created: App='{self.APP_NAME}', User='{user_id}', Session='{session_id}'")
            
            return {
                "session_id": session_id,
                "user_id": user_id,
                "app_name": self.APP_NAME,
                "state": initial_state,
                "created": True
            }
            
        except Exception as e:
            logger.error(f"Failed to create ADK session: {e}")
            raise
    
    async def get_session(self, user_id: str, session_id: str) -> Optional[Any]:
        """
        Get ADK session using proper SessionService patterns.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Session object or None if not found
        """
        try:
            session = await self.session_service.get_session(
                app_name=self.APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
            
            if session:
                logger.debug(f"Retrieved ADK session: {session_id}")
            else:
                logger.warning(f"ADK session not found: {session_id}")
                
            return session
            
        except Exception as e:
            logger.error(f"Failed to get ADK session {session_id}: {e}")
            return None
    
    async def update_session_state(self, user_id: str, session_id: str, 
                                 key: str, value: Any) -> bool:
        """
        Update session state via ADK patterns.
        Note: In production, state updates typically happen via ToolContext.state
        
        Args:
            user_id: User identifier
            session_id: Session identifier  
            key: State key to update
            value: New value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = await self.get_session(user_id, session_id)
            if not session:
                logger.error(f"Cannot update state - session not found: {session_id}")
                return False
                
            # Update state (this is manual - normally done via ToolContext)
            if hasattr(session, 'state'):
                session.state[key] = value
                logger.debug(f"Updated session state: {key} = {value}")
                return True
            else:
                logger.error("Session object missing state attribute")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update session state: {e}")
            return False
    
    def create_runner(self, agent, user_id: Optional[str] = None) -> Runner:
        """
        Create ADK Runner with proper SessionService integration.
        
        Args:
            agent: ADK Agent instance
            user_id: Optional user ID for runner context
            
        Returns:
            Configured ADK Runner
        """
        try:
            runner = Runner(
                agent=agent,
                app_name=self.APP_NAME,
                session_service=self.session_service
            )
            
            logger.info(f"Created ADK Runner for agent '{agent.name}'")
            return runner
            
        except Exception as e:
            logger.error(f"Failed to create ADK Runner: {e}")
            raise
    
    async def call_agent_async(self, query: str, runner: Runner, 
                             user_id: str, session_id: str) -> str:
        """
        Call agent using ADK Runner patterns from tutorial.
        
        Args:
            query: User query/request
            runner: ADK Runner instance
            user_id: User identifier  
            session_id: Session identifier
            
        Returns:
            Agent's final response text
        """
        try:
            logger.info(f"Agent Query: {query}")
            
            # Prepare message in ADK format
            content = types.Content(
                role='user', 
                parts=[types.Part(text=query)]
            )
            
            final_response_text = "Agent did not produce a final response."
            
            # Execute agent using ADK Runner pattern
            async for event in runner.run_async(
                user_id=user_id, 
                session_id=session_id, 
                new_message=content
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_response_text = event.content.parts[0].text
                    elif event.actions and event.actions.escalate:
                        final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                    break
            
            logger.info(f"Agent Response: {final_response_text}")
            return final_response_text
            
        except Exception as e:
            logger.error(f"Failed to call agent: {e}")
            return f"Error calling agent: {str(e)}"
