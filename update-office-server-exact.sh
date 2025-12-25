#!/bin/bash
# Exact update command for RFMS-Uploader on office server
# Path: /volume1/docker/rfms-uploader

echo "=========================================="
echo "Updating RFMS-Uploader Container"
echo "Path: /volume1/docker/rfms-uploader"
echo "=========================================="
echo ""

ssh atoz@AtozServer << 'ENDSSH'
cd /volume1/docker/rfms-uploader

echo "[1/5] Pulling latest code from git..."
git fetch origin
git checkout stock-recv
git pull origin stock-recv

echo ""
echo "[2/5] Stopping container..."
docker-compose down

echo ""
echo "[3/5] Rebuilding container (this may take a few minutes)..."
docker-compose build --no-cache

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
echo "Container should be running on port 5007"
echo "Check logs: docker-compose logs -f"
ENDSSH

