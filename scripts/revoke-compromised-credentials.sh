#!/bin/bash
#
# EMERGENCY: Revoke compromised Google Cloud credentials
# This script helps revoke the exposed service account key
#

echo "🚨 EMERGENCY: Revoking compromised Google Cloud credentials"
echo ""
echo "The following steps will help secure your Google Cloud account:"
echo ""

# Extract project ID from the exposed credentials
PROJECT_ID="ai-code-review--78723-335"
PRIVATE_KEY_ID="cc5762d28cc05730092ff1cc39ef9818d19e86ef"

echo "📋 Detected compromised credentials:"
echo "   Project ID: $PROJECT_ID"
echo "   Private Key ID: $PRIVATE_KEY_ID"
echo ""

echo "🔧 IMMEDIATE ACTIONS REQUIRED:"
echo ""
echo "1. 🚨 REVOKE THE SERVICE ACCOUNT KEY (CRITICAL):"
echo "   gcloud iam service-accounts keys delete $PRIVATE_KEY_ID \\"
echo "     --iam-account=SERVICE_ACCOUNT_EMAIL@$PROJECT_ID.iam.gserviceaccount.com"
echo ""
echo "2. 🔍 LIST ALL KEYS FOR YOUR SERVICE ACCOUNT:"
echo "   gcloud iam service-accounts keys list \\"
echo "     --iam-account=SERVICE_ACCOUNT_EMAIL@$PROJECT_ID.iam.gserviceaccount.com"
echo ""
echo "3. 🆕 CREATE NEW SERVICE ACCOUNT KEY:"
echo "   gcloud iam service-accounts keys create infra/credentials/google-cloud-credentials.json \\"
echo "     --iam-account=SERVICE_ACCOUNT_EMAIL@$PROJECT_ID.iam.gserviceaccount.com"
echo ""
echo "4. 🔒 SET PROPER PERMISSIONS:"
echo "   chmod 600 infra/credentials/google-cloud-credentials.json"
echo ""

echo "⚠️  Note: Replace 'SERVICE_ACCOUNT_EMAIL' with your actual service account email"
echo "🔍 Find it with: gcloud iam service-accounts list --project=$PROJECT_ID"
echo ""

read -p "Do you want to list service accounts for project $PROJECT_ID? (y/n): " list_accounts
if [ "$list_accounts" = "y" ]; then
    echo "📋 Service accounts in project $PROJECT_ID:"
    gcloud iam service-accounts list --project=$PROJECT_ID 2>/dev/null || echo "❌ Failed to list service accounts. Make sure you're authenticated with gcloud."
fi

echo ""
echo "📚 Additional security steps:"
echo "1. Check Google Cloud Console audit logs for any unauthorized access"
echo "2. Review billing for unexpected charges"
echo "3. Consider rotating any other keys/passwords that might be affected"
echo "4. Review IAM permissions on the service account"
echo ""
echo "🔗 Google Cloud Console: https://console.cloud.google.com/iam-admin/serviceaccounts?project=$PROJECT_ID"