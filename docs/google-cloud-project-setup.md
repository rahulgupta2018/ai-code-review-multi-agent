# Google Cloud Project Setup Guide

This guide explains how to use the configurable Google Cloud project setup script for the AI Code Review Multi-Agent System.

## Quick Start

### 1. Prerequisites

Before running the setup script, ensure you have:

- **Google Cloud CLI (gcloud)** installed: https://cloud.google.com/sdk/docs/install
- **yq** for YAML parsing: `brew install yq`
- **jq** for JSON parsing: `brew install jq`
- A Google account with billing enabled

### 2. Basic Setup

Create a new Google Cloud project with default settings:

```bash
./scripts/create-google-cloud-project.sh create
```

This will:
- Create a new project using `chilternwarriors.cc@gmail.com`
- Enable all required APIs for GADK integration
- Create service accounts with proper permissions
- Set up storage buckets
- Generate service account keys
- Update your `.env` file

### 3. Configuration Options

#### Change Email Account

```bash
./scripts/create-google-cloud-project.sh create -e your-email@gmail.com
```

#### Change Project Name Prefix

```bash
./scripts/create-google-cloud-project.sh create -p my-custom-project
```

#### Change Default Region

```bash
./scripts/create-google-cloud-project.sh create -r europe-west1
```

#### Specify Billing Account

```bash
./scripts/create-google-cloud-project.sh create -b 01234-56789A-BCDEFG
```

#### Dry Run (See what would happen)

```bash
./scripts/create-google-cloud-project.sh create -d
```

### 4. Configuration File

The script uses `/config/google-cloud-setup.yaml` for configuration. Key settings:

```yaml
account:
  email: "chilternwarriors.cc@gmail.com"  # Change this to your email
  
project:
  name_prefix: "ai-code-review-multi-agent"  # Change project name prefix
  
location:
  region: "us-central1"  # Change default region
  
billing:
  account_id: ""  # Auto-detected if empty
```

### 5. Available Commands

#### Create New Project
```bash
./scripts/create-google-cloud-project.sh create
```

#### Configure Existing Project
```bash
./scripts/create-google-cloud-project.sh configure -p existing-project-id
```

#### Verify Setup
```bash
./scripts/create-google-cloud-project.sh verify
```

#### List Your Projects
```bash
./scripts/create-google-cloud-project.sh list-projects
```

#### Switch to Different Project
```bash
./scripts/create-google-cloud-project.sh switch-project
```

#### Update Configuration Interactively
```bash
./scripts/create-google-cloud-project.sh update-config
```

### 6. Common Scenarios

#### Scenario 1: First Time Setup
```bash
# 1. Review and update configuration if needed
./scripts/create-google-cloud-project.sh update-config

# 2. Create project (dry run first)
./scripts/create-google-cloud-project.sh create -d

# 3. Create project for real
./scripts/create-google-cloud-project.sh create

# 4. Verify everything is working
./scripts/create-google-cloud-project.sh verify
```

#### Scenario 2: Different Email/Billing Account
```bash
# Create with different email and billing
./scripts/create-google-cloud-project.sh create \
  -e different-email@gmail.com \
  -b YOUR-BILLING-ACCOUNT-ID \
  -r europe-west1
```

#### Scenario 3: Multiple Projects for Different Environments
```bash
# Development project
./scripts/create-google-cloud-project.sh create -p ai-review-dev

# Production project  
./scripts/create-google-cloud-project.sh create -p ai-review-prod

# Staging project
./scripts/create-google-cloud-project.sh create -p ai-review-staging
```

### 7. Environment Variables

After successful setup, these variables will be added to your `.env` file:

```bash
GOOGLE_CLOUD_PROJECT_ID=your-project-id-123456-7890
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-cloud-credentials.json
GADK_ENABLED=true
GADK_PROJECT_ID=your-project-id-123456-7890
GADK_BUCKET=your-project-id-123456-7890-gadk-data
GADK_SERVICE_ACCOUNT=ai-code-review-gadk@your-project-id-123456-7890.iam.gserviceaccount.com
```

### 8. Troubleshooting

#### Authentication Issues
```bash
# Re-authenticate
gcloud auth login chilternwarriors.cc@gmail.com

# Check current account
gcloud auth list
```

#### Billing Issues
```bash
# List billing accounts
gcloud billing accounts list

# Check project billing
gcloud billing projects describe PROJECT_ID
```

#### API Issues
```bash
# Check enabled APIs
gcloud services list --enabled --project=PROJECT_ID

# Enable specific API
gcloud services enable aiplatform.googleapis.com --project=PROJECT_ID
```

#### Permission Issues
```bash
# Check IAM policy
gcloud projects get-iam-policy PROJECT_ID

# Check service account
gcloud iam service-accounts list --project=PROJECT_ID
```

### 9. Security Best Practices

1. **Service Account Keys**: The generated key file is stored in `credentials/google-cloud-credentials.json` with restricted permissions (600)

2. **IAM Roles**: Service accounts are created with minimal required permissions

3. **Project Isolation**: Each environment can have its own project for better isolation

4. **Credential Management**: Never commit credential files to version control

### 10. Integration with Development Environment

After project setup, start your development environment:

```bash
# Start all services
./scripts/dev-setup.sh up development

# Verify infrastructure
./scripts/test-infrastructure.sh

# Check service status
./scripts/dev-setup.sh status
```

## Configuration Reference

### Complete Configuration File Structure

```yaml
# Project settings
project:
  name_prefix: "ai-code-review-multi-agent"
  display_name: "AI Code Review Multi-Agent System"
  description: "Multi-agent code review system with GADK integration"

# Account settings
account:
  email: "chilternwarriors.cc@gmail.com"
  backup_email: ""

# Billing settings
billing:
  account_id: ""  # Auto-detected
  auto_enable: true
  budget_alert: 50.0

# Location settings
location:
  region: "us-central1"
  zone: "us-central1-a"
  multi_region: "US"

# Services to enable
services:
  core: [...]
  ai_ml: [...]
  storage_compute: [...]
  monitoring: [...]

# Service accounts
service_accounts:
  gadk: {...}
  compute: {...}

# Resources
resources:
  storage: {...}
  vertex_ai: {...}
```

For full configuration details, see `config/google-cloud-setup.yaml`.

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run with verbose output: `./scripts/create-google-cloud-project.sh create -v`
3. Use dry run to see what would happen: `./scripts/create-google-cloud-project.sh create -d`
4. Verify your setup: `./scripts/create-google-cloud-project.sh verify`