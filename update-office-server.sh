#!/bin/bash
# Update RFMS-Uploader container on office server
# This script stops the container, pulls latest code, rebuilds, and restarts

set -e  # Exit on error

echo "=========================================="
echo "RFMS-Uploader - Office Server Update"
echo "=========================================="
echo ""

# Configuration - Update these if needed
APP_DIR="/path/to/RFMS-UPLOADER"  # Update with actual path on office server
CONTAINER_NAME="rfms-uploader"
COMPOSE_FILE="docker-compose.yml"

# Check if we're in the right directory or if APP_DIR is set
if [ -f "docker-compose.yml" ]; then
    APP_DIR=$(pwd)
    echo "✓ Found docker-compose.yml in current directory"
elif [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    echo "✓ Changed to app directory: $APP_DIR"
else
    echo "ERROR: Could not find application directory"
    echo "Please run this script from the app directory or set APP_DIR variable"
    exit 1
fi

# Step 1: Pull latest code from git
echo ""
echo "[1/6] Pulling latest code from git..."
git fetch origin
git checkout stock-recv
git pull origin stock-recv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to pull latest code"
    exit 1
fi
echo "✓ Code updated"

# Step 2: Stop the container
echo ""
echo "[2/6] Stopping container..."
docker-compose -f "$COMPOSE_FILE" down
if [ $? -ne 0 ]; then
    echo "WARNING: Container may not have been running"
fi
echo "✓ Container stopped"

# Step 3: Remove old images (optional - comment out if you want to keep cache)
echo ""
echo "[3/6] Removing old images..."
docker-compose -f "$COMPOSE_FILE" down --rmi local 2>/dev/null || true
echo "✓ Old images removed"

# Step 4: Rebuild the container
echo ""
echo "[4/6] Rebuilding container (this may take a few minutes)..."
docker-compose -f "$COMPOSE_FILE" build --no-cache
if [ $? -ne 0 ]; then
    echo "ERROR: Build failed!"
    echo "Check the build output above for errors"
    exit 1
fi
echo "✓ Container rebuilt"

# Step 5: Start the container
echo ""
echo "[5/6] Starting container..."
docker-compose -f "$COMPOSE_FILE" up -d
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start container!"
    docker-compose -f "$COMPOSE_FILE" logs --tail=50
    exit 1
fi
echo "✓ Container started"

# Step 6: Wait and verify
echo ""
echo "[6/6] Waiting for container to start and verify..."
sleep 15

echo ""
echo "=========================================="
echo "Container Status:"
echo "=========================================="
docker-compose -f "$COMPOSE_FILE" ps

echo ""
echo "=========================================="
echo "Recent Logs (last 30 lines):"
echo "=========================================="
docker-compose -f "$COMPOSE_FILE" logs --tail=30

echo ""
echo "=========================================="
echo "Checking if application is responding..."
echo "=========================================="
sleep 5
if curl -s http://localhost:5007 >/dev/null 2>&1; then
    echo "✓ Application is responding on port 5007"
else
    echo "⚠ Application is not responding yet (may still be starting)"
    echo "Check logs with: docker-compose -f $COMPOSE_FILE logs -f"
fi

echo ""
echo "=========================================="
echo "✅ Update Complete!"
echo "=========================================="
echo "Container: $CONTAINER_NAME"
echo "Port: 5007"
echo ""
echo "Useful commands:"
echo "  View logs:    docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop:         docker-compose -f $COMPOSE_FILE down"
echo "  Restart:      docker-compose -f $COMPOSE_FILE restart"
echo "  Shell:        docker exec -it $CONTAINER_NAME bash"
echo ""

