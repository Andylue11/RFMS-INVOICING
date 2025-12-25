#!/bin/bash
# Complete update script with GitHub SSH setup

echo "=========================================="
echo "RFMS-Uploader Server Update (Fixed)"
echo "=========================================="
echo ""

ssh atoz@AtozServer << 'ENDSSH'
cd /volume1/docker/rfms-uploader

# Step 1: Setup GitHub SSH
echo "[1/6] Setting up GitHub SSH..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh
ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null
chmod 600 ~/.ssh/known_hosts
echo "✅ GitHub SSH configured"

# Step 2: Update git remote to SSH
echo ""
echo "[2/6] Updating git remote to SSH..."
git remote set-url origin git@github.com:Andylue11/RFMS-UPLOADER.git
echo "✅ Remote updated"

# Step 3: Pull latest code
echo ""
echo "[3/6] Pulling latest code from main..."
git fetch origin
git checkout main
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Git pull failed!"
    echo "This might mean:"
    echo "  1. SSH key not added to GitHub, OR"
    echo "  2. Need to use HTTPS with token instead"
    echo ""
    echo "Trying HTTPS method as fallback..."
    git remote set-url origin https://github.com/Andylue11/RFMS-UPLOADER.git
    git pull origin main
    if [ $? -ne 0 ]; then
        echo "❌ Both methods failed. Please check git access."
        exit 1
    fi
fi

echo ""
echo "[4/6] Stopping container..."
docker-compose down

echo ""
echo "[5/6] Rebuilding container (this may take a few minutes)..."
docker-compose build --no-cache

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "[6/6] Starting container..."
docker-compose up -d

echo ""
echo "Checking status..."
sleep 10
docker-compose ps

echo ""
echo "Recent logs:"
docker-compose logs --tail=30

echo ""
echo "=========================================="
echo "✅ Update Complete!"
echo "=========================================="
ENDSSH

