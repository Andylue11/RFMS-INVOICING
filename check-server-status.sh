#!/bin/bash
# Check server status - Run this from your local machine

echo "=========================================="
echo "Checking RFMS-Uploader Server Status"
echo "=========================================="
echo ""

ssh atoz@AtozServer << 'ENDSSH'
cd /volume1/docker/rfms-uploader

echo "=== Git Status ==="
git status
echo ""

echo "=== Current Branch ==="
git branch --show-current
echo ""

echo "=== Last Commit ==="
git log -1 --oneline
echo ""

echo "=== Remote URL ==="
git remote -v
echo ""

echo "=== Container Status ==="
docker-compose ps
echo ""

echo "=== Container Health ==="
docker ps --filter "name=rfms-uploader" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "=== Recent Logs (last 30 lines) ==="
docker-compose logs --tail=30
echo ""

echo "=== Check if app is responding ==="
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5007 | grep -q "200\|302\|301"; then
    echo "✅ Application is responding on port 5007"
else
    echo "⚠️  Application may not be responding yet"
fi
echo ""

echo "=== Disk Space ==="
df -h /volume1/docker/rfms-uploader | tail -1
echo ""

ENDSSH

echo "=========================================="
echo "Status Check Complete"
echo "=========================================="

