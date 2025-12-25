#!/bin/bash
# Complete Docker rebuild script for NAS

set -e  # Exit on error

echo "=========================================="
echo "RFMS Uploader - Complete Docker Rebuild"
echo "=========================================="

cd /volume1/docker/pdf-extractor

# Step 1: Verify files exist
echo ""
echo "[1/7] Verifying files..."
if [ ! -f "Dockerfile" ]; then
    echo "ERROR: Dockerfile not found!"
    exit 1
fi
if [ ! -f "docker-compose.yml" ]; then
    echo "ERROR: docker-compose.yml not found!"
    exit 1
fi
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found!"
    exit 1
fi
if [ ! -d "data" ]; then
    echo "WARNING: data directory not found!"
    echo "Creating data directory..."
    mkdir -p data
fi
if [ ! -f "data/australian_postcodes.csv" ]; then
    echo "WARNING: australian_postcodes.csv not found in data directory!"
fi
echo "✓ Files verified"

# Step 2: Stop and remove container
echo ""
echo "[2/7] Stopping and removing container..."
docker-compose down 2>/dev/null || true
echo "✓ Container stopped"

# Step 3: Remove all related images
echo ""
echo "[3/7] Removing old images..."
docker rmi pdf-extractor-pdf-extractor 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=pdf-extractor*") 2>/dev/null || true
docker system prune -f --volumes 2>/dev/null || true
echo "✓ Old images removed"

# Step 4: Verify Docker is running
echo ""
echo "[4/7] Checking Docker status..."
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    exit 1
fi
echo "✓ Docker is running"

# Step 5: Build with verbose output
echo ""
echo "[5/7] Building Docker image (this may take 5-10 minutes)..."
echo "Build output:"
docker-compose build --no-cache --progress=plain 2>&1 | tee /tmp/docker-build.log

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "ERROR: Build failed!"
    echo "Last 50 lines of build log:"
    tail -50 /tmp/docker-build.log
    exit 1
fi
echo "✓ Build completed"

# Step 6: Start container
echo ""
echo "[6/7] Starting container..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start container!"
    docker-compose logs
    exit 1
fi
echo "✓ Container started"

# Step 7: Wait and check status
echo ""
echo "[7/7] Waiting for container to start..."
sleep 10

echo ""
echo "=========================================="
echo "Container Status:"
echo "=========================================="
docker-compose ps

echo ""
echo "=========================================="
echo "Recent Logs (last 30 lines):"
echo "=========================================="
docker-compose logs --tail=30

echo ""
echo "=========================================="
echo "Checking if application is responding..."
echo "=========================================="
sleep 5
if curl -s http://localhost:5005 >/dev/null 2>&1; then
    echo "✓ Application is responding on port 5005"
else
    echo "⚠ Application is not responding yet (may still be starting)"
    echo "Check logs with: docker-compose logs -f"
fi

echo ""
echo "=========================================="
echo "✅ Rebuild Complete!"
echo "=========================================="
echo "Application URL: http://192.168.0.201:5005"
echo ""
echo "Useful commands:"
echo "  View logs:    docker-compose logs -f"
echo "  Stop:         docker-compose down"
echo "  Restart:      docker-compose restart"
echo "  Shell:        docker exec -it pdf-extractor bash"
echo ""

