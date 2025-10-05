# Google Cloud Project Setup Guide
# Complete setup for AI Code Review Multi-Agent System with GADK Integration

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Google Cloud Project Creation](#google-cloud-project-creation)
3. [Enable Required APIs](#enable-required-apis)
4. [Service Account Setup](#service-account-setup)
5. [GADK Configuration](#gadk-configuration)
6. [Vertex AI Setup](#vertex-ai-setup)
7. [Discovery Engine Setup](#discovery-engine-setup)
8. [Dialogflow Setup](#dialogflow-setup)
9. [Environment Configuration](#environment-configuration)
10. [Testing Setup](#testing-setup)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- Google Cloud CLI (`gcloud`)
- Docker and Docker Compose
- Python 3.11+
- Git

### Install Google Cloud CLI
```bash
# macOS (using Homebrew)
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

### Verify Installation
```bash
gcloud version
```

## Google Cloud Project Creation

### 1. Create New Project
```bash
# Set your project ID (must be globally unique)
export PROJECT_ID="ai-code-review-$(date +%s)"

# Create the project
gcloud projects create $PROJECT_ID \
    --name="AI Code Review Multi-Agent" \
    --labels="environment=development,type=ai-agents"

# Set as default project
gcloud config set project $PROJECT_ID

# Verify project creation
gcloud projects describe $PROJECT_ID
```

### 2. Enable Billing (Required for GADK)
```bash
# List available billing accounts
gcloud billing accounts list

# Link billing account to project (replace BILLING_ACCOUNT_ID)
gcloud billing projects link $PROJECT_ID \
    --billing-account=BILLING_ACCOUNT_ID
```

## Enable Required APIs

### Core APIs for GADK Integration
```bash
# Enable all required APIs
gcloud services enable \
    aiplatform.googleapis.com \
    discoveryengine.googleapis.com \
    dialogflow.googleapis.com \
    cloudbuild.googleapis.com \
    container.googleapis.com \
    compute.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com

# Verify enabled services
gcloud services list --enabled
```

### Wait for API Propagation
```bash
# Wait for APIs to be fully enabled (can take 2-5 minutes)
echo "Waiting for APIs to propagate..."
sleep 120
```

## Service Account Setup

### 1. Create Service Account
```bash
# Create service account for the application
gcloud iam service-accounts create ai-code-review-gadk \
    --display-name="AI Code Review GADK Service Account" \
    --description="Service account for AI Code Review Multi-Agent System with GADK"

# Get service account email
export SERVICE_ACCOUNT_EMAIL="ai-code-review-gadk@${PROJECT_ID}.iam.gserviceaccount.com"
```

### 2. Assign Required Roles
```bash
# AI Platform roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/aiplatform.admin"

# Discovery Engine roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/discoveryengine.admin"

# Dialogflow roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/dialogflow.admin"

# Storage and logging roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/logging.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/monitoring.admin"

# Secret Manager access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.admin"
```

### 3. Create and Download Service Account Key
```bash
# Create credentials directory
mkdir -p credentials

# Generate service account key
gcloud iam service-accounts keys create credentials/google-cloud-credentials.json \
    --iam-account="${SERVICE_ACCOUNT_EMAIL}"

# Verify key creation
ls -la credentials/google-cloud-credentials.json
```

## GADK Configuration

### 1. Set Default Location
```bash
# Set default region for AI services
export LOCATION="us-central1"
gcloud config set ai/region $LOCATION
```

### 2. Create GADK Resources

#### Create Cloud Storage Bucket for GADK
```bash
# Create bucket for GADK data
export BUCKET_NAME="${PROJECT_ID}-gadk-data"
gsutil mb -p $PROJECT_ID -c STANDARD -l $LOCATION gs://$BUCKET_NAME

# Set bucket permissions
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT_EMAIL}:roles/storage.admin gs://$BUCKET_NAME
```

## Vertex AI Setup

### 1. Initialize Vertex AI
```bash
# Initialize Vertex AI in the project
gcloud ai-platform models list --region=$LOCATION

# Create Vertex AI endpoint (if needed)
# This will be done programmatically by the application
```

### 2. Test Vertex AI Access
```bash
# Test Vertex AI API access
gcloud ai models list --region=$LOCATION
```

## Discovery Engine Setup

### 1. Create Discovery Engine App
```bash
# Create Discovery Engine application
gcloud alpha discovery-engine apps create ai-code-review-app \
    --location=global \
    --industry-vertical=GENERIC

# List Discovery Engine apps to verify
gcloud alpha discovery-engine apps list --location=global
```

### 2. Create Data Store
```bash
# Create data store for code analysis
gcloud alpha discovery-engine data-stores create code-analysis-store \
    --location=global \
    --industry-vertical=GENERIC \
    --content-config=CONTENT_REQUIRED \
    --solution-types=SOLUTION_TYPE_SEARCH
```

## Dialogflow Setup

### 1. Create Dialogflow CX Agent
```bash
# Create Dialogflow CX agent
gcloud alpha dialogflow cx agents create \
    --display-name="AI Code Review Agent" \
    --description="Agent for AI Code Review interactions" \
    --default-language-code="en" \
    --time-zone="America/New_York" \
    --location=global
```

### 2. List Agents to Get Agent ID
```bash
# List agents to get the agent ID
gcloud alpha dialogflow cx agents list --location=global
```

## Environment Configuration

### 1. Update .env File
```bash
# Update your .env file with the project details
cat >> .env << EOF

# Updated Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID
GOOGLE_CLOUD_LOCATION=$LOCATION
GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-cloud-credentials.json

# GADK Configuration
GADK_PROJECT_ID=$PROJECT_ID
GADK_BUCKET=$BUCKET_NAME

# Service Account
SERVICE_ACCOUNT_EMAIL=$SERVICE_ACCOUNT_EMAIL

# Vertex AI Configuration
VERTEX_AI_LOCATION=$LOCATION

# Discovery Engine Configuration
AGENT_BUILDER_LOCATION=global

# Dialogflow Configuration
DIALOGFLOW_LOCATION=global
EOF
```

### 2. Set Environment Variables
```bash
# Export for current session
export GOOGLE_CLOUD_PROJECT_ID=$PROJECT_ID
export GOOGLE_APPLICATION_CREDENTIALS="./credentials/google-cloud-credentials.json"
```

## Testing Setup

### 1. Test Authentication
```bash
# Test service account authentication
gcloud auth activate-service-account --key-file=credentials/google-cloud-credentials.json

# Test API access
gcloud ai models list --region=$LOCATION
```

### 2. Test GADK Integration
```bash
# Test with Python (requires google-cloud-aiplatform)
python3 -c "
from google.cloud import aiplatform
aiplatform.init(project='$PROJECT_ID', location='$LOCATION')
print('✅ Vertex AI connection successful')
"
```

### 3. Start Development Environment
```bash
# Start the development environment
./scripts/dev-setup.sh up development

# Check service status
./scripts/dev-setup.sh status
```

## Security Best Practices

### 1. Secure Credentials
```bash
# Add credentials to .gitignore
echo "credentials/" >> .gitignore
echo ".env" >> .gitignore

# Set proper file permissions
chmod 600 credentials/google-cloud-credentials.json
chmod 600 .env
```

### 2. Use Secret Manager (Production)
```bash
# Store sensitive data in Secret Manager
gcloud secrets create gadk-config --data-file=.env

# Grant access to service account
gcloud secrets add-iam-policy-binding gadk-config \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"
```

## Monitoring and Logging

### 1. Enable Cloud Logging
```bash
# Create log sink for application logs
gcloud logging sinks create ai-code-review-sink \
    storage.googleapis.com/$BUCKET_NAME/logs \
    --log-filter='resource.type="gce_instance" AND logName:"ai-code-review"'
```

### 2. Set Up Monitoring
```bash
# Create notification channel (replace EMAIL)
gcloud alpha monitoring channels create \
    --display-name="AI Code Review Alerts" \
    --type=email \
    --channel-labels=email_address=YOUR_EMAIL@example.com
```

## Cost Management

### 1. Set Budget Alerts
```bash
# Create budget (replace BILLING_ACCOUNT_ID and amount)
gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="AI Code Review Budget" \
    --budget-amount=100USD \
    --threshold-rules-percent=50,80,100
```

### 2. Resource Quotas
```bash
# Check current quotas
gcloud compute project-info describe --project=$PROJECT_ID
```

## Cleanup (When Needed)

### Remove Resources
```bash
# Delete service account key
gcloud iam service-accounts keys delete KEY_ID \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

# Delete service account
gcloud iam service-accounts delete $SERVICE_ACCOUNT_EMAIL

# Delete project (WARNING: This removes everything)
# gcloud projects delete $PROJECT_ID
```

## Troubleshooting

### Common Issues

#### 1. API Not Enabled
```bash
# Check if specific API is enabled
gcloud services list --enabled --filter="name:aiplatform.googleapis.com"

# Enable missing API
gcloud services enable aiplatform.googleapis.com
```

#### 2. Permission Denied
```bash
# Check service account roles
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:$SERVICE_ACCOUNT_EMAIL"
```

#### 3. Authentication Issues
```bash
# Verify credentials file
cat credentials/google-cloud-credentials.json | jq .

# Test authentication
gcloud auth list
```

#### 4. Quota Exceeded
```bash
# Check quotas
gcloud compute project-info describe --project=$PROJECT_ID

# Request quota increase through Cloud Console
```

### Support Resources

- [Google Cloud GADK Documentation](https://cloud.google.com/gadk)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Discovery Engine Documentation](https://cloud.google.com/discovery-engine/docs)
- [Dialogflow CX Documentation](https://cloud.google.com/dialogflow/cx/docs)

## Next Steps

After completing this setup:

1. ✅ **Test the infrastructure**: `./scripts/dev-setup.sh up development`
2. ✅ **Verify GADK integration**: Check BaseAgent GADK methods
3. ✅ **Run sample analysis**: Test the complete pipeline
4. ✅ **Monitor performance**: Use Grafana dashboards
5. ✅ **Scale as needed**: Adjust quotas and resources

---

**📧 Need Help?** If you encounter issues, check the troubleshooting section or refer to Google Cloud documentation.

**💡 Pro Tip**: Keep your project ID and service account email handy - you'll need them for environment configuration.