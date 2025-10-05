# Google Cloud Setup Guide for Vertex AI Agents

## Overview
This guide walks through setting up Google Cloud for Vertex AI Agent Builder integration with the agentic code review system.

## Step 1: Create Google Cloud Project

### 1.1 Sign up for Google Cloud (if needed)
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Sign in with your Google account
- Accept terms and activate $300 free credit

### 1.2 Create New Project
```bash
# Option 1: Via Console
1. Go to https://console.cloud.google.com/projectcreate
2. Project name: "agentic-code-review"
3. Project ID: "agentic-code-review-[unique-suffix]"
4. Click "Create"

# Option 2: Via CLI (after installing gcloud)
gcloud projects create agentic-code-review-$(date +%s) \
    --name="Agentic Code Review" \
    --set-as-default
```

### 1.3 Enable Billing
- Go to [Billing](https://console.cloud.google.com/billing)
- Link your project to billing account
- Note: Free tier includes $300 credit

## Step 2: Enable Required APIs

### 2.1 Enable Vertex AI APIs
```bash
# Via CLI
gcloud services enable \
    aiplatform.googleapis.com \
    discoveryengine.googleapis.com \
    dialogflow.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com

# Via Console
# Go to APIs & Services > Library
# Search and enable:
# - Vertex AI API
# - Discovery Engine API  
# - Dialogflow API
# - Cloud Build API
# - Artifact Registry API
```

### 2.2 Verify APIs are Enabled
```bash
gcloud services list --enabled --filter="name:aiplatform OR name:discoveryengine"
```

## Step 3: Create Service Account

### 3.1 Create Service Account
```bash
# Create service account
gcloud iam service-accounts create agentic-code-review \
    --display-name="Agentic Code Review Service Account" \
    --description="Service account for Vertex AI Agent Builder integration"

# Get the email
export SERVICE_ACCOUNT_EMAIL=$(gcloud iam service-accounts list \
    --filter="displayName:Agentic Code Review Service Account" \
    --format="value(email)")

echo "Service Account Email: $SERVICE_ACCOUNT_EMAIL"
```

### 3.2 Grant Required Permissions
```bash
# Vertex AI User (for Vertex AI Agents)
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/aiplatform.user"

# Discovery Engine Admin (for Agent Builder)
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/discoveryengine.admin"

# Dialogflow API Admin (for Conversational Agents)
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/dialogflow.admin"
```

### 3.3 Generate Credentials JSON
```bash
# Generate and download credentials
gcloud iam service-accounts keys create ./credentials/google-cloud-credentials.json \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials/google-cloud-credentials.json"
```

## Step 4: Test Connection

### 4.1 Install Google Cloud SDK
```bash
# Install Python client libraries
pip install google-cloud-aiplatform google-cloud-discoveryengine google-cloud-dialogflow

# Verify installation
python -c "from google.cloud import aiplatform; print('Vertex AI client imported successfully')"
```

### 4.2 Test Authentication
```bash
# Test with gcloud
gcloud auth application-default login
gcloud projects describe $(gcloud config get-value project)

# Test with Python
python -c "
from google.cloud import aiplatform
aiplatform.init(project='$(gcloud config get-value project)')
print('Vertex AI initialized successfully')
"
```

## Step 5: Project Configuration

### 5.1 Set Environment Variables
```bash
# Add to .env file
echo "GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)" >> .env
echo "GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-cloud-credentials.json" >> .env
echo "VERTEX_AI_LOCATION=us-central1" >> .env
```

### 5.2 Verify Setup
```bash
# Quick verification script
python -c "
import os
from google.cloud import aiplatform

project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
location = os.getenv('VERTEX_AI_LOCATION', 'us-central1')

aiplatform.init(project=project_id, location=location)
print(f'✅ Connected to project: {project_id}')
print(f'✅ Location: {location}')
print('🎉 Google Cloud setup complete!')
"
```

## Step 6: Security Best Practices

### 6.1 Secure Credentials
```bash
# Create credentials directory
mkdir -p credentials/
chmod 700 credentials/

# Add to .gitignore
echo "credentials/" >> .gitignore
echo ".env" >> .gitignore
```

### 6.2 Principle of Least Privilege
- Review and minimize IAM permissions
- Use separate service accounts for different environments
- Rotate credentials regularly

## Next Steps

1. ✅ Google Cloud Project Created
2. ✅ Vertex AI APIs Enabled  
3. ✅ Service Account Configured
4. ✅ Credentials Generated
5. 🔄 Ready for AGDK Module Structure Implementation

## Troubleshooting

### Common Issues
```bash
# Permission denied
gcloud auth login
gcloud auth application-default login

# API not enabled
gcloud services enable aiplatform.googleapis.com

# Billing not enabled
# Go to console.cloud.google.com/billing
```

### Useful Commands
```bash
# List projects
gcloud projects list

# Set active project
gcloud config set project PROJECT_ID

# List enabled APIs
gcloud services list --enabled

# List service accounts
gcloud iam service-accounts list
```