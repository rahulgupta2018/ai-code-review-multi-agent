# Google Cloud Setup for Agentic Code Review

This directory contains the setup and configuration for integrating with Google Cloud's Vertex AI Agent Builder (formerly GADK).

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Run the automated setup script
./scripts/setup_google_cloud.sh
```

### Option 2: Manual Setup
Follow the detailed guide in [`docs/google_cloud_setup.md`](../docs/google_cloud_setup.md)

## 🔧 What Gets Set Up

1. **Google Cloud Project**: New project with unique ID
2. **APIs Enabled**:
   - Vertex AI API (for AI agents)
   - Discovery Engine API (for Agent Builder)
   - Dialogflow API (for Conversational Agents)
   - Cloud Build API (for deployment)
   - Artifact Registry API (for containers)

3. **Service Account**: With appropriate permissions
4. **Credentials**: JSON key file for authentication
5. **Environment**: Configuration in `.env` file

## 📁 Files Created

```
credentials/
├── google-cloud-credentials.json    # Service account key (DO NOT COMMIT)
└── .gitkeep

.env                                 # Environment variables (DO NOT COMMIT)
```

## 🔍 Verification

After setup, verify your configuration:

```bash
# Run verification script
python scripts/verify_google_cloud.py

# Or manual verification
python -c "
from google.cloud import aiplatform
import os
aiplatform.init(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
print('✅ Google Cloud setup successful!')
"
```

## 🌐 Google Cloud Services Used

### Vertex AI Agents
- **Purpose**: AI agent development and orchestration
- **Usage**: Building intelligent code review agents
- **Cost**: Pay-per-use, free tier available

### Discovery Engine (Agent Builder)
- **Purpose**: Search and recommendation capabilities
- **Usage**: Code pattern discovery and recommendations  
- **Cost**: Free tier: 1K searches/month

### Dialogflow CX (Conversational Agents)
- **Purpose**: Conversational AI and natural language processing
- **Usage**: Interactive code review conversations
- **Cost**: Free tier: 1K requests/month

## 💰 Cost Management

### Free Tier Limits
- **$300 credit** for new accounts (90 days)
- **Vertex AI**: Free tier available for many operations
- **Discovery Engine**: 1K searches/month free
- **Dialogflow**: 1K requests/month free

### Cost Optimization
```bash
# Monitor usage
gcloud logging read "resource.type=gce_instance" --limit=10

# Set up billing alerts
gcloud alpha billing budgets create \
    --billing-account=YOUR_BILLING_ACCOUNT \
    --display-name="Agentic Code Review Budget" \
    --budget-amount=50USD
```

## 🔒 Security Best Practices

### Credentials Security
```bash
# Never commit credentials
echo "credentials/" >> .gitignore
echo ".env" >> .gitignore

# Restrict file permissions
chmod 600 credentials/google-cloud-credentials.json
```

### IAM Best Practices
- Use principle of least privilege
- Rotate service account keys regularly
- Monitor access logs
- Use separate accounts for dev/prod

### Environment Isolation
```bash
# Development
export GOOGLE_CLOUD_PROJECT=agentic-code-review-dev

# Production  
export GOOGLE_CLOUD_PROJECT=agentic-code-review-prod
```

## 🛠️ Troubleshooting

### Common Issues

#### Authentication Errors
```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Check credentials
gcloud auth list
```

#### API Not Enabled
```bash
# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable discoveryengine.googleapis.com
```

#### Permission Denied
```bash
# Check IAM roles
gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT

# Add missing role
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
    --role="roles/aiplatform.user"
```

#### Billing Issues
- Ensure billing is enabled in [Google Cloud Console](https://console.cloud.google.com/billing)
- Check billing account is linked to your project

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

# Check quotas
gcloud compute project-info describe --project=$GOOGLE_CLOUD_PROJECT
```

## 📚 Next Steps

After successful setup:

1. ✅ **Verify** connection with `python scripts/verify_google_cloud.py`
2. 🔄 **Proceed** to GADK Module Structure implementation
3. 🏗️ **Build** the agent framework integration
4. 🚀 **Deploy** your first agent

## 📖 Additional Resources

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Agent Builder Guide](https://cloud.google.com/generative-ai-app-builder/docs)
- [Dialogflow CX Documentation](https://cloud.google.com/dialogflow/cx/docs)
- [Google Cloud Free Tier](https://cloud.google.com/free)

## 🆘 Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review [Google Cloud Documentation](https://cloud.google.com/docs)
3. Check [Google Cloud Status](https://status.cloud.google.com/)
4. Visit [Google Cloud Community](https://cloud.google.com/community)

---

**⚠️ Important**: Always keep your credentials secure and never commit them to version control!