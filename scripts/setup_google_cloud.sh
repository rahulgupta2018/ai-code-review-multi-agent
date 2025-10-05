#!/bin/bash

# Google Cloud Setup Script for Agentic Code Review
# This script automates the Google Cloud project setup for Vertex AI Agents

set -e

echo "🚀 Starting Google Cloud Setup for Agentic Code Review..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "Google Cloud CLI is not installed. Please install it first:"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID with unique suffix
PROJECT_ID="agentic-code-review-$(date +%s)"
SERVICE_ACCOUNT_NAME="agentic-code-review"
CREDENTIALS_FILE="./credentials/google-cloud-credentials.json"

echo "📋 Project Details:"
echo "   Project ID: $PROJECT_ID"
echo "   Service Account: $SERVICE_ACCOUNT_NAME"
echo "   Credentials: $CREDENTIALS_FILE"
echo

# Step 1: Create Project
echo "🔧 Step 1: Creating Google Cloud Project..."
if gcloud projects create $PROJECT_ID --name="Agentic Code Review"; then
    print_status "Project created: $PROJECT_ID"
else
    print_error "Failed to create project. It might already exist."
    read -p "Enter existing project ID: " PROJECT_ID
fi

# Set as default project
gcloud config set project $PROJECT_ID
print_status "Set as default project"

# Step 2: Enable Billing (user needs to do this manually)
echo
print_warning "MANUAL STEP REQUIRED:"
echo "   1. Go to https://console.cloud.google.com/billing"
echo "   2. Link your project to a billing account"
echo "   3. The free tier includes \$300 credit"
read -p "Press Enter after enabling billing..."

# Step 3: Enable APIs
echo
echo "🔧 Step 2: Enabling Required APIs..."
apis=(
    "aiplatform.googleapis.com"
    "discoveryengine.googleapis.com"
    "dialogflow.googleapis.com"
    "cloudbuild.googleapis.com"
    "artifactregistry.googleapis.com"
)

for api in "${apis[@]}"; do
    echo "   Enabling $api..."
    gcloud services enable $api
done
print_status "All required APIs enabled"

# Step 4: Create Service Account
echo
echo "🔧 Step 3: Creating Service Account..."
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="Agentic Code Review Service Account" \
    --description="Service account for Vertex AI Agent Builder integration"

SERVICE_ACCOUNT_EMAIL=$(gcloud iam service-accounts list \
    --filter="displayName:Agentic Code Review Service Account" \
    --format="value(email)")

print_status "Service account created: $SERVICE_ACCOUNT_EMAIL"

# Step 5: Grant Permissions
echo
echo "🔧 Step 4: Granting IAM Permissions..."
roles=(
    "roles/aiplatform.user"
    "roles/discoveryengine.admin"
    "roles/dialogflow.admin"
)

for role in "${roles[@]}"; do
    echo "   Granting $role..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$role"
done
print_status "IAM permissions granted"

# Step 6: Generate Credentials
echo
echo "🔧 Step 5: Generating Service Account Credentials..."
gcloud iam service-accounts keys create $CREDENTIALS_FILE \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

print_status "Credentials saved to: $CREDENTIALS_FILE"

# Step 7: Update Environment File
echo
echo "🔧 Step 6: Updating Environment Configuration..."
cat >> .env << EOF

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_APPLICATION_CREDENTIALS=$CREDENTIALS_FILE
VERTEX_AI_LOCATION=us-central1
AGDK_PROJECT_ID=$PROJECT_ID

# Feature Flags
ANALYSIS_USE_AGDK=true
EOF

print_status "Environment variables added to .env"

# Step 8: Install Python Dependencies
echo
echo "🔧 Step 7: Installing Python Dependencies..."
if command -v poetry &> /dev/null; then
    echo "   Using Poetry to install dependencies..."
    poetry install
    print_status "Dependencies installed via Poetry"
else
    echo "   Poetry not found, using pip..."
    pip install google-cloud-aiplatform google-cloud-discoveryengine google-cloud-dialogflow
    print_status "Python client libraries installed via pip"
fi

# Step 9: Test Connection
echo
echo "🔧 Step 8: Testing Connection..."
python3 -c "
import os
from google.cloud import aiplatform

project_id = '$PROJECT_ID'
location = 'us-central1'

try:
    aiplatform.init(project=project_id, location=location)
    print('✅ Vertex AI connection successful')
    print(f'✅ Project: {project_id}')
    print(f'✅ Location: {location}')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    exit(1)
"

# Step 10: Update .gitignore
echo
echo "🔧 Step 9: Updating .gitignore..."
if [ ! -f .gitignore ]; then
    touch .gitignore
fi

# Add to .gitignore if not already present
grep -qxF "credentials/" .gitignore || echo "credentials/" >> .gitignore
grep -qxF ".env" .gitignore || echo ".env" >> .gitignore

print_status ".gitignore updated"

echo
echo "🎉 Google Cloud Setup Complete!"
echo
echo "📋 Summary:"
echo "   ✅ Project: $PROJECT_ID"
echo "   ✅ Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "   ✅ Credentials: $CREDENTIALS_FILE"
echo "   ✅ APIs Enabled: Vertex AI, Discovery Engine, Dialogflow"
echo "   ✅ Environment: .env updated"
echo
echo "🔄 Next Steps:"
echo "   1. Review the credentials file: $CREDENTIALS_FILE"
echo "   2. Proceed with AGDK Module Structure implementation"
echo "   3. Start building the agent framework"
echo
print_warning "Important: Keep your credentials secure and never commit them to version control!"