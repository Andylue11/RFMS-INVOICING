#!/bin/bash
# Setup SSH key for Git on Synology NAS
# Run this on your NAS

set -e

echo "Setting up SSH for Git on Synology NAS..."
echo ""

# Try to create home directory if it doesn't exist
if [ ! -d "/var/services/homes/atoz" ]; then
    echo "Creating home directory..."
    sudo mkdir -p /var/services/homes/atoz
    sudo chown atoz:users /var/services/homes/atoz
    sudo chmod 755 /var/services/homes/atoz
fi

# Try to create .ssh in home directory
if [ ! -d ~/.ssh ]; then
    echo "Creating .ssh directory in home..."
    mkdir -p ~/.ssh 2>/dev/null || sudo mkdir -p ~/.ssh && sudo chown $USER:$USER ~/.ssh
    chmod 700 ~/.ssh 2>/dev/null || sudo chmod 700 ~/.ssh
fi

# Alternative: Use application directory if home doesn't work
APP_DIR="/volume1/docker/pdf-extractor"
SSH_DIR="$APP_DIR/.ssh"

if [ ! -d ~/.ssh ] || [ ! -w ~/.ssh ]; then
    echo "Using application directory for SSH key..."
    mkdir -p "$SSH_DIR"
    chmod 700 "$SSH_DIR"
    SSH_KEY_PATH="$SSH_DIR/id_ed25519"
    
    # Set SSH config to use this key
    mkdir -p ~/.ssh 2>/dev/null || true
    cat > ~/.ssh/config << EOF
Host github.com
    HostName github.com
    User git
    IdentityFile $SSH_KEY_PATH
    IdentitiesOnly yes
EOF
    chmod 600 ~/.ssh/config 2>/dev/null || true
else
    SSH_KEY_PATH=~/.ssh/id_ed25519
fi

# Generate SSH key if it doesn't exist
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "Generating SSH key..."
    ssh-keygen -t ed25519 -C "nas@synology" -f "$SSH_KEY_PATH" -N ""
    echo "✅ SSH key generated at: $SSH_KEY_PATH"
else
    echo "✅ SSH key already exists at: $SSH_KEY_PATH"
fi

echo ""
echo "=========================================="
echo "📋 Copy this public key to GitHub:"
echo "=========================================="
cat "${SSH_KEY_PATH}.pub"
echo "=========================================="
echo ""
echo "1. Go to: https://github.com/settings/ssh/new"
echo "2. Paste the key above"
echo "3. Title it: 'Synology NAS'"
echo "4. Click 'Add SSH key'"
echo ""
echo "After adding the key, test with:"
echo "  ssh -T git@github.com"
echo ""

