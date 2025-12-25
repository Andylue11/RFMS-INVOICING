#!/bin/bash
# Script to fix server setup issues
# Run this on the server: ssh atoz@AtozServer

echo "=========================================="
echo "Fixing Server Setup"
echo "=========================================="
echo ""

cd /volume1/docker/pdf-extractor || exit 1

echo "=== Step 1: Remove .git directory ==="
if [ -d ".git" ]; then
    echo "Removing .git directory from server..."
    rm -rf .git
    echo "✓ .git directory removed"
else
    echo "✓ No .git directory found (nothing to remove)"
fi
echo ""

echo "=== Step 2: Update docker-compose-synology.yml ==="
if [ ! -f "docker-compose-synology.yml" ]; then
    echo "✗ docker-compose-synology.yml not found!"
    exit 1
fi

# Check if it already has the volume mount for /app
if grep -q "/volume1/docker/pdf-extractor:/app" docker-compose-synology.yml; then
    echo "✓ docker-compose already has full volume mount"
else
    echo "⚠️  docker-compose may need updating - check volume mounts"
fi

# Check port
if grep -q "\"5005:5000\"" docker-compose-synology.yml; then
    echo "✓ Port 5005 configured correctly"
else
    echo "⚠️  Port may not be set to 5005"
fi
echo ""

echo "=== Step 3: Verify Required Code Files ==="
if [ -f "app.py" ] && grep -q "RFMS returned.*customers.*Sample customer types" app.py; then
    echo "✓ app.py has updated builder search code"
else
    echo "✗ app.py missing or outdated - needs manual update"
fi

if [ -f "utils/ai_analyzer.py" ]; then
    echo "✓ utils/ai_analyzer.py exists"
else
    echo "✗ utils/ai_analyzer.py missing"
fi

if [ -f "utils/rfms_client.py" ]; then
    echo "✓ utils/rfms_client.py exists"
else
    echo "✗ utils/rfms_client.py missing"
fi
echo ""

echo "=== Step 4: Restart Container with Correct Configuration ==="
read -p "Do you want to restart the container now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Stopping container..."
    docker-compose -f docker-compose-synology.yml down
    
    echo "Starting container..."
    docker-compose -f docker-compose-synology.yml up -d
    
    echo "Waiting for container to start..."
    sleep 5
    
    echo "Container status:"
    docker ps | grep pdf-extractor
    
    echo ""
    echo "Recent logs:"
    docker logs pdf-extractor --tail 20
fi

echo ""
echo "=========================================="
echo "Fix Complete"
echo "=========================================="

