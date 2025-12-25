#!/bin/bash
# Fix SSH directory on Synology NAS
# Run this on your NAS via SSH

echo "Creating .ssh directory..."

# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh

# Set proper permissions
chmod 700 ~/.ssh

# Create the SSH key if directory now exists
if [ -d ~/.ssh ]; then
    echo "✅ .ssh directory created successfully!"
    echo ""
    echo "Now generating SSH key..."
    ssh-keygen -t ed25519 -C "nas@synology" -f ~/.ssh/id_ed25519 -N ""
    
    echo ""
    echo "✅ SSH key generated!"
    echo ""
    echo "📋 Copy this public key and add it to GitHub:"
    echo "=========================================="
    cat ~/.ssh/id_ed25519.pub
    echo "=========================================="
    echo ""
    echo "1. Go to: https://github.com/settings/ssh/new"
    echo "2. Paste the key above"
    echo "3. Give it a title (e.g., 'Synology NAS')"
    echo "4. Click 'Add SSH key'"
    echo ""
else
    echo "❌ Failed to create .ssh directory"
    echo "Try running: sudo mkdir -p ~/.ssh && sudo chmod 700 ~/.ssh && sudo chown $USER:$USER ~/.ssh"
fi

