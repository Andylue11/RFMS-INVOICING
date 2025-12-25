#!/bin/bash
# Diagnostic script for Docker build issues

echo "=========================================="
echo "Docker Build Diagnostics"
echo "=========================================="

cd /volume1/docker/pdf-extractor

echo ""
echo "1. Current directory:"
pwd

echo ""
echo "2. Files in directory:"
ls -la

echo ""
echo "3. Dockerfile exists and size:"
if [ -f "Dockerfile" ]; then
    ls -lh Dockerfile
    echo "First 10 lines of Dockerfile:"
    head -10 Dockerfile
else
    echo "ERROR: Dockerfile not found!"
    exit 1
fi

echo ""
echo "4. docker-compose.yml exists:"
if [ -f "docker-compose.yml" ]; then
    ls -lh docker-compose.yml
else
    echo "ERROR: docker-compose.yml not found!"
    exit 1
fi

echo ""
echo "5. Docker version:"
docker --version
docker-compose --version

echo ""
echo "6. Docker daemon status:"
docker info 2>&1 | head -5

echo ""
echo "7. Existing containers:"
docker ps -a | grep pdf-extractor || echo "No pdf-extractor containers found"

echo ""
echo "8. Existing images:"
docker images | grep pdf-extractor || echo "No pdf-extractor images found"

echo ""
echo "9. Disk space:"
df -h /volume1

echo ""
echo "10. Testing Docker build manually:"
echo "Running: docker build --no-cache -t pdf-extractor-test ."
docker build --no-cache -t pdf-extractor-test . 2>&1 | tail -20

echo ""
echo "=========================================="
echo "Diagnostics complete"
echo "=========================================="

