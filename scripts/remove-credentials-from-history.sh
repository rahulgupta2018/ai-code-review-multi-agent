#!/bin/bash
# 
# CRITICAL: Remove credentials from git history
# WARNING: This rewrites git history and cannot be undone!
#
# Usage: ./scripts/remove-credentials-from-history.sh
#

set -e

echo "🚨 WARNING: This script will rewrite git history!"
echo "📋 This will remove 'infra/credentials/google-cloud-credentials.json' from ALL commits"
echo "⚠️  This action cannot be undone!"
echo ""
echo "🔍 Current git status:"
git status --short

echo ""
read -p "Are you sure you want to proceed? (type 'YES' to continue): " confirm

if [ "$confirm" != "YES" ]; then
    echo "❌ Operation cancelled"
    exit 1
fi

echo ""
echo "🏃 Creating backup branch..."
git checkout -b backup-before-credential-removal

echo "🔄 Switching back to main..."
git checkout main

echo "🧹 Removing credentials from git history..."
git filter-branch --force --index-filter \
    'git rm --cached --ignore-unmatch infra/credentials/google-cloud-credentials.json' \
    --prune-empty --tag-name-filter cat -- --all

echo "🗑️  Cleaning up refs..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "✅ Credentials file removed from git history!"
echo "🔍 Verifying removal..."
if git log --oneline --follow -- infra/credentials/google-cloud-credentials.json | wc -l | grep -q "0"; then
    echo "✅ SUCCESS: File completely removed from history"
else
    echo "⚠️  WARNING: File may still exist in some commits"
    git log --oneline --follow -- infra/credentials/google-cloud-credentials.json
fi

echo ""
echo "📋 Next steps:"
echo "1. Verify the file is gone: git log --follow -- infra/credentials/google-cloud-credentials.json"
echo "2. Push changes: git push --force-with-lease origin main"
echo "3. Delete backup branch: git branch -D backup-before-credential-removal"
echo ""
echo "⚠️  Note: Collaborators will need to rebase their work after this change!"