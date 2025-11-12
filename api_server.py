#!/usr/bin/env python3
"""
Web API Server for ADK Code Review System
Provides HTTP endpoints to trigger the agentic workflow pipeline
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from google.genai import types

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our orchestration logic
from services.model_service import ModelService
from utils import extract_code_from_input, validate_code_input

# Initialize FastAPI app
app = FastAPI(
    title="ADK Code Review System API",
    description="Multi-agent code review system with ADK orchestration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for ADK components
session_service = None
runner = None
model_service = None
APP_NAME = "adk-code-review-system"
USER_ID = "api-user"

# Request/Response models
class CodeReviewRequest(BaseModel):
    code: str
    language: Optional[str] = "python"
    analysis_type: Optional[str] = "quality"
    session_id: Optional[str] = None

class CodeReviewResponse(BaseModel):
    status: str
    session_id: str
    analysis_result: Dict[str, Any]
    execution_time: float
    timestamp: str

class SessionStatusResponse(BaseModel):
    session_id: str
    total_reviews: int
    total_issues: int
    analysis_history: list
    session_metadata: Dict[str, Any]

async def initialize_adk_components():
    """Initialize ADK components on startup."""
    global session_service, runner, model_service
    
    try:
        # Initialize ModelService
        model_service = ModelService()
        print("🔧 ModelService initialized for API")
        
        # Import ADK components
        from google.adk.sessions import InMemorySessionService
        from google.adk.runners import Runner
        from code_review_orchestrator.agent import code_review_orchestrator_agent
        
        # Initialize session service
        session_service = InMemorySessionService()
        print("📁 Session service initialized")
        
        # Initialize runner with orchestrator
        runner = Runner(
            agent=code_review_orchestrator_agent,
            app_name="AI Code Review System",
            session_service=session_service
        )
        print("🚀 ADK Runner initialized with orchestrator")
        
        # Create default session for API requests
        try:
            await session_service.create_session(
                app_name="AI Code Review System",
                user_id="api-user",
                session_id="api-session-default",
                state={
                    'session_metadata': {'total_reviews': 0, 'created_via': 'api'},
                    'quality_metrics': {'total_issues_found': 0, 'critical_issues': 0, 'high_issues': 0},
                    'analysis_history': []
                }
            )
            print("📋 Default API session created")
        except Exception as e:
            print(f"⚠️ Session creation warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize ADK components: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize ADK components when the API starts."""
    success = await initialize_adk_components()
    if not success:
        print("⚠️ API starting without full ADK initialization")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "ADK Code Review System API",
        "version": "1.0.0",
        "endpoints": [
            "/review - POST: Submit code for review",
            "/session/{session_id} - GET: Get session status", 
            "/health - GET: Health check",
            "/docs - GET: API documentation"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "adk_initialized": session_service is not None and runner is not None,
        "model_service": model_service is not None
    }

@app.post("/review", response_model=CodeReviewResponse)
async def review_code(request: CodeReviewRequest):
    """
    Submit code for review using the ADK multi-agent pipeline.
    """
    import time
    start_time = time.time()
    
    try:
        # Validate that ADK components are initialized
        if not session_service or not runner:
            raise HTTPException(
                status_code=503, 
                detail="ADK components not initialized"
            )
        
        # Extract and validate code
        extracted = extract_code_from_input(f"```{request.language}\n{request.code}\n```")
        
        if not extracted['code']:
            raise HTTPException(
                status_code=400,
                detail="No valid code found in request"
            )
        
        validation = validate_code_input(extracted['code'])
        if not validation.get('valid', False):
            issues = validation.get('issues', ['Unknown validation error'])
            raise HTTPException(
                status_code=400,
                detail=f"Code validation failed: {'; '.join(issues)}"
            )
        
        # Use or create a session 
        session_id = request.session_id if request.session_id else "api-session-default"
        
        # Prepare analysis request
        analysis_request = {
            'code': extracted['code'],
            'language': request.language,
            'analysis_type': request.analysis_type,
            'session_context': {
                'session_id': session_id,
                'user_id': USER_ID,
                'timestamp': time.time()
            }
        }
        
        # Run the multi-agent analysis  
        content = types.Content(role="user", parts=[types.Part(text=f"Analyze this {request.language} code:\n\n{extracted['code']}")])
        
        analysis_results = []
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session_id,
            new_message=content
        ):
            if hasattr(event, 'parts') and event.parts:
                analysis_results.append(event.parts[0].text)
        
        # Combine all analysis results
        result = "\n".join(analysis_results) if analysis_results else "Analysis completed but no detailed results available."
        
        # Note: Session state updates would be handled by the ADK runner automatically
        
        execution_time = time.time() - start_time
        
        # Format the response
        response = CodeReviewResponse(
            status="success",
            session_id=session_id,
            analysis_result={
                "agent_analysis": result,
                "code_metrics": {
                    "language": request.language,
                    "lines_of_code": len(extracted['code'].split('\n')),
                    "analysis_type": request.analysis_type
                },
                "formatted_result": result
            },
            execution_time=execution_time,
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@app.get("/session/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """Get the status and history of a specific session."""
    try:
        if not session_service:
            raise HTTPException(
                status_code=503,
                detail="Session service not initialized"
            )
        
        session = session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id
        )
        
        return SessionStatusResponse(
            session_id=session_id,
            total_reviews=session.state['session_metadata']['total_reviews'],
            total_issues=session.state['quality_metrics']['total_issues_found'],
            analysis_history=session.state['analysis_history'],
            session_metadata=session.state['session_metadata']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {str(e)}"
        )

@app.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    try:
        if not session_service:
            raise HTTPException(
                status_code=503,
                detail="Session service not initialized"
            )
        
        # This is a simplified implementation
        # In practice, you'd want to implement a proper session listing in the session service
        return {
            "message": "Session listing not fully implemented",
            "note": "Use specific session_id endpoints"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sessions: {str(e)}"
        )

if __name__ == "__main__":
    # This allows running the API server directly
    print("🌐 Starting ADK Code Review API Server...")
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )