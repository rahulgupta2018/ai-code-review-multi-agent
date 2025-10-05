#!/bin/bash
# GADK Development Environment Startup Script
# This script initializes the GADK development environment with all necessary services

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
        log_warning "No Google Cloud credentials found. GADK features will be limited."
        return 1
    fi
}

# Function to initialize GADK workspace
initialize_gadk_workspace() {
    log_info "Initializing GADK workspace..."
    
    # Create workspace directories
    mkdir -p "${GADK_WORKSPACE}/sessions"
    mkdir -p "${GADK_WORKSPACE}/tools"
    mkdir -p "${GADK_WORKSPACE}/logs"
    mkdir -p "${GADK_WORKSPACE}/cache"
    
    # Set permissions
    chmod 755 "${GADK_WORKSPACE}"
    chmod 755 "${GADK_WORKSPACE}/sessions"
    chmod 755 "${GADK_WORKSPACE}/tools"
    chmod 755 "${GADK_WORKSPACE}/logs"
    chmod 755 "${GADK_WORKSPACE}/cache"
    
    log_success "GADK workspace initialized at ${GADK_WORKSPACE}"
}

# Function to start GADK dev portal
start_gadk_dev_portal() {
    log_info "Starting GADK development portal..."
    
    # Check if dev portal is available
    if command -v gadk >/dev/null 2>&1; then
        log_info "Starting GADK dev portal on port ${GADK_DEV_PORTAL_PORT}..."
        
        # Start dev portal in background
        nohup gadk dev-portal start \
            --port "${GADK_DEV_PORTAL_PORT}" \
            --workspace "${GADK_WORKSPACE}" \
            --log-level "${GADK_LOG_LEVEL}" \
            > "${GADK_WORKSPACE}/logs/dev-portal.log" 2>&1 &
        
        echo $! > "${GADK_WORKSPACE}/dev-portal.pid"
        
        # Wait for portal to start
        sleep 5
        
        if kill -0 $(cat "${GADK_WORKSPACE}/dev-portal.pid" 2>/dev/null) 2>/dev/null; then
            log_success "GADK dev portal started successfully on port ${GADK_DEV_PORTAL_PORT}"
        else
            log_error "Failed to start GADK dev portal"
            return 1
        fi
    else
        log_warning "GADK CLI not available. Dev portal will not be started."
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

# Function to run GADK integration tests
run_gadk_tests() {
    log_info "Running GADK integration tests..."
    
    if [[ -f "/app/test_baseagent_gadk_integration.py" ]]; then
        if python /app/test_baseagent_gadk_integration.py; then
            log_success "GADK integration tests passed"
        else
            log_warning "GADK integration tests failed (this might be expected without full Google Cloud setup)"
        fi
    else
        log_info "GADK integration tests not found, skipping..."
    fi
}

# Function to display environment information
display_environment_info() {
    log_info "GADK Development Environment Information:"
    echo "================================================"
    echo "Workspace: ${GADK_WORKSPACE}"
    echo "Dev Portal Port: ${GADK_DEV_PORTAL_PORT}"
    echo "Log Level: ${GADK_LOG_LEVEL}"
    echo "Google Cloud Project: ${GOOGLE_CLOUD_PROJECT_ID:-Not set}"
    echo "Google Cloud Location: ${GOOGLE_CLOUD_LOCATION:-Not set}"
    echo "Python Version: $(python --version)"
    echo "GADK CLI: $(command -v gadk >/dev/null 2>&1 && echo 'Available' || echo 'Not available')"
    echo "================================================"
}

# Function to cleanup on exit
cleanup() {
    log_info "Cleaning up GADK development environment..."
    
    # Stop dev portal
    if [[ -f "${GADK_WORKSPACE}/dev-portal.pid" ]]; then
        if kill $(cat "${GADK_WORKSPACE}/dev-portal.pid") 2>/dev/null; then
            log_info "GADK dev portal stopped"
        fi
        rm -f "${GADK_WORKSPACE}/dev-portal.pid"
    fi
}

# Set up signal handlers for cleanup
trap cleanup EXIT INT TERM

# Main execution
main() {
    log_info "Starting GADK Development Environment..."
    
    # Display environment information
    display_environment_info
    
    # Check credentials
    check_gcloud_credentials || true
    
    # Verify Python environment
    verify_python_environment
    
    # Initialize workspace
    initialize_gadk_workspace
    
    # Start services
    start_gadk_dev_portal || true
    
    # Run tests
    run_gadk_tests
    
    log_success "GADK Development Environment is ready!"
    log_info "Access points:"
    log_info "  - API Server: http://localhost:8000"
    log_info "  - GADK Dev Portal: http://localhost:${GADK_DEV_PORTAL_PORT}"
    
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
            if [[ -f "${GADK_WORKSPACE}/dev-portal.pid" ]] && ! kill -0 $(cat "${GADK_WORKSPACE}/dev-portal.pid") 2>/dev/null; then
                log_warning "GADK dev portal stopped unexpectedly"
            fi
        done
    fi
}

# Execute main function with all arguments
main "$@"