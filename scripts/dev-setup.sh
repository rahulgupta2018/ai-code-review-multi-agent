#!/bin/bash

# AI Code Review Multi-Agent System with AGDK Integration
# Development Environment Setup Script
# This script sets up the complete development environment with Docker Compose

set -euo pipefail

# Script metadata
SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
DEFAULT_PROFILE="development"
DEFAULT_SERVICES="redis ollama ai-code-review-agdk"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
ENV_FILE="${PROJECT_ROOT}/.env"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"

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

# Print usage information
print_usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS] [COMMAND]

COMMANDS:
    up [profile]        Start development environment (default: development)
    down               Stop and remove all containers
    restart            Restart all services
    logs [service]     Show logs for all services or specific service
    status             Show status of all services
    clean              Clean up containers, volumes, and networks
    reset              Reset everything (clean + rebuild)
    shell [service]    Open shell in running service (default: ai-code-review-agdk)
    build              Build all images
    pull               Pull latest images

PROFILES:
    development        Full development environment (default)
    minimal           Redis + Ollama only
    production        Production-ready setup
    monitoring        With Prometheus + Grafana
    tools             Development tools (Redis Commander, File Browser)

OPTIONS:
    -h, --help         Show this help message
    -v, --verbose      Enable verbose output
    -f, --force        Force operations without confirmation
    --no-build         Skip building images
    --detach           Run in background (detached mode)

EXAMPLES:
    $SCRIPT_NAME up                    # Start development environment
    $SCRIPT_NAME up production         # Start production environment
    $SCRIPT_NAME logs ai-code-review-agdk  # Show app logs
    $SCRIPT_NAME shell                 # Open shell in main container
    $SCRIPT_NAME clean                 # Clean up everything

ENVIRONMENT:
    Copy .env.example to .env and configure your settings before running.
    
EOF
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed or not available"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Setup environment file
setup_environment() {
    log_info "Setting up environment configuration..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f "$ENV_EXAMPLE" ]]; then
            log_info "Creating .env file from .env.example..."
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            log_warning "Please edit .env file with your configuration before starting services"
        else
            log_error ".env.example file not found"
            exit 1
        fi
    else
        log_success "Environment file .env already exists"
    fi
}

# Validate environment file
validate_environment() {
    log_info "Validating environment configuration..."
    
    # Check required variables
    local required_vars=(
        "GOOGLE_CLOUD_PROJECT_ID"
        "AGDK_ENABLED"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE" 2>/dev/null || grep -q "^${var}=your-" "$ENV_FILE" 2>/dev/null; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_warning "The following environment variables need to be configured in .env:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        log_warning "Please update .env file with your actual values"
    else
        log_success "Environment validation passed"
    fi
}

# Start services
start_services() {
    local profile="${1:-$DEFAULT_PROFILE}"
    local detach_flag=""
    
    if [[ "$DETACH" == "true" ]]; then
        detach_flag="-d"
    fi
    
    log_info "Starting services with profile: $profile"
    
    # Ensure volumes exist
    docker volume create ai-code-review-redis-data 2>/dev/null || true
    docker volume create ai-code-review-ollama-data 2>/dev/null || true
    docker volume create ai-code-review-agdk-workspace 2>/dev/null || true
    
    # Build if needed
    if [[ "$NO_BUILD" != "true" ]]; then
        log_info "Building services..."
        docker compose --profile "$profile" build
    fi
    
    # Start services
    docker compose --profile "$profile" up $detach_flag
}

# Stop services
stop_services() {
    log_info "Stopping all services..."
    docker compose down
    log_success "Services stopped"
}

# Restart services
restart_services() {
    log_info "Restarting services..."
    docker compose restart
    log_success "Services restarted"
}

# Show logs
show_logs() {
    local service="${1:-}"
    
    if [[ -n "$service" ]]; then
        log_info "Showing logs for service: $service"
        docker compose logs -f "$service"
    else
        log_info "Showing logs for all services"
        docker compose logs -f
    fi
}

# Show status
show_status() {
    log_info "Service status:"
    docker compose ps
    
    echo
    log_info "Volume usage:"
    docker volume ls | grep ai-code-review || true
    
    echo
    log_info "Network status:"
    docker network ls | grep ai-code-review || true
}

# Clean up
clean_up() {
    local force_flag=""
    
    if [[ "$FORCE" == "true" ]]; then
        force_flag="--force"
    fi
    
    log_warning "This will remove all containers, volumes, and networks"
    if [[ "$FORCE" != "true" ]]; then
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Cancelled"
            exit 0
        fi
    fi
    
    log_info "Stopping and removing containers..."
    docker compose down --volumes --remove-orphans
    
    log_info "Removing project volumes..."
    docker volume rm ai-code-review-redis-data 2>/dev/null || true
    docker volume rm ai-code-review-ollama-data 2>/dev/null || true
    docker volume rm ai-code-review-postgres-data 2>/dev/null || true
    docker volume rm ai-code-review-agdk-workspace 2>/dev/null || true
    docker volume rm ai-code-review-jupyter-data 2>/dev/null || true
    docker volume rm ai-code-review-pip-cache 2>/dev/null || true
    docker volume rm ai-code-review-poetry-cache 2>/dev/null || true
    
    log_info "Removing project networks..."
    docker network rm ai-code-review-network 2>/dev/null || true
    
    log_info "Pruning unused Docker resources..."
    docker system prune -f
    
    log_success "Cleanup completed"
}

# Reset environment
reset_environment() {
    log_warning "This will clean everything and rebuild from scratch"
    if [[ "$FORCE" != "true" ]]; then
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Cancelled"
            exit 0
        fi
    fi
    
    clean_up
    
    log_info "Rebuilding images..."
    docker compose build --no-cache
    
    log_success "Reset completed"
}

# Open shell in service
open_shell() {
    local service="${1:-ai-code-review-agdk}"
    
    log_info "Opening shell in service: $service"
    
    # Check if service is running
    if ! docker compose ps "$service" | grep -q "Up"; then
        log_error "Service $service is not running"
        exit 1
    fi
    
    docker compose exec "$service" /bin/bash
}

# Build images
build_images() {
    log_info "Building all images..."
    docker compose build
    log_success "Build completed"
}

# Pull images
pull_images() {
    log_info "Pulling latest images..."
    docker compose pull
    log_success "Pull completed"
}

# Main function
main() {
    # Default options
    VERBOSE=false
    FORCE=false
    NO_BUILD=false
    DETACH=false
    
    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                print_usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                set -x
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            --no-build)
                NO_BUILD=true
                shift
                ;;
            --detach)
                DETACH=true
                shift
                ;;
            up)
                COMMAND="up"
                shift
                PROFILE="${1:-$DEFAULT_PROFILE}"
                [[ $# -gt 0 ]] && shift
                ;;
            down)
                COMMAND="down"
                shift
                ;;
            restart)
                COMMAND="restart"
                shift
                ;;
            logs)
                COMMAND="logs"
                shift
                SERVICE="${1:-}"
                [[ $# -gt 0 ]] && shift
                ;;
            status)
                COMMAND="status"
                shift
                ;;
            clean)
                COMMAND="clean"
                shift
                ;;
            reset)
                COMMAND="reset"
                shift
                ;;
            shell)
                COMMAND="shell"
                shift
                SERVICE="${1:-ai-code-review-agdk}"
                [[ $# -gt 0 ]] && shift
                ;;
            build)
                COMMAND="build"
                shift
                ;;
            pull)
                COMMAND="pull"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
    
    # Set default command
    COMMAND="${COMMAND:-up}"
    PROFILE="${PROFILE:-$DEFAULT_PROFILE}"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Check prerequisites
    check_prerequisites
    
    # Setup environment
    setup_environment
    
    # Validate environment (except for clean/reset)
    if [[ "$COMMAND" != "clean" ]] && [[ "$COMMAND" != "reset" ]]; then
        validate_environment
    fi
    
    # Execute command
    case $COMMAND in
        up)
            start_services "$PROFILE"
            ;;
        down)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs "$SERVICE"
            ;;
        status)
            show_status
            ;;
        clean)
            clean_up
            ;;
        reset)
            reset_environment
            ;;
        shell)
            open_shell "$SERVICE"
            ;;
        build)
            build_images
            ;;
        pull)
            pull_images
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            print_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"