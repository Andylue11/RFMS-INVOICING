#!/bin/bash
# Update server - First fixes git remote, then updates container

echo "=========================================="
echo "RFMS-Uploader Server Update"
echo "=========================================="
echo ""

ssh atoz@AtozServer << 'ENDSSH'
cd /volume1/docker/rfms-uploader

# Check and fix git remote if needed
CURRENT_REMOTE=$(git remote get-url origin)
if [[ "$CURRENT_REMOTE" == *"https://github.com"* ]]; then
    echo "⚠️  Git remote is using HTTPS, switching to SSH..."
    git remote set-url origin git@github.com:Andylue11/RFMS-UPLOADER.git
    echo "✅ Remote updated to SSH"
fi

echo ""
echo "[1/5] Pulling latest code from git..."
git fetch origin
git checkout main
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ Git pull failed. Trying alternative method..."
    echo "If SSH keys aren't set up, you may need to:"
    echo "1. Set up SSH keys on the server, OR"
    echo "2. Use a personal access token with HTTPS"
    exit 1
fi

echo ""
echo "[2/5] Stopping container..."
docker-compose down

echo ""
echo "[3/5] Rebuilding container (this may take a few minutes)..."
docker-compose build --no-cache

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "[4/5] Starting container..."
docker-compose up -d

echo ""
echo "[5/5] Checking status..."
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

