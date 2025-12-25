#!/bin/bash
# Update server using git - Fixed for Synology
# Usage: ./update-server-git-fixed.sh

SERVER="atoz@192.168.0.201"
REMOTE_DIR="/volume1/docker/rfms-uploader"

echo "=========================================="
echo "Updating RFMS-Uploader on server via Git"
echo "=========================================="
echo ""

# Pull latest changes
echo "[1/3] Pulling latest changes from git..."
ssh $SERVER "cd $REMOTE_DIR && git pull"
if [ $? -ne 0 ]; then
    echo "ERROR: Git pull failed"
    exit 1
fi

# Rebuild container using docker-compose (Synology uses docker-compose, not docker compose)
echo ""
echo "[2/3] Rebuilding container..."
ssh $SERVER "cd $REMOTE_DIR && docker-compose down && docker-compose build --no-cache && docker-compose up -d"
if [ $? -ne 0 ]; then
    echo "ERROR: Container rebuild failed"
    exit 1
fi

# Verify
echo ""
echo "[3/3] Verifying deployment..."
sleep 5
ssh $SERVER "cd $REMOTE_DIR && docker-compose ps && echo '' && docker-compose logs --tail=20"

echo ""
echo "=========================================="
echo "Update Complete!"
echo "=========================================="

