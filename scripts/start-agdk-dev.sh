#!/bin/bash
# AGDK Development Environment Startup Script
# This script initializes the AGDK development environment with all necessary services

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Function to check if Google Cloud credentials are available
check_gcloud_credentials() {
    log_info "Checking Google Cloud credentials..."
    
    if [[ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]] && [[ -f "${GOOGLE_APPLICATION_CREDENTIALS}" ]]; then
        log_success "Google Cloud credentials file found: ${GOOGLE_APPLICATION_CREDENTIALS}"
        return 0
    elif gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
        log_success "Google Cloud authenticated via gcloud CLI"
        return 0
    else
        log_warning "No Google Cloud credentials found. AGDK features will be limited."
        return 1
    fi
}

# Function to initialize AGDK workspace
initialize_agdk_workspace() {
    log_info "Initializing AGDK workspace..."
    
    # Create workspace directories
    mkdir -p "${AGDK_WORKSPACE}/sessions"
    mkdir -p "${AGDK_WORKSPACE}/tools"
    mkdir -p "${AGDK_WORKSPACE}/logs"
    mkdir -p "${AGDK_WORKSPACE}/cache"
    
    # Set permissions
    chmod 755 "${AGDK_WORKSPACE}"
    chmod 755 "${AGDK_WORKSPACE}/sessions"
    chmod 755 "${AGDK_WORKSPACE}/tools"
    chmod 755 "${AGDK_WORKSPACE}/logs"
    chmod 755 "${AGDK_WORKSPACE}/cache"
    
    log_success "AGDK workspace initialized at ${AGDK_WORKSPACE}"
}

# Function to start AGDK dev portal
start_agdk_dev_portal() {
    log_info "Starting AGDK development portal..."
    
    # Check if dev portal is available
    if command -v agdk >/dev/null 2>&1; then
        log_info "Starting AGDK dev portal on port ${AGDK_DEV_PORTAL_PORT}..."
        
        # Start dev portal in background
        nohup agdk dev-portal start \
            --port "${AGDK_DEV_PORTAL_PORT}" \
            --workspace "${AGDK_WORKSPACE}" \
            --log-level "${AGDK_LOG_LEVEL}" \
            > "${AGDK_WORKSPACE}/logs/dev-portal.log" 2>&1 &
        
        echo $! > "${AGDK_WORKSPACE}/dev-portal.pid"
        
        # Wait for portal to start
        sleep 5
        
        if kill -0 $(cat "${AGDK_WORKSPACE}/dev-portal.pid" 2>/dev/null) 2>/dev/null; then
            log_success "AGDK dev portal started successfully on port ${AGDK_DEV_PORTAL_PORT}"
        else
            log_error "Failed to start AGDK dev portal"
            return 1
        fi
    else
        log_warning "AGDK CLI not available. Dev portal will not be started."
        return 1
    fi
}

# Function to verify Python environment
verify_python_environment() {
    log_info "Verifying Python environment..."
    
    # Check Python version
    python_version=$(python --version 2>&1 | cut -d' ' -f2)
    log_info "Python version: ${python_version}"
    
    # Check required packages
    required_packages=(
        "google-cloud-aiplatform"
        "google-cloud-discoveryengine"
        "google-cloud-dialogflow"
        "google-auth"
    )
    
    for package in "${required_packages[@]}"; do
        if python -c "import ${package//-/_}" 2>/dev/null; then
            log_success "Package ${package} is available"
        else
            log_error "Package ${package} is not available"
            return 1
        fi
    done
    
    log_success "Python environment verified"
}

# Function to run AGDK integration tests
run_agdk_tests() {
    log_info "Running AGDK integration tests..."
    
    if [[ -f "/app/test_baseagent_agdk_integration.py" ]]; then
        if python /app/test_baseagent_agdk_integration.py; then
            log_success "AGDK integration tests passed"
        else
            log_warning "AGDK integration tests failed (this might be expected without full Google Cloud setup)"
        fi
    else
        log_info "AGDK integration tests not found, skipping..."
    fi
}

# Function to display environment information
display_environment_info() {
    log_info "AGDK Development Environment Information:"
    echo "================================================"
    echo "Workspace: ${AGDK_WORKSPACE}"
    echo "Dev Portal Port: ${AGDK_DEV_PORTAL_PORT}"
    echo "Log Level: ${AGDK_LOG_LEVEL}"
    echo "Google Cloud Project: ${GOOGLE_CLOUD_PROJECT_ID:-Not set}"
    echo "Google Cloud Location: ${GOOGLE_CLOUD_LOCATION:-Not set}"
    echo "Python Version: $(python --version)"
    echo "AGDK CLI: $(command -v agdk >/dev/null 2>&1 && echo 'Available' || echo 'Not available')"
    echo "================================================"
}

# Function to start Jupyter Lab for development
start_jupyter_lab() {
    log_info "Starting Jupyter Lab for AGDK development..."
    
    if command -v jupyter >/dev/null 2>&1; then
        nohup jupyter lab \
            --ip=0.0.0.0 \
            --port=8888 \
            --no-browser \
            --allow-root \
            --notebook-dir="${AGDK_WORKSPACE}" \
            > "${AGDK_WORKSPACE}/logs/jupyter.log" 2>&1 &
        
        echo $! > "${AGDK_WORKSPACE}/jupyter.pid"
        log_success "Jupyter Lab started on port 8888"
    else
        log_warning "Jupyter Lab not available"
    fi
}

# Function to cleanup on exit
cleanup() {
    log_info "Cleaning up AGDK development environment..."
    
    # Stop dev portal
    if [[ -f "${AGDK_WORKSPACE}/dev-portal.pid" ]]; then
        if kill $(cat "${AGDK_WORKSPACE}/dev-portal.pid") 2>/dev/null; then
            log_info "AGDK dev portal stopped"
        fi
        rm -f "${AGDK_WORKSPACE}/dev-portal.pid"
    fi
    
    # Stop Jupyter Lab
    if [[ -f "${AGDK_WORKSPACE}/jupyter.pid" ]]; then
        if kill $(cat "${AGDK_WORKSPACE}/jupyter.pid") 2>/dev/null; then
            log_info "Jupyter Lab stopped"
        fi
        rm -f "${AGDK_WORKSPACE}/jupyter.pid"
    fi
}

# Set up signal handlers for cleanup
trap cleanup EXIT INT TERM

# Main execution
main() {
    log_info "Starting AGDK Development Environment..."
    
    # Display environment information
    display_environment_info
    
    # Check credentials
    check_gcloud_credentials || true
    
    # Verify Python environment
    verify_python_environment
    
    # Initialize workspace
    initialize_agdk_workspace
    
    # Start services
    start_agdk_dev_portal || true
    start_jupyter_lab || true
    
    # Run tests
    run_agdk_tests
    
    log_success "AGDK Development Environment is ready!"
    log_info "Access points:"
    log_info "  - API Server: http://localhost:8000"
    log_info "  - AGDK Dev Portal: http://localhost:${AGDK_DEV_PORTAL_PORT}"
    log_info "  - Jupyter Lab: http://localhost:8888"
    
    # Keep container running
    log_info "Environment is running. Press Ctrl+C to stop."
    
    # Start the main application
    if [[ "${1:-}" == "--api-only" ]]; then
        log_info "Starting API server only..."
        exec python -m src.api.main
    else
        log_info "Starting full development environment..."
        # Keep container alive
        while true; do
            sleep 30
            # Check if services are still running
            if [[ -f "${AGDK_WORKSPACE}/dev-portal.pid" ]] && ! kill -0 $(cat "${AGDK_WORKSPACE}/dev-portal.pid") 2>/dev/null; then
                log_warning "AGDK dev portal stopped unexpectedly"
            fi
        done
    fi
}

# Execute main function with all arguments
main "$@"