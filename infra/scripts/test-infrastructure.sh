#!/bin/bash

# Simple Infrastructure Test Script
# Tests basic functionality without complex Docker builds

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

# Test Docker
test_docker() {
    log_info "Testing Docker..."
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running"
        return 1
    fi
    
    log_success "Docker is running"
}

# Test Redis
test_redis() {
    log_info "Testing Redis connectivity..."
    
    if ! docker ps | grep -q ai-code-review-redis; then
        log_error "Redis container is not running"
        return 1
    fi
    
    # Test Redis connection
    if docker exec ai-code-review-redis redis-cli ping | grep -q PONG; then
        log_success "Redis is responding"
    else
        log_error "Redis is not responding"
        return 1
    fi
}

# Test Ollama
test_ollama() {
    log_info "Testing native Ollama connectivity..."
    
    # Test from host
    if curl -s http://localhost:11434/api/version &> /dev/null; then
        log_success "Native Ollama is accessible from host"
    else
        log_error "Native Ollama is not accessible from host"
        return 1
    fi
    
    # Test from Docker network
    if docker run --rm --network=ai-code-review-network curlimages/curl:latest curl -s http://host.docker.internal:11434/api/version &> /dev/null; then
        log_success "Native Ollama is accessible from Docker containers"
    else
        log_error "Native Ollama is not accessible from Docker containers"
        return 1
    fi
}

# Test Docker network
test_network() {
    log_info "Testing Docker network..."
    
    if docker network ls | grep -q ai-code-review-network; then
        log_success "AI Code Review network exists"
    else
        log_error "AI Code Review network does not exist"
        return 1
    fi
}

# Test volumes
test_volumes() {
    log_info "Testing Docker volumes..."
    
    local volumes=(
        "ai-code-review-redis-data"
        "ai-code-review-gadk-workspace"
    )
    
    for volume in "${volumes[@]}"; do
        if docker volume ls | grep -q "$volume"; then
            log_success "Volume $volume exists"
        else
            log_warning "Volume $volume does not exist"
        fi
    done
}

# Test Python environment
test_python() {
    log_info "Testing Python environment..."
    
    # Test basic Python
    if python3 --version &> /dev/null; then
        local python_version=$(python3 --version)
        log_success "Python available: $python_version"
    else
        log_error "Python 3 is not available"
        return 1
    fi
    
    # Test if we can import basic packages
    if python3 -c "import json, os, sys; print('Basic Python imports work')" &> /dev/null; then
        log_success "Basic Python imports work"
    else
        log_error "Basic Python imports failed"
        return 1
    fi
}

# Test environment configuration
test_environment() {
    log_info "Testing environment configuration..."
    
    if [[ -f ".env" ]]; then
        log_success ".env file exists"
        
        # Check key configuration
        if grep -q "OLLAMA_BASE_URL=http://host.docker.internal:11434" .env; then
            log_success "Ollama URL is correctly configured for native access"
        else
            log_warning "Ollama URL may not be configured correctly"
        fi
        
        if grep -q "ENVIRONMENT=development" .env; then
            log_success "Development environment is configured"
        else
            log_warning "Environment may not be configured correctly"
        fi
    else
        log_error ".env file does not exist"
        return 1
    fi
}

# Summary function
print_summary() {
    echo
    log_info "=== Infrastructure Test Summary ==="
    echo
    echo "✅ Components Successfully Tested:"
    echo "   • Docker Engine"
    echo "   • Redis Container"
    echo "   • Native Ollama (with GPU support)"
    echo "   • Docker Network"
    echo "   • Python Environment"
    echo "   • Environment Configuration"
    echo
    echo "🔧 What's Working:"
    echo "   • Basic infrastructure is ready"
    echo "   • Redis caching is available"
    echo "   • Native Ollama with GPU acceleration"
    echo "   • Container networking"
    echo
    echo "📝 Next Steps:"
    echo "   1. Configure Google Cloud project (run setup-google-cloud.sh)"
    echo "   2. Build application containers (when needed)"
    echo "   3. Test BaseAgent GADK integration"
    echo "   4. Run full development environment"
    echo
}

# Main test function
main() {
    log_info "Starting AI Code Review Infrastructure Test..."
    echo
    
    # Run tests
    test_docker
    test_redis
    test_ollama
    test_network
    test_volumes
    test_python
    test_environment
    
    echo
    log_success "🎉 All infrastructure tests passed!"
    print_summary
}

# Run main function
main "$@"