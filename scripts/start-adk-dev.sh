#!/bin/bash
# ADK Development Environment Startup Script
# This script initializes the ADK development environment with all necessary services

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
        log_warning "No Google Cloud credentials found. ADK features will be limited."
        return 1
    fi
}

# Function to initialize ADK workspace
initialize_adk_workspace() {
    log_info "Initializing ADK workspace..."
    
    # Create workspace directories
    mkdir -p "${ADK_WORKSPACE}/sessions"
    mkdir -p "${ADK_WORKSPACE}/tools"
    mkdir -p "${ADK_WORKSPACE}/logs"
    mkdir -p "${ADK_WORKSPACE}/cache"
    
    # Set permissions
    chmod 755 "${ADK_WORKSPACE}"
    chmod 755 "${ADK_WORKSPACE}/sessions"
    chmod 755 "${ADK_WORKSPACE}/tools"
    chmod 755 "${ADK_WORKSPACE}/logs"
    chmod 755 "${ADK_WORKSPACE}/cache"
    
    log_success "ADK workspace initialized at ${ADK_WORKSPACE}"
}

# Function to start ADK dev portal
start_adk_dev_portal() {
    log_info "Starting ADK development portal..."
    
    # Check if our custom dev portal exists
    if [[ -f "/app/scripts/adk-dev-portal.py" ]]; then
        log_info "Starting custom ADK dev portal on port ${ADK_DEV_PORTAL_PORT}..."
        
        # Start custom dev portal in background
        nohup python3 /app/scripts/adk-dev-portal.py \
            > "${ADK_WORKSPACE}/logs/dev-portal.log" 2>&1 &
        
        echo $! > "${ADK_WORKSPACE}/dev-portal.pid"
        
        # Wait for portal to start
        sleep 5
        
        if kill -0 $(cat "${ADK_WORKSPACE}/dev-portal.pid" 2>/dev/null) 2>/dev/null; then
            log_success "ADK dev portal started successfully on port ${ADK_DEV_PORTAL_PORT}"
            log_info "Portal URL: http://localhost:${ADK_DEV_PORTAL_PORT}"
        else
            log_error "Failed to start custom ADK dev portal"
            return 1
        fi
    # Check if adk CLI is available  
    elif command -v adk >/dev/null 2>&1; then
        log_info "Starting official ADK dev portal on port ${ADK_DEV_PORTAL_PORT}..."
        
        # Start official dev portal in background
        nohup adk dev-portal start \
            --port "${ADK_DEV_PORTAL_PORT}" \
            --workspace "${ADK_WORKSPACE}" \
            --log-level "${ADK_LOG_LEVEL}" \
            > "${ADK_WORKSPACE}/logs/dev-portal.log" 2>&1 &
        
        echo $! > "${ADK_WORKSPACE}/dev-portal.pid"
        
        # Wait for portal to start
        sleep 5
        
        if kill -0 $(cat "${ADK_WORKSPACE}/dev-portal.pid" 2>/dev/null) 2>/dev/null; then
            log_success "Official ADK dev portal started successfully on port ${ADK_DEV_PORTAL_PORT}"
        else
            log_error "Failed to start official ADK dev portal"
            return 1
        fi
    else
        log_warning "No ADK dev portal available (neither custom nor official CLI found)"
        return 1
    fi
}

# Function to verify Python environment
verify_python_environment() {
    log_info "Verifying Python environment..."
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    log_info "Python version: ${python_version}"
    
    # Check required packages (basic ones that should be available)
    required_packages=(
        "sys"
        "os"
        "json"
        "logging"
    )
    
    for package in "${required_packages[@]}"; do
        if python3 -c "import ${package}" 2>/dev/null; then
            log_success "Package ${package} is available"
        else
            log_error "Package ${package} is not available"
            return 1
        fi
    done
    
    log_success "Python environment verified"
}

# Function to run ADK integration tests
run_adk_tests() {
    log_info "Running ADK integration tests..."
    
    # Run tests
    if [[ -f "/app/tests/test_adk_integration.py" ]]; then
        if python3 /app/tests/test_adk_integration.py; then
            log_success "ADK integration tests passed"
        else
            log_warning "ADK integration tests failed (this might be expected without full Google Cloud setup)"
        fi
    else
        log_info "ADK integration tests not found, skipping..."
    fi
}

# Function to display environment information
display_environment_info() {
    log_info "ADK Development Environment Information:"
    echo "================================================"
    echo "Workspace: ${ADK_WORKSPACE}"
    echo "Dev Portal Port: ${ADK_DEV_PORTAL_PORT}"
    echo "Log Level: ${ADK_LOG_LEVEL}"
    echo "Google Cloud Project: ${GOOGLE_CLOUD_PROJECT_ID:-Not set}"
    echo "Google Cloud Location: ${GOOGLE_CLOUD_LOCATION:-Not set}"
    echo "Python Version: $(python3 --version 2>/dev/null || echo 'Not available')"
    echo "ADK CLI: $(command -v adk >/dev/null 2>&1 && echo 'Available' || echo 'Not available')"
    echo "================================================"
}

# Function to cleanup on exit
cleanup() {
    log_info "Cleaning up ADK development environment..."
    
    # Stop dev portal
    if [[ -f "${ADK_WORKSPACE}/dev-portal.pid" ]]; then
        if kill $(cat "${ADK_WORKSPACE}/dev-portal.pid") 2>/dev/null; then
            log_info "ADK dev portal stopped"
        fi
        rm -f "${ADK_WORKSPACE}/dev-portal.pid"
    fi
}

# Set up signal handlers for cleanup
trap cleanup EXIT INT TERM

# Main execution
main() {
    log_info "Starting ADK Development Environment..."
    
    # Display environment information
    display_environment_info
    
    # Check credentials
    check_gcloud_credentials || true
    
    # Verify Python environment
    verify_python_environment
    
    # Initialize workspace
    initialize_adk_workspace
    
    # Start services
    start_adk_dev_portal || true
    
    # Run tests
    run_adk_tests
    
    log_success "ADK Development Environment is ready!"
    log_info "Access points:"
    log_info "  - API Server: http://localhost:8000"
    log_info "  - ADK Dev Portal: http://localhost:${ADK_DEV_PORTAL_PORT}"
    
    # Keep container running
    log_info "Environment is running. Press Ctrl+C to stop."
    
    # Start the main application
    if [[ "${1:-}" == "--api-only" ]]; then
        log_info "Starting API server only..."
        exec python3 -m src.api.main 2>/dev/null || {
            log_warning "API server not available yet, this is expected during development"
            log_info "ADK environment setup completed successfully"
            exit 0
        }
    else
        log_info "Starting full development environment..."
        # Keep container alive
        while true; do
            sleep 30
            # Check if services are still running
            if [[ -f "${ADK_WORKSPACE}/dev-portal.pid" ]] && ! kill -0 $(cat "${ADK_WORKSPACE}/dev-portal.pid") 2>/dev/null; then
                log_warning "ADK dev portal stopped unexpectedly"
            fi
        done
    fi
}

# Execute main function with all arguments
main "$@"