#!/bin/bash
# Script to check server Docker container setup and code correctness
# Run this on the server: ssh atoz@AtozServer

echo "=========================================="
echo "Server Docker Container Setup Check"
echo "=========================================="
echo ""

cd /volume1/docker/pdf-extractor || exit 1

echo "=== 1. Checking Docker Container Status ==="
docker ps -a | grep pdf-extractor
echo ""

echo "=== 2. Checking Volume Mounts ==="
docker inspect pdf-extractor 2>/dev/null | grep -A 20 "Mounts" || echo "Container not running"
echo ""

echo "=== 3. Checking docker-compose Configuration ==="
if [ -f "docker-compose-synology.yml" ]; then
    echo "✓ docker-compose-synology.yml exists"
    echo "Port mapping:"
    grep -A 1 "ports:" docker-compose-synology.yml
    echo ""
    echo "Volume mounts:"
    grep -A 5 "volumes:" docker-compose-synology.yml
    echo ""
else
    echo "✗ docker-compose-synology.yml NOT FOUND"
    echo ""
fi

echo "=== 4. Checking for .git Directory (should NOT exist) ==="
if [ -d ".git" ]; then
    echo "⚠️  WARNING: .git directory found on server!"
    echo "   This should be removed - server should not be a git repository"
    echo "   Size: $(du -sh .git 2>/dev/null | cut -f1)"
else
    echo "✓ No .git directory found (good)"
fi
echo ""

echo "=== 5. Checking Required Files ==="
REQUIRED_FILES=("app.py" "models.py" "requirements.txt" "Dockerfile" "utils/rfms_client.py" "utils/ai_analyzer.py")
MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file MISSING"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done
echo ""

if [ $MISSING_FILES -gt 0 ]; then
    echo "⚠️  $MISSING_FILES required file(s) missing!"
fi

echo "=== 6. Checking app.py Code (Builder Search Function) ==="
if grep -q "RFMS returned.*customers.*Sample customer types" app.py 2>/dev/null; then
    echo "✓ Improved logging found in search_customers function"
else
    echo "✗ Improved logging NOT found - code may be outdated"
fi

if grep -q "BUILDER'" app.py 2>/dev/null && grep -q "No customers matched builder filter criteria" app.py 2>/dev/null; then
    echo "✓ Builder search improvements found (BUILDER singular + fallback logic)"
else
    echo "✗ Builder search improvements NOT found"
fi
echo ""

echo "=== 7. Checking Port Configuration ==="
EXPECTED_PORT="5005"
if grep -q "\"$EXPECTED_PORT:5000\"" docker-compose-synology.yml 2>/dev/null; then
    echo "✓ Port $EXPECTED_PORT configured correctly"
else
    echo "✗ Port NOT set to $EXPECTED_PORT in docker-compose-synology.yml"
fi
echo ""

echo "=== 8. Checking Container Code (inside running container) ==="
if docker ps | grep -q pdf-extractor; then
    echo "Container is running, checking code inside container:"
    if docker exec pdf-extractor grep -q "RFMS returned.*customers.*Sample customer types" /app/app.py 2>/dev/null; then
        echo "✓ Container has updated code with improved logging"
    else
        echo "✗ Container code is OUTDATED (missing improvements)"
    fi
    
    CONTAINER_PORT=$(docker port pdf-extractor 2>/dev/null | grep "5000/tcp" | cut -d: -f2)
    echo "Container is accessible on host port: $CONTAINER_PORT"
else
    echo "Container is not running"
fi
echo ""

echo "=== 9. Checking for Unnecessary Files ==="
if [ -d ".git" ]; then
    echo "⚠️  .git directory should be removed"
fi
if [ -f ".gitignore" ]; then
    echo "⚠️  .gitignore on server (not needed, but not harmful)"
fi
if [ -d "__pycache__" ]; then
    echo "⚠️  __pycache__ directories found (can be cleaned up)"
fi
if [ -f "app.log" ]; then
    echo "ℹ️  app.log found (log file)"
fi
echo ""

echo "=========================================="
echo "Check Complete"
echo "=========================================="

