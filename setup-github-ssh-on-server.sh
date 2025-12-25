#!/bin/bash
# Setup GitHub SSH on the office server
# This adds GitHub to known_hosts and verifies SSH access

echo "=========================================="
echo "Setting up GitHub SSH on Server"
echo "=========================================="
echo ""

ssh atoz@AtozServer << 'ENDSSH'
# Add GitHub to known_hosts
echo "Adding GitHub to known_hosts..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh
ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null
chmod 600 ~/.ssh/known_hosts

echo "✅ GitHub added to known_hosts"

# Test connection
echo ""
echo "Testing GitHub SSH connection..."
ssh -T git@github.com 2>&1 | head -1

echo ""
echo "If you see 'Hi [username]!', SSH is working!"
echo "If you see 'Permission denied', you need to add your SSH key to GitHub"
ENDSSH

