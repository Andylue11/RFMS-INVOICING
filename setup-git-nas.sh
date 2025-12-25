#!/bin/bash
# Setup Git on Synology NAS for PDF Extractor
# Run this script on your NAS to configure Git with SSH authentication

set -e

echo "=========================================="
echo "Git Setup for Synology NAS"
echo "=========================================="
echo ""

APP_DIR="/volume1/docker/pdf-extractor"
GITHUB_REPO="git@github.com:Andylue11/PDF-Extracr-FINAL-v2-production-draft.git"

cd "$APP_DIR"

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa ] && [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "🔑 No SSH key found. Generating one..."
    echo "Press Enter to use default location, or specify a custom path:"
    read -r ssh_key_path
    
    if [ -z "$ssh_key_path" ]; then
        ssh-keygen -t ed25519 -C "nas@synology" -f ~/.ssh/id_ed25519 -N ""
        SSH_KEY_FILE="$HOME/.ssh/id_ed25519"
    else
        ssh-keygen -t ed25519 -C "nas@synology" -f "$ssh_key_path" -N ""
        SSH_KEY_FILE="$ssh_key_path"
    fi
    
    echo ""
    echo "✅ SSH key generated!"
    echo ""
    echo "📋 Copy this public key and add it to GitHub:"
    echo "=========================================="
    cat "${SSH_KEY_FILE}.pub"
    echo "=========================================="
    echo ""
    echo "1. Go to: https://github.com/settings/ssh/new"
    echo "2. Paste the key above"
    echo "3. Give it a title (e.g., 'Synology NAS')"
    echo "4. Click 'Add SSH key'"
    echo ""
    read -p "Press Enter after adding the key to GitHub..."
else
    if [ -f ~/.ssh/id_ed25519 ]; then
        SSH_KEY_FILE="$HOME/.ssh/id_ed25519"
    else
        SSH_KEY_FILE="$HOME/.ssh/id_rsa"
    fi
    echo "✅ Using existing SSH key: $SSH_KEY_FILE"
fi

# Configure Git to use SSH
echo ""
echo "🔧 Configuring Git repository..."

if [ ! -d .git ]; then
    echo "Initializing Git repository..."
    /bin/git init
    /bin/git remote add origin "$GITHUB_REPO"
else
    echo "Updating remote URL to use SSH..."
    /bin/git remote set-url origin "$GITHUB_REPO"
fi

# Test SSH connection
echo ""
echo "🧪 Testing SSH connection to GitHub..."
if ssh -T -o StrictHostKeyChecking=no git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "✅ SSH connection successful!"
else
    echo "⚠️  SSH connection test failed. You may need to:"
    echo "   1. Add your SSH key to GitHub"
    echo "   2. Test manually: ssh -T git@github.com"
fi

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
echo "You can now use: /bin/git pull"
echo "Or use the update script from Windows"

