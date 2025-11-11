#!/bin/bash
# ADK Development Environment Startup Script
# Initializes and starts the AI Code Review Multi-Agent system with Google ADK integration

set -euo pipefail

# Color output functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
export ADK_WORKSPACE=${ADK_WORKSPACE:-/app/adk-workspace}
export ADK_DEV_PORTAL_HOST=${ADK_DEV_PORTAL_HOST:-0.0.0.0}
export ADK_DEV_PORTAL_PORT=${ADK_DEV_PORTAL_PORT:-8200}
export API_HOST=${API_HOST:-0.0.0.0}
export API_PORT=${API_PORT:-8000}
export ENVIRONMENT=${ENVIRONMENT:-development}
export DEBUG=${DEBUG:-true}

log_info "Starting AI Code Review Multi-Agent System with Google ADK Integration"
log_info "Environment: $ENVIRONMENT"
log_info "Debug Mode: $DEBUG"
log_info "ADK Workspace: $ADK_WORKSPACE"
log_info "API Port: $API_PORT"
log_info "ADK Dev Portal Port: $ADK_DEV_PORTAL_PORT"

# Create necessary directories
log_info "Creating required directories..."
mkdir -p "$ADK_WORKSPACE"
mkdir -p /app/logs
mkdir -p /app/outputs
mkdir -p /app/data
mkdir -p /app/credentials

# Initialize ADK workspace if not exists
if [ ! -f "$ADK_WORKSPACE/.initialized" ]; then
    log_info "Initializing ADK workspace..."
    cd "$ADK_WORKSPACE"
    
    # Create ADK workspace structure
    mkdir -p agents sessions tools workflows reports
    mkdir -p config/{agents,environments,llm,rules,integrations}
    mkdir -p data/{cache,memory,knowledge_base}
    mkdir -p logs/{agents,sessions,tools,workflows}
    
    # Mark as initialized
    touch .initialized
    echo "$(date -Iseconds)" > .initialization_date
    log_success "ADK workspace initialized"
else
    log_info "ADK workspace already initialized"
fi

# Google Cloud authentication setup
if [ -f "/app/credentials/google-cloud-credentials.json" ]; then
    log_info "Setting up Google Cloud authentication..."
    export GOOGLE_APPLICATION_CREDENTIALS="/app/credentials/google-cloud-credentials.json"
    
    # Activate service account
    if command -v gcloud &> /dev/null; then
        gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS" --quiet
        log_success "Google Cloud authentication configured"
    else
        log_warning "gcloud CLI not available, skipping service account activation"
    fi
else
    log_warning "Google Cloud credentials not found at /app/credentials/google-cloud-credentials.json"
    log_warning "Some features may not work without proper authentication"
fi

# Wait for dependencies (optional - external services)
log_info "Checking for dependencies..."

# Note: Redis and other external services are handled separately
# This container focuses on the core ADK application

# Validate Python environment
log_info "Validating Python environment..."
python_version=$(python --version 2>&1 | cut -d' ' -f2)
log_info "Python version: $python_version"

# Check critical packages
log_info "Checking critical packages..."

# Core packages
if python -c "import pydantic" 2>/dev/null; then
    log_success "pydantic is available"
else
    log_error "pydantic is not available"
fi

if python -c "import structlog" 2>/dev/null; then
    log_success "structlog is available"
else
    log_error "structlog is not available"
fi

if python -c "import fastapi" 2>/dev/null; then
    log_success "fastapi is available"
else
    log_error "fastapi is not available"
fi

# Google ADK (proper import check)
if python -c "import google.adk.core" 2>/dev/null; then
    log_success "google-adk is available"
elif python -c "import google.adk" 2>/dev/null; then
    log_success "google-adk is available"
else
    log_warning "google-adk is not properly configured (may need authentication)"
fi

# Tree-sitter (proper import check)
if python -c "import tree_sitter" 2>/dev/null; then
    log_success "tree-sitter is available"
else
    log_warning "tree-sitter is not properly configured"
fi

# Start services based on environment
if [ "$ENVIRONMENT" = "development" ]; then
    log_info "Starting development services..."
    
    # Start ADK Dev Portal in background
    log_info "Starting ADK Development Portal on port $ADK_DEV_PORTAL_PORT..."
    cd /app
    python infra/scripts/adk-dev-portal.py \
        --host "$ADK_DEV_PORTAL_HOST" \
        --port "$ADK_DEV_PORTAL_PORT" \
        --workspace "$ADK_WORKSPACE" \
        --reload &
    
    ADK_PORTAL_PID=$!
    log_success "ADK Development Portal started (PID: $ADK_PORTAL_PID)"
    
    # Wait a moment for the portal to start
    sleep 2
    
    # Start main API with hot reload
    log_info "Starting main API on port $API_PORT..."
    exec python -m uvicorn src.api.main:app \
        --host "$API_HOST" \
        --port "$API_PORT" \
        --reload \
        --reload-dir /app/src \
        --log-level info
else
    # Production mode
    log_info "Starting production services..."
    
    # Start ADK Dev Portal in background
    log_info "Starting ADK Development Portal on port $ADK_DEV_PORTAL_PORT..."
    cd /app
    python infra/scripts/adk-dev-portal.py \
        --host "$ADK_DEV_PORTAL_HOST" \
        --port "$ADK_DEV_PORTAL_PORT" \
        --workspace "$ADK_WORKSPACE" &
    
    ADK_PORTAL_PID=$!
    log_success "ADK Development Portal started (PID: $ADK_PORTAL_PID)"
    
    # Start main API
    log_info "Starting main API on port $API_PORT..."
    exec python -m uvicorn src.api.main:app \
        --host "$API_HOST" \
        --port "$API_PORT" \
        --workers 4 \
        --log-level info
fi