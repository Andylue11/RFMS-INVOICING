#!/bin/bash
# Alternative: Setup Git on Synology NAS using Personal Access Token
# Use this if you prefer HTTPS with token instead of SSH

set -e

echo "=========================================="
echo "Git Setup with Personal Access Token"
echo "=========================================="
echo ""
echo "You'll need a GitHub Personal Access Token (PAT)"
echo "Create one at: https://github.com/settings/tokens"
echo "Select scopes: repo (all)"
echo ""

APP_DIR="/volume1/docker/pdf-extractor"
GITHUB_USER="Andylue11"
GITHUB_REPO="PDF-Extracr-FINAL-v2-production-draft"
GITHUB_URL="https://${GITHUB_USER}@github.com/${GITHUB_USER}/${GITHUB_REPO}.git"

cd "$APP_DIR"

echo "Enter your GitHub Personal Access Token:"
read -s GITHUB_TOKEN

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Token is required!"
    exit 1
fi

# Configure Git repository
echo ""
echo "🔧 Configuring Git repository..."

if [ ! -d .git ]; then
    echo "Initializing Git repository..."
    /bin/git init
    /bin/git remote add origin "https://${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${GITHUB_REPO}.git"
else
    echo "Updating remote URL..."
    /bin/git remote set-url origin "https://${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${GITHUB_REPO}.git"
fi

# Store token in git credential helper (optional but more secure than URL)
/bin/git config credential.helper store
echo "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com" > ~/.git-credentials

echo ""
echo "📥 Fetching from GitHub..."
/bin/git fetch origin

echo ""
echo "🔄 Setting up main branch..."
if /bin/git show-ref --verify --quiet refs/heads/main; then
    /bin/git checkout main
else
    /bin/git checkout -b main origin/main 2>/dev/null || /bin/git checkout -b main
    /bin/git branch --set-upstream-to=origin/main main 2>/dev/null || true
fi

echo ""
echo "=========================================="
echo "✅ Git setup complete!"
echo "=========================================="
echo ""
echo "Token saved in: ~/.git-credentials"
echo "You can now use: /bin/git pull"

