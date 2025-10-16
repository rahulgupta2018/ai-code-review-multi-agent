"""
FastAPI Main Application for AI Code Review Multi-Agent System
"""

from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any
import logging
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import core modules
from core.config import get_settings
from core.exceptions import ADKError, ValidationError, ConfigurationError
from api.middleware import SecurityMiddleware, LoggingMiddleware
from api.v1.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="AI Code Review Multi-Agent System",
        description="Production-ready ADK Multi-Agent Code Review MVP",
        version="1.0.0",
        debug=settings.debug,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["https://localhost", "https://127.0.0.1"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
        )
    
    # Add custom middleware
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    return app

# Create the FastAPI app
app = create_application()

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "message": "AI Code Review Multi-Agent System API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    try:
        settings = get_settings()
        return {
            "status": "healthy",
            "environment": settings.environment,
            "debug": settings.debug,
            "timestamp": "2025-01-14T20:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.exception_handler(ADKError)
async def adk_exception_handler(request: Request, exc: ADKError) -> JSONResponse:
    """Handle ADK-specific exceptions."""
    logger.error(f"ADK Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "ADK Error",
            "message": str(exc),
            "type": "adk_error"
        }
    )

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation exceptions."""
    logger.warning(f"Validation Exception: {exc}")
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "message": str(exc),
            "type": "validation_error"
        }
    )

@app.exception_handler(ConfigurationError)
async def config_exception_handler(request: Request, exc: ConfigurationError) -> JSONResponse:
    """Handle configuration exceptions."""
    logger.error(f"Configuration Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Configuration Error",
            "message": str(exc),
            "type": "configuration_error"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "type": "general_error"
        }
    )

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )