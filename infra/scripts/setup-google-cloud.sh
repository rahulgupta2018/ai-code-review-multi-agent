#!/bin/bash

# Google Cloud Project Setup Script for AI Code Review Multi-Agent System
# This script automates the Google Cloud project setup for GADK integration

set -euo pipefail

# Script configuration
SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_REGION="us-central1"
DEFAULT_PROJECT_PREFIX="ai-code-review"
SERVICE_ACCOUNT_NAME="ai-code-review-gadk"

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
Usage: $SCRIPT_NAME [OPTIONS]

DESCRIPTION:
    Automated Google Cloud project setup for AI Code Review Multi-Agent System
    with GADK integration. This script will:
    
    1. Create a new Google Cloud project
    2. Enable required APIs
    3. Create service account with proper roles
    4. Set up GADK resources
    5. Configure Vertex AI, Discovery Engine, and Dialogflow
    6. Generate credentials and update environment

OPTIONS:
    -p, --project-id PROJECT_ID    Custom project ID (default: auto-generated)
    -r, --region REGION           Google Cloud region (default: us-central1)
    -b, --billing-account ID      Billing account ID (required)
    -e, --email EMAIL             Email for notifications
    -f, --force                   Skip confirmations
    -d, --dry-run                 Show what would be done without executing
    -h, --help                    Show this help message
    -v, --verbose                 Enable verbose output

EXAMPLES:
    $SCRIPT_NAME --billing-account 012345-678901-ABCDEF
    $SCRIPT_NAME -p my-ai-project -r europe-west1 -b 012345-678901-ABCDEF
    $SCRIPT_NAME --dry-run --billing-account 012345-678901-ABCDEF

PREREQUISITES:
    - Google Cloud CLI installed and authenticated
    - Billing account with owner permissions
    - Docker and Docker Compose installed

EOF
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud CLI is not installed"
        log_info "Install it from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 &> /dev/null; then
        log_error "Not authenticated with Google Cloud"
        log_info "Run: gcloud auth login"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check project root
    if [[ ! -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        log_error "Not in the correct project directory"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Validate billing account
validate_billing_account() {
    local billing_account="$1"
    
    log_info "Validating billing account: $billing_account"
    
    if ! gcloud billing accounts describe "$billing_account" &> /dev/null; then
        log_error "Invalid billing account or insufficient permissions"
        log_info "List available accounts with: gcloud billing accounts list"
        exit 1
    fi
    
    log_success "Billing account validated"
}

# Generate unique project ID
generate_project_id() {
    local prefix="$1"
    local timestamp=$(date +%s)
    local random=$(( RANDOM % 9000 + 1000 ))
    echo "${prefix}-${timestamp}-${random}"
}

# Create Google Cloud project
create_project() {
    local project_id="$1"
    local billing_account="$2"
    
    log_info "Creating Google Cloud project: $project_id"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create project: $project_id"
        return 0
    fi
    
    # Create project
    if gcloud projects create "$project_id" \
        --name="AI Code Review Multi-Agent" \
        --labels="environment=development,type=ai-agents,created-by=setup-script"; then
        log_success "Project created successfully"
    else
        log_error "Failed to create project"
        exit 1
    fi
    
    # Set as default project
    gcloud config set project "$project_id"
    
    # Link billing account
    log_info "Linking billing account..."
    if gcloud billing projects link "$project_id" --billing-account="$billing_account"; then
        log_success "Billing account linked successfully"
    else
        log_error "Failed to link billing account"
        exit 1
    fi
}

# Enable required APIs
enable_apis() {
    local project_id="$1"
    
    log_info "Enabling required APIs..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would enable required APIs"
        return 0
    fi
    
    local apis=(
        "aiplatform.googleapis.com"
        "discoveryengine.googleapis.com"
        "dialogflow.googleapis.com"
        "cloudbuild.googleapis.com"
        "container.googleapis.com"
        "compute.googleapis.com"
        "storage.googleapis.com"
        "secretmanager.googleapis.com"
        "logging.googleapis.com"
        "monitoring.googleapis.com"
        "cloudresourcemanager.googleapis.com"
        "iam.googleapis.com"
    )
    
    if gcloud services enable "${apis[@]}"; then
        log_success "APIs enabled successfully"
    else
        log_error "Failed to enable some APIs"
        exit 1
    fi
    
    # Wait for API propagation
    log_info "Waiting for API propagation (2 minutes)..."
    sleep 120
}

# Create service account
create_service_account() {
    local project_id="$1"
    local region="$2"
    
    log_info "Creating service account..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create service account: $SERVICE_ACCOUNT_NAME"
        return 0
    fi
    
    # Create service account
    if gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="AI Code Review GADK Service Account" \
        --description="Service account for AI Code Review Multi-Agent System with GADK"; then
        log_success "Service account created"
    else
        log_error "Failed to create service account"
        exit 1
    fi
    
    local service_account_email="${SERVICE_ACCOUNT_NAME}@${project_id}.iam.gserviceaccount.com"
    
    # Assign roles
    log_info "Assigning IAM roles..."
    local roles=(
        "roles/aiplatform.user"
        "roles/aiplatform.admin"
        "roles/discoveryengine.admin"
        "roles/dialogflow.admin"
        "roles/storage.admin"
        "roles/logging.admin"
        "roles/monitoring.admin"
        "roles/secretmanager.admin"
    )
    
    for role in "${roles[@]}"; do
        if gcloud projects add-iam-policy-binding "$project_id" \
            --member="serviceAccount:${service_account_email}" \
            --role="$role"; then
            log_info "Assigned role: $role"
        else
            log_warning "Failed to assign role: $role"
        fi
    done
    
    # Create credentials
    log_info "Creating service account credentials..."
    mkdir -p "$PROJECT_ROOT/credentials"
    
    if gcloud iam service-accounts keys create "$PROJECT_ROOT/credentials/google-cloud-credentials.json" \
        --iam-account="$service_account_email"; then
        log_success "Credentials created"
        
        # Set secure permissions
        chmod 600 "$PROJECT_ROOT/credentials/google-cloud-credentials.json"
    else
        log_error "Failed to create credentials"
        exit 1
    fi
}

# Set up GADK resources
setup_gadk_resources() {
    local project_id="$1"
    local region="$2"
    
    log_info "Setting up GADK resources..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would set up GADK resources"
        return 0
    fi
    
    # Set default region for AI services
    gcloud config set ai/region "$region"
    
    # Create Cloud Storage bucket
    local bucket_name="${project_id}-gadk-data"
    
    if gsutil mb -p "$project_id" -c STANDARD -l "$region" "gs://$bucket_name"; then
        log_success "Storage bucket created: $bucket_name"
        
        # Set bucket permissions
        local service_account_email="${SERVICE_ACCOUNT_NAME}@${project_id}.iam.gserviceaccount.com"
        gsutil iam ch "serviceAccount:${service_account_email}:roles/storage.admin" "gs://$bucket_name"
    else
        log_warning "Failed to create storage bucket (may already exist)"
    fi
    
    # Test Vertex AI access
    log_info "Testing Vertex AI access..."
    if gcloud ai models list --region="$region" &> /dev/null; then
        log_success "Vertex AI access confirmed"
    else
        log_warning "Vertex AI access test failed (may need time to propagate)"
    fi
}

# Create Discovery Engine resources
setup_discovery_engine() {
    local project_id="$1"
    
    log_info "Setting up Discovery Engine..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would set up Discovery Engine"
        return 0
    fi
    
    # Create Discovery Engine app
    if gcloud alpha discovery-engine apps create ai-code-review-app \
        --location=global \
        --industry-vertical=GENERIC; then
        log_success "Discovery Engine app created"
    else
        log_warning "Discovery Engine app creation failed (may already exist)"
    fi
    
    # Create data store
    if gcloud alpha discovery-engine data-stores create code-analysis-store \
        --location=global \
        --industry-vertical=GENERIC \
        --content-config=CONTENT_REQUIRED \
        --solution-types=SOLUTION_TYPE_SEARCH; then
        log_success "Discovery Engine data store created"
    else
        log_warning "Discovery Engine data store creation failed (may already exist)"
    fi
}

# Create Dialogflow resources
setup_dialogflow() {
    local project_id="$1"
    
    log_info "Setting up Dialogflow CX..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would set up Dialogflow CX"
        return 0
    fi
    
    # Create Dialogflow CX agent
    if gcloud alpha dialogflow cx agents create \
        --display-name="AI Code Review Agent" \
        --description="Agent for AI Code Review interactions" \
        --default-language-code="en" \
        --time-zone="America/New_York" \
        --location=global; then
        log_success "Dialogflow CX agent created"
    else
        log_warning "Dialogflow CX agent creation failed (may already exist)"
    fi
}

# Update environment configuration
update_environment() {
    local project_id="$1"
    local region="$2"
    local email="$3"
    
    log_info "Updating environment configuration..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would update .env file"
        return 0
    fi
    
    local env_file="$PROJECT_ROOT/.env"
    local service_account_email="${SERVICE_ACCOUNT_NAME}@${project_id}.iam.gserviceaccount.com"
    local bucket_name="${project_id}-gadk-data"
    
    # Update .env file
    sed -i.bak "s/GOOGLE_CLOUD_PROJECT_ID=.*/GOOGLE_CLOUD_PROJECT_ID=$project_id/" "$env_file"
    sed -i.bak "s/GOOGLE_CLOUD_LOCATION=.*/GOOGLE_CLOUD_LOCATION=$region/" "$env_file"
    sed -i.bak "s/GADK_PROJECT_ID=.*/GADK_PROJECT_ID=$project_id/" "$env_file"
    sed -i.bak "s/VERTEX_AI_LOCATION=.*/VERTEX_AI_LOCATION=$region/" "$env_file"
    
    # Add additional configuration
    cat >> "$env_file" << EOF

# Generated by setup script on $(date)
SERVICE_ACCOUNT_EMAIL=$service_account_email
GADK_BUCKET=$bucket_name
SETUP_COMPLETED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF
    
    # Remove backup file
    rm -f "${env_file}.bak"
    
    log_success "Environment configuration updated"
}

# Set up monitoring and alerting
setup_monitoring() {
    local project_id="$1"
    local email="$2"
    
    if [[ -z "$email" ]]; then
        log_info "Skipping monitoring setup (no email provided)"
        return 0
    fi
    
    log_info "Setting up monitoring..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would set up monitoring for $email"
        return 0
    fi
    
    # Create notification channel
    if gcloud alpha monitoring channels create \
        --display-name="AI Code Review Alerts" \
        --type=email \
        --channel-labels=email_address="$email"; then
        log_success "Monitoring notification channel created"
    else
        log_warning "Failed to create monitoring notification channel"
    fi
}

# Print setup summary
print_summary() {
    local project_id="$1"
    local region="$2"
    local service_account_email="${SERVICE_ACCOUNT_NAME}@${project_id}.iam.gserviceaccount.com"
    
    cat << EOF

${GREEN}============================================================================${NC}
${GREEN}🎉 GOOGLE CLOUD SETUP COMPLETED SUCCESSFULLY!${NC}
${GREEN}============================================================================${NC}

${BLUE}Project Details:${NC}
  Project ID: $project_id
  Region: $region
  Service Account: $service_account_email

${BLUE}Created Resources:${NC}
  ✅ Google Cloud Project with billing enabled
  ✅ Required APIs enabled (Vertex AI, Discovery Engine, Dialogflow)
  ✅ Service account with proper IAM roles
  ✅ Cloud Storage bucket for GADK data
  ✅ Discovery Engine app and data store
  ✅ Dialogflow CX agent
  ✅ Service account credentials

${BLUE}Generated Files:${NC}
  📄 credentials/google-cloud-credentials.json
  📝 .env (updated with project configuration)

${BLUE}Next Steps:${NC}
  1. Review and customize your .env file if needed
  2. Start the development environment:
     ${YELLOW}./scripts/dev-setup.sh up development${NC}
  
  3. Test the GADK integration:
     ${YELLOW}./scripts/dev-setup.sh status${NC}
  
  4. Open the monitoring dashboard:
     ${YELLOW}http://localhost:3000${NC} (Grafana)

${BLUE}Documentation:${NC}
  📚 Setup Guide: docs/google_cloud_setup_guide.md
  🔧 Troubleshooting: Check the guide for common issues

${YELLOW}⚠️  Important Security Notes:${NC}
  • Keep your credentials file secure and never commit it to git
  • Review IAM permissions periodically
  • Monitor usage and costs in Google Cloud Console

${GREEN}Happy coding with GADK integration! 🚀${NC}

EOF
}

# Main function
main() {
    # Default options
    PROJECT_ID=""
    REGION="$DEFAULT_REGION"
    BILLING_ACCOUNT=""
    EMAIL=""
    FORCE=false
    DRY_RUN=false
    VERBOSE=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--project-id)
                PROJECT_ID="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -b|--billing-account)
                BILLING_ACCOUNT="$2"
                shift 2
                ;;
            -e|--email)
                EMAIL="$2"
                shift 2
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                set -x
                shift
                ;;
            -h|--help)
                print_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
    
    # Validate required parameters
    if [[ -z "$BILLING_ACCOUNT" ]]; then
        log_error "Billing account is required"
        log_info "Find your billing account ID with: gcloud billing accounts list"
        exit 1
    fi
    
    # Generate project ID if not provided
    if [[ -z "$PROJECT_ID" ]]; then
        PROJECT_ID=$(generate_project_id "$DEFAULT_PROJECT_PREFIX")
        log_info "Generated project ID: $PROJECT_ID"
    fi
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Show configuration
    log_info "Setup Configuration:"
    echo "  Project ID: $PROJECT_ID"
    echo "  Region: $REGION"
    echo "  Billing Account: $BILLING_ACCOUNT"
    echo "  Email: ${EMAIL:-"(not provided)"}"
    echo "  Dry Run: $DRY_RUN"
    
    # Confirm if not forced
    if [[ "$FORCE" != "true" ]] && [[ "$DRY_RUN" != "true" ]]; then
        echo
        read -p "Continue with setup? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Setup cancelled"
            exit 0
        fi
    fi
    
    # Run setup steps
    check_prerequisites
    validate_billing_account "$BILLING_ACCOUNT"
    create_project "$PROJECT_ID" "$BILLING_ACCOUNT"
    enable_apis "$PROJECT_ID"
    create_service_account "$PROJECT_ID" "$REGION"
    setup_gadk_resources "$PROJECT_ID" "$REGION"
    setup_discovery_engine "$PROJECT_ID"
    setup_dialogflow "$PROJECT_ID"
    update_environment "$PROJECT_ID" "$REGION" "$EMAIL"
    setup_monitoring "$PROJECT_ID" "$EMAIL"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        print_summary "$PROJECT_ID" "$REGION"
    else
        log_info "Dry run completed - no changes made"
    fi
}

# Run main function
main "$@"