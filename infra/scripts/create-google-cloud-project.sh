#!/bin/bash

# Google Cloud Multi-Agent Project Setup Script
# Configurable script for creating and setting up Google Cloud projects
# for the AI Code Review Multi-Agent System with GADK integration

set -euo pipefail

# Script metadata
SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration files
CONFIG_FILE="${PROJECT_ROOT}/config/google-cloud-setup.yaml"
ENV_FILE="${PROJECT_ROOT}/.env"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_debug() {
    if [[ "${DEBUG:-false}" == "true" ]]; then
        echo -e "${CYAN}[DEBUG]${NC} $1"
    fi
}

# Print usage information
print_usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS] [COMMAND]

COMMANDS:
    create                 Create new Google Cloud project
    configure             Configure existing project
    verify                Verify project setup
    cleanup               Clean up project resources
    update-config         Update configuration file
    list-projects         List available projects
    switch-project        Switch to different project
    
OPTIONS:
    -h, --help            Show this help message
    -c, --config FILE     Use custom configuration file
    -e, --email EMAIL     Override account email
    -b, --billing ID      Override billing account ID
    -r, --region REGION   Override default region
    -p, --project NAME    Override project name prefix
    -d, --dry-run         Show what would be done without executing
    -v, --verbose         Enable verbose output
    -y, --yes             Skip confirmation prompts
    --debug               Enable debug logging

EXAMPLES:
    $SCRIPT_NAME create                           # Create project with default config
    $SCRIPT_NAME create -e user@example.com       # Create with different email
    $SCRIPT_NAME create -d                        # Dry run to see what would happen
    $SCRIPT_NAME configure -p my-project          # Configure existing project
    $SCRIPT_NAME verify                           # Verify current setup
    $SCRIPT_NAME update-config                    # Update configuration interactively

CONFIGURATION:
    Configuration is read from: $CONFIG_FILE
    You can override settings using command-line options or by editing the config file.
    
EOF
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud CLI (gcloud) is not installed"
        log_info "Install it from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check if yq is installed for YAML parsing
    if ! command -v yq &> /dev/null; then
        log_warning "yq is not installed. Installing via homebrew..."
        if command -v brew &> /dev/null; then
            brew install yq
        else
            log_error "Please install yq manually: https://github.com/mikefarah/yq"
            exit 1
        fi
    fi
    
    # Check if jq is installed for JSON parsing
    if ! command -v jq &> /dev/null; then
        log_warning "jq is not installed. Installing via homebrew..."
        if command -v brew &> /dev/null; then
            brew install jq
        else
            log_error "Please install jq manually"
            exit 1
        fi
    fi
    
    # Check configuration file
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Load configuration from YAML file
load_config() {
    log_debug "Loading configuration from $CONFIG_FILE"
    
    # Parse YAML configuration
    PROJECT_NAME_PREFIX=$(yq '.project.name_prefix' "$CONFIG_FILE")
    PROJECT_DISPLAY_NAME=$(yq '.project.display_name' "$CONFIG_FILE")
    PROJECT_DESCRIPTION=$(yq '.project.description' "$CONFIG_FILE")
    
    ACCOUNT_EMAIL=$(yq '.account.email' "$CONFIG_FILE")
    BACKUP_EMAIL=$(yq '.account.backup_email' "$CONFIG_FILE")
    
    BILLING_ACCOUNT_ID=$(yq '.billing.account_id' "$CONFIG_FILE")
    AUTO_ENABLE_BILLING=$(yq '.billing.auto_enable' "$CONFIG_FILE")
    BUDGET_ALERT=$(yq '.billing.budget_alert' "$CONFIG_FILE")
    
    DEFAULT_REGION=$(yq '.location.region' "$CONFIG_FILE")
    DEFAULT_ZONE=$(yq '.location.zone' "$CONFIG_FILE")
    MULTI_REGION=$(yq '.location.multi_region' "$CONFIG_FILE")
    
    # Override with command line options if provided
    ACCOUNT_EMAIL="${OVERRIDE_EMAIL:-$ACCOUNT_EMAIL}"
    BILLING_ACCOUNT_ID="${OVERRIDE_BILLING:-$BILLING_ACCOUNT_ID}"
    DEFAULT_REGION="${OVERRIDE_REGION:-$DEFAULT_REGION}"
    PROJECT_NAME_PREFIX="${OVERRIDE_PROJECT:-$PROJECT_NAME_PREFIX}"
    
    log_debug "Configuration loaded successfully"
}

# Generate unique project ID
generate_project_id() {
    # Generate unique project ID with timestamp and random number
    local timestamp=$(date +%s)
    local short_timestamp=${timestamp: -7}  # Last 7 digits of timestamp
    local random=$(( RANDOM % 1000 ))
    
    # Use the configured project name prefix
    PROJECT_ID="${PROJECT_NAME_PREFIX}-${short_timestamp}-${random}"
    
    # Check if it exceeds 30 characters and truncate if needed
    if [[ ${#PROJECT_ID} -gt 30 ]]; then
        # Use shorter timestamp if needed
        local shorter_timestamp=${timestamp: -5}
        PROJECT_ID="${PROJECT_NAME_PREFIX}-${shorter_timestamp}-${random}"
        
        # If still too long, truncate the prefix
        if [[ ${#PROJECT_ID} -gt 30 ]]; then
            local short_prefix=$(echo "$PROJECT_NAME_PREFIX" | cut -c1-15)
            PROJECT_ID="${short_prefix}-${shorter_timestamp}-${random}"
        fi
    fi
    
    log_debug "Generated project ID: $PROJECT_ID (${#PROJECT_ID} characters)"
}

# Authenticate with Google Cloud
authenticate_gcloud() {
    log_step "Authenticating with Google Cloud..."
    
    # Check if already authenticated
    local current_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -n1)
    
    if [[ "$current_account" == "$ACCOUNT_EMAIL" ]]; then
        log_success "Already authenticated as $ACCOUNT_EMAIL"
        return 0
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would authenticate as $ACCOUNT_EMAIL"
        return 0
    fi
    
    # Authenticate
    log_info "Authenticating as $ACCOUNT_EMAIL..."
    if gcloud auth login "$ACCOUNT_EMAIL" --no-launch-browser; then
        log_success "Authentication successful"
    else
        log_error "Authentication failed"
        exit 1
    fi
    
    # Set default account
    gcloud config set account "$ACCOUNT_EMAIL"
}

# Get or validate billing account
setup_billing() {
    log_step "Setting up billing account..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would set up billing account"
        return 0
    fi
    
    # List available billing accounts
    local billing_accounts=$(gcloud billing accounts list --format="json")
    
    if [[ $(echo "$billing_accounts" | jq '. | length') -eq 0 ]]; then
        log_error "No billing accounts found. Please set up billing in Google Cloud Console."
        log_info "Visit: https://console.cloud.google.com/billing"
        exit 1
    fi
    
    # If no billing account specified, use the first active one
    if [[ -z "$BILLING_ACCOUNT_ID" || "$BILLING_ACCOUNT_ID" == "null" ]]; then
        BILLING_ACCOUNT_ID=$(echo "$billing_accounts" | jq -r '.[] | select(.open == true) | .name' | head -n1)
        if [[ -z "$BILLING_ACCOUNT_ID" ]]; then
            log_error "No active billing accounts found"
            exit 1
        fi
        log_info "Using billing account: $BILLING_ACCOUNT_ID"
    fi
    
    # Extract account ID from full name if needed
    if [[ "$BILLING_ACCOUNT_ID" =~ billingAccounts/ ]]; then
        BILLING_ACCOUNT_ID=$(echo "$BILLING_ACCOUNT_ID" | sed 's|billingAccounts/||')
    fi
    
    log_success "Billing account configured: $BILLING_ACCOUNT_ID"
}

# Create Google Cloud project
create_project() {
    log_step "Creating Google Cloud project..."
    
    generate_project_id
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create project:"
        log_info "  Project ID: $PROJECT_ID"
        log_info "  Display Name: $PROJECT_DISPLAY_NAME"
        log_info "  Description: $PROJECT_DESCRIPTION"
        return 0
    fi
    
    # Create project
    if gcloud projects create "$PROJECT_ID" \
        --name="$PROJECT_DISPLAY_NAME" \
        --set-as-default; then
        log_success "Project created successfully: $PROJECT_ID"
    else
        log_error "Failed to create project"
        exit 1
    fi
    
    # Link billing account
    if [[ "$AUTO_ENABLE_BILLING" == "true" ]]; then
        log_info "Linking billing account..."
        if gcloud billing projects link "$PROJECT_ID" \
            --billing-account="$BILLING_ACCOUNT_ID"; then
            log_success "Billing account linked successfully"
        else
            log_warning "Failed to link billing account. You may need to do this manually."
        fi
    fi
}

# Enable required APIs
enable_apis() {
    log_step "Enabling required APIs..."
    
    # Get services from config
    local core_services=$(yq '.services.core[]' "$CONFIG_FILE")
    local ai_ml_services=$(yq '.services.ai_ml[]' "$CONFIG_FILE")
    local storage_compute_services=$(yq '.services.storage_compute[]' "$CONFIG_FILE")
    local monitoring_services=$(yq '.services.monitoring[]' "$CONFIG_FILE")
    
    # Combine all services
    local all_services=$(echo -e "$core_services\n$ai_ml_services\n$storage_compute_services\n$monitoring_services")
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would enable APIs:"
        echo "$all_services" | while read service; do
            log_info "  - $service"
        done
        return 0
    fi
    
    # Enable APIs in batches
    local services_array=()
    while IFS= read -r service; do
        if [[ -n "$service" ]]; then
            services_array+=("$service")
        fi
    done <<< "$all_services"
    
    if [[ ${#services_array[@]} -gt 0 ]]; then
        log_info "Enabling ${#services_array[@]} APIs..."
        local failed_apis=()
        local enabled_count=0
        
        # Enable APIs one by one to identify failures
        for service in "${services_array[@]}"; do
            if gcloud services enable "$service" --project="$PROJECT_ID" 2>/dev/null; then
                log_success "✓ Enabled: $service"
                ((enabled_count++))
            else
                log_warning "✗ Failed to enable: $service"
                failed_apis+=("$service")
            fi
        done
        
        log_info "Successfully enabled $enabled_count/${#services_array[@]} APIs"
        
        if [[ ${#failed_apis[@]} -gt 0 ]]; then
            log_warning "Failed to enable ${#failed_apis[@]} APIs:"
            for api in "${failed_apis[@]}"; do
                log_warning "  - $api"
            done
            log_warning "Continuing with setup using available APIs..."
        fi
    fi
}

# Create service accounts
create_service_accounts() {
    log_step "Creating service accounts..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create service accounts"
        return 0
    fi
    
    # Create GADK service account
    local gadk_sa_name=$(yq '.service_accounts.gadk.name' "$CONFIG_FILE")
    local gadk_sa_display=$(yq '.service_accounts.gadk.display_name' "$CONFIG_FILE")
    local gadk_sa_desc=$(yq '.service_accounts.gadk.description' "$CONFIG_FILE")
    
    log_info "Creating GADK service account..."
    local create_output
    if create_output=$(gcloud iam service-accounts create "$gadk_sa_name" \
        --display-name="$gadk_sa_display" \
        --description="$gadk_sa_desc" \
        --project="$PROJECT_ID" 2>&1); then
        log_success "GADK service account created"
        # Wait for service account to propagate
        log_info "Waiting for service account to propagate..."
        sleep 10
    else
        # Check if it's just a "already exists" conflict
        if echo "$create_output" | grep -q "already exists"; then
            log_success "GADK service account already exists (this is fine)"
        else
            log_error "Failed to create GADK service account: $create_output"
            exit 1
        fi
    fi
    
    # Assign roles to GADK service account
    local gadk_roles=$(yq '.service_accounts.gadk.roles[]' "$CONFIG_FILE")
    while IFS= read -r role; do
        if [[ -n "$role" ]]; then
            log_info "Assigning role $role to GADK service account..."
            local retry_count=0
            local max_retries=3
            while [[ $retry_count -lt $max_retries ]]; do
                if gcloud projects add-iam-policy-binding "$PROJECT_ID" \
                    --member="serviceAccount:${gadk_sa_name}@${PROJECT_ID}.iam.gserviceaccount.com" \
                    --role="$role" >/dev/null 2>&1; then
                    log_success "✓ Assigned role: $role"
                    break
                else
                    ((retry_count++))
                    if [[ $retry_count -lt $max_retries ]]; then
                        log_warning "Role assignment failed, retrying in 5 seconds... ($retry_count/$max_retries)"
                        sleep 5
                    else
                        log_error "✗ Failed to assign role after $max_retries attempts: $role"
                    fi
                fi
            done
        fi
    done <<< "$gadk_roles"
    
    # Create compute service account
    local compute_sa_name=$(yq '.service_accounts.compute.name' "$CONFIG_FILE")
    local compute_sa_display=$(yq '.service_accounts.compute.display_name' "$CONFIG_FILE")
    local compute_sa_desc=$(yq '.service_accounts.compute.description' "$CONFIG_FILE")
    
    log_info "Creating compute service account..."
    local create_output
    if create_output=$(gcloud iam service-accounts create "$compute_sa_name" \
        --display-name="$compute_sa_display" \
        --description="$compute_sa_desc" \
        --project="$PROJECT_ID" 2>&1); then
        log_success "Compute service account created"
        # Wait for service account to propagate
        log_info "Waiting for service account to propagate..."
        sleep 10
    else
        # Check if it's just a "already exists" conflict
        if echo "$create_output" | grep -q "already exists"; then
            log_success "Compute service account already exists (this is fine)"
        else
            log_error "Failed to create compute service account: $create_output"
            exit 1
        fi
    fi
    
    # Assign roles to compute service account
    local compute_roles=$(yq '.service_accounts.compute.roles[]' "$CONFIG_FILE")
    while IFS= read -r role; do
        if [[ -n "$role" ]]; then
            log_info "Assigning role $role to compute service account..."
            local retry_count=0
            local max_retries=3
            while [[ $retry_count -lt $max_retries ]]; do
                if gcloud projects add-iam-policy-binding "$PROJECT_ID" \
                    --member="serviceAccount:${compute_sa_name}@${PROJECT_ID}.iam.gserviceaccount.com" \
                    --role="$role" >/dev/null 2>&1; then
                    log_success "✓ Assigned role: $role"
                    break
                else
                    ((retry_count++))
                    if [[ $retry_count -lt $max_retries ]]; then
                        log_warning "Role assignment failed, retrying in 5 seconds... ($retry_count/$max_retries)"
                        sleep 5
                    else
                        log_error "✗ Failed to assign role after $max_retries attempts: $role"
                    fi
                fi
            done
        fi
    done <<< "$compute_roles"
}

# Create storage resources
create_storage_resources() {
    log_step "Creating storage resources..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create storage resources"
        return 0
    fi
    
    # Create data bucket
    local data_bucket_suffix=$(yq '.resources.storage.data_bucket.name_suffix' "$CONFIG_FILE")
    local data_bucket_location=$(yq '.resources.storage.data_bucket.location' "$CONFIG_FILE")
    local data_bucket_class=$(yq '.resources.storage.data_bucket.storage_class' "$CONFIG_FILE")
    
    local data_bucket_name="${PROJECT_ID}-${data_bucket_suffix}"
    
    log_info "Creating data bucket: $data_bucket_name"
    local create_output
    if create_output=$(gsutil mb -p "$PROJECT_ID" -c "$data_bucket_class" -l "$data_bucket_location" "gs://$data_bucket_name" 2>&1); then
        log_success "Data bucket created: $data_bucket_name"
    else
        # Check if it's just a "already exists" conflict
        if echo "$create_output" | grep -q "already exists\|BucketAlreadyExists"; then
            log_success "Data bucket already exists (this is fine): $data_bucket_name"
        else
            log_error "Failed to create data bucket: $create_output"
            exit 1
        fi
    fi
    
    # Create backup bucket
    local backup_bucket_suffix=$(yq '.resources.storage.backup_bucket.name_suffix' "$CONFIG_FILE")
    local backup_bucket_location=$(yq '.resources.storage.backup_bucket.location' "$CONFIG_FILE")
    local backup_bucket_class=$(yq '.resources.storage.backup_bucket.storage_class' "$CONFIG_FILE")
    
    local backup_bucket_name="${PROJECT_ID}-${backup_bucket_suffix}"
    
    log_info "Creating backup bucket: $backup_bucket_name"
    if create_output=$(gsutil mb -p "$PROJECT_ID" -c "$backup_bucket_class" -l "$backup_bucket_location" "gs://$backup_bucket_name" 2>&1); then
        log_success "Backup bucket created: $backup_bucket_name"
    else
        # Check if it's just a "already exists" conflict
        if echo "$create_output" | grep -q "already exists\|BucketAlreadyExists"; then
            log_success "Backup bucket already exists (this is fine): $backup_bucket_name"
        else
            log_error "Failed to create backup bucket: $create_output"
            exit 1
        fi
    fi
}

# Generate service account key
generate_service_account_key() {
    log_step "Generating service account key..."
    
    local gadk_sa_name=$(yq '.service_accounts.gadk.name' "$CONFIG_FILE")
    local key_file="${PROJECT_ROOT}/credentials/google-cloud-credentials.json"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would generate service account key to $key_file"
        return 0
    fi
    
    # Create credentials directory if it doesn't exist
    mkdir -p "$(dirname "$key_file")"
    
    # Generate key
    log_info "Generating service account key..."
    if gcloud iam service-accounts keys create "$key_file" \
        --iam-account="${gadk_sa_name}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --project="$PROJECT_ID"; then
        log_success "Service account key generated: $key_file"
        
        # Set file permissions
        chmod 600 "$key_file"
        log_info "Key file permissions set to 600"
    else
        log_error "Failed to generate service account key"
        exit 1
    fi
}

# Update environment file
update_environment_file() {
    log_step "Updating environment file..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would update environment file"
        return 0
    fi
    
    # Create .env file if it doesn't exist
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f "$ENV_EXAMPLE" ]]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            log_info "Created .env file from .env.example"
        else
            touch "$ENV_FILE"
            log_info "Created new .env file"
        fi
    fi
    
    # Update environment variables
    local gadk_sa_name=$(yq '.service_accounts.gadk.name' "$CONFIG_FILE")
    local data_bucket_suffix=$(yq '.resources.storage.data_bucket.name_suffix' "$CONFIG_FILE")
    local data_bucket_name="${PROJECT_ID}-${data_bucket_suffix}"
    
    # Update or add environment variables
    local env_vars=(
        "GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID"
        "GOOGLE_CLOUD_LOCATION=$DEFAULT_REGION"
        "GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-cloud-credentials.json"
        "GADK_ENABLED=true"
        "GADK_PROJECT_ID=$PROJECT_ID"
        "GADK_BUCKET=$data_bucket_name"
        "GADK_SERVICE_ACCOUNT=${gadk_sa_name}@${PROJECT_ID}.iam.gserviceaccount.com"
    )
    
    for env_var in "${env_vars[@]}"; do
        local key=$(echo "$env_var" | cut -d'=' -f1)
        local value=$(echo "$env_var" | cut -d'=' -f2-)
        
        if grep -q "^${key}=" "$ENV_FILE"; then
            # Update existing variable
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i.bak "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
            else
                sed -i.bak "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
            fi
        else
            # Add new variable
            echo "${key}=${value}" >> "$ENV_FILE"
        fi
    done
    
    # Remove backup file
    rm -f "${ENV_FILE}.bak"
    
    log_success "Environment file updated"
}

# Verify setup
verify_setup() {
    log_step "Verifying setup..."
    
    local errors=0
    
    # Check project exists and is accessible
    if gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
        log_success "✓ Project $PROJECT_ID is accessible"
    else
        log_error "✗ Cannot access project $PROJECT_ID"
        ((errors++))
    fi
    
    # Check billing is enabled
    if gcloud billing projects describe "$PROJECT_ID" >/dev/null 2>&1; then
        log_success "✓ Billing is enabled"
    else
        log_warning "⚠ Billing may not be enabled"
    fi
    
    # Check APIs are enabled
    local required_apis=("aiplatform.googleapis.com" "discoveryengine.googleapis.com" "dialogflow.googleapis.com")
    for api in "${required_apis[@]}"; do
        if gcloud services list --enabled --filter="name:$api" --format="value(name)" --project="$PROJECT_ID" | grep -q "$api"; then
            log_success "✓ API $api is enabled"
        else
            log_error "✗ API $api is not enabled"
            ((errors++))
        fi
    done
    
    # Check service account exists
    local gadk_sa_name=$(yq '.service_accounts.gadk.name' "$CONFIG_FILE")
    if gcloud iam service-accounts describe "${gadk_sa_name}@${PROJECT_ID}.iam.gserviceaccount.com" --project="$PROJECT_ID" >/dev/null 2>&1; then
        log_success "✓ GADK service account exists"
    else
        log_error "✗ GADK service account not found"
        ((errors++))
    fi
    
    # Check credentials file
    local key_file="${PROJECT_ROOT}/credentials/google-cloud-credentials.json"
    if [[ -f "$key_file" ]]; then
        log_success "✓ Service account key file exists"
    else
        log_error "✗ Service account key file not found"
        ((errors++))
    fi
    
    # Check storage buckets
    local data_bucket_suffix=$(yq '.resources.storage.data_bucket.name_suffix' "$CONFIG_FILE")
    local data_bucket_name="${PROJECT_ID}-${data_bucket_suffix}"
    if gsutil ls "gs://$data_bucket_name" >/dev/null 2>&1; then
        log_success "✓ Data bucket exists: $data_bucket_name"
    else
        log_warning "⚠ Data bucket not found: $data_bucket_name"
    fi
    
    if [[ $errors -eq 0 ]]; then
        log_success "All verification checks passed!"
        return 0
    else
        log_error "$errors verification checks failed"
        return 1
    fi
}

# Display summary
display_summary() {
    cat << EOF

${GREEN}===================================================${NC}
${GREEN}     Google Cloud Project Setup Complete!${NC}
${GREEN}===================================================${NC}

${BLUE}Project Information:${NC}
  Project ID: ${YELLOW}$PROJECT_ID${NC}
  Display Name: $PROJECT_DISPLAY_NAME
  Region: $DEFAULT_REGION
  Account: $ACCOUNT_EMAIL

${BLUE}Resources Created:${NC}
  ✅ Google Cloud Project
  ✅ Service Accounts (GADK, Compute)
  ✅ Required APIs Enabled
  ✅ Storage Buckets
  ✅ IAM Roles Configured
  ✅ Service Account Key Generated

${BLUE}Next Steps:${NC}
  1. Verify your setup: ${CYAN}$SCRIPT_NAME verify${NC}
  2. Test GADK integration: ${CYAN}./scripts/test-infrastructure.sh${NC}
  3. Start development environment: ${CYAN}./scripts/dev-setup.sh up development${NC}

${BLUE}Configuration Files Updated:${NC}
  📁 .env file with project settings
  🔑 credentials/google-cloud-credentials.json

${GREEN}Happy coding with GADK integration! 🚀${NC}

EOF
}

# List available projects
list_projects() {
    log_step "Listing available Google Cloud projects..."
    
    gcloud projects list --format="table(
        projectId:label='PROJECT_ID',
        name:label='NAME',
        projectNumber:label='NUMBER',
        lifecycleState:label='STATE'
    )"
}

# Switch to different project
switch_project() {
    local target_project="$1"
    
    if [[ -z "$target_project" ]]; then
        log_error "Project ID required for switch command"
        exit 1
    fi
    
    log_step "Switching to project: $target_project"
    
    # Check if project exists
    if ! gcloud projects describe "$target_project" >/dev/null 2>&1; then
        log_error "Project $target_project not found or not accessible"
        exit 1
    fi
    
    # Set as default project
    gcloud config set project "$target_project"
    
    # Update environment file
    PROJECT_ID="$target_project"
    update_environment_file
    
    log_success "Switched to project: $target_project"
}

# Interactive configuration update
interactive_config_update() {
    log_step "Interactive configuration update..."
    
    echo -e "${BLUE}Current configuration:${NC}"
    echo "  Email: $(yq '.account.email' "$CONFIG_FILE")"
    echo "  Project prefix: $(yq '.project.name_prefix' "$CONFIG_FILE")"
    echo "  Region: $(yq '.location.region' "$CONFIG_FILE")"
    echo
    
    read -p "Update email? (current: $(yq '.account.email' "$CONFIG_FILE")) [Enter to skip]: " new_email
    if [[ -n "$new_email" ]]; then
        yq -i ".account.email = \"$new_email\"" "$CONFIG_FILE"
        log_success "Email updated to: $new_email"
    fi
    
    read -p "Update project prefix? (current: $(yq '.project.name_prefix' "$CONFIG_FILE")) [Enter to skip]: " new_prefix
    if [[ -n "$new_prefix" ]]; then
        yq -i ".project.name_prefix = \"$new_prefix\"" "$CONFIG_FILE"
        log_success "Project prefix updated to: $new_prefix"
    fi
    
    read -p "Update region? (current: $(yq '.location.region' "$CONFIG_FILE")) [Enter to skip]: " new_region
    if [[ -n "$new_region" ]]; then
        yq -i ".location.region = \"$new_region\"" "$CONFIG_FILE"
        log_success "Region updated to: $new_region"
    fi
    
    log_success "Configuration update complete"
}

# Main execution function
main() {
    # Default options
    local command=""
    local dry_run=false
    local verbose=false
    local yes_to_all=false
    local debug=false
    
    # Initialize override variables
    local OVERRIDE_EMAIL=""
    local OVERRIDE_BILLING=""
    local OVERRIDE_REGION=""
    local OVERRIDE_PROJECT=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                print_usage
                exit 0
                ;;
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -e|--email)
                OVERRIDE_EMAIL="$2"
                shift 2
                ;;
            -b|--billing)
                OVERRIDE_BILLING="$2"
                shift 2
                ;;
            -r|--region)
                OVERRIDE_REGION="$2"
                shift 2
                ;;
            -p|--project)
                OVERRIDE_PROJECT="$2"
                shift 2
                ;;
            -d|--dry-run)
                dry_run=true
                shift
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            -y|--yes)
                yes_to_all=true
                shift
                ;;
            --debug)
                debug=true
                shift
                ;;
            create|configure|verify|cleanup|update-config|list-projects|switch-project)
                command="$1"
                shift
                ;;
            *)
                if [[ -z "$command" ]]; then
                    command="$1"
                    shift
                else
                    log_error "Unknown option: $1"
                    print_usage
                    exit 1
                fi
                ;;
        esac
    done
    
    # Set global variables
    DRY_RUN="$dry_run"
    VERBOSE="$verbose"
    YES_TO_ALL="$yes_to_all"
    DEBUG="$debug"
    
    # Default command
    command="${command:-create}"
    
    # Enable verbose output if requested
    if [[ "$verbose" == "true" ]]; then
        set -x
    fi
    
    # Check prerequisites (except for help and list commands)
    if [[ "$command" != "list-projects" ]]; then
        check_prerequisites
    fi
    
    # Load configuration (except for list-projects and update-config)
    if [[ "$command" != "list-projects" && "$command" != "update-config" ]]; then
        load_config
    fi
    
    # Execute command
    case "$command" in
        create)
            echo -e "${GREEN}Creating new Google Cloud project for AI Code Review Multi-Agent System${NC}"
            echo
            
            if [[ "$yes_to_all" != "true" && "$dry_run" != "true" ]]; then
                echo "This will:"
                echo "  • Create a new Google Cloud project"
                echo "  • Enable required APIs"
                echo "  • Create service accounts"
                echo "  • Set up storage resources"
                echo "  • Generate service account keys"
                echo
                read -p "Continue? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log_info "Operation cancelled"
                    exit 0
                fi
            fi
            
            authenticate_gcloud
            setup_billing
            create_project
            enable_apis
            create_service_accounts
            create_storage_resources
            generate_service_account_key
            update_environment_file
            
            if verify_setup; then
                display_summary
            else
                log_warning "Setup completed with some issues. Run '$SCRIPT_NAME verify' to check."
            fi
            ;;
        configure)
            if [[ -n "${OVERRIDE_PROJECT}" ]]; then
                PROJECT_ID="$OVERRIDE_PROJECT"
            else
                read -p "Enter project ID to configure: " PROJECT_ID
            fi
            
            authenticate_gcloud
            enable_apis
            create_service_accounts
            create_storage_resources
            generate_service_account_key
            update_environment_file
            verify_setup
            ;;
        verify)
            if [[ -n "${OVERRIDE_PROJECT}" ]]; then
                PROJECT_ID="$OVERRIDE_PROJECT"
            else
                PROJECT_ID=$(yq '.project.name_prefix' "$CONFIG_FILE" 2>/dev/null || echo "")
                if [[ -z "$PROJECT_ID" ]]; then
                    read -p "Enter project ID to verify: " PROJECT_ID
                fi
            fi
            
            verify_setup
            ;;
        list-projects)
            list_projects
            ;;
        switch-project)
            read -p "Enter project ID to switch to: " target_project
            switch_project "$target_project"
            ;;
        update-config)
            interactive_config_update
            ;;
        cleanup)
            log_warning "Cleanup functionality not yet implemented"
            log_info "Please use Google Cloud Console for resource cleanup"
            ;;
        *)
            log_error "Unknown command: $command"
            print_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"