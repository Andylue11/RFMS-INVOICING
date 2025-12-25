#!/bin/bash
# Remote update script - Run this via SSH on the office server
# Usage: ssh atoz@AtozServer 'bash -s' < update-office-server-remote.sh
# OR: Copy this script to the server and run it there

set -e  # Exit on error

echo "=========================================="
echo "RFMS-Uploader - Office Server Update"
echo "=========================================="
echo ""

# Detect the application directory
# Try common locations
if [ -d "/volume1/docker/RFMS-UPLOADER" ]; then
    APP_DIR="/volume1/docker/RFMS-UPLOADER"
elif [ -d "/volume1/docker/rfms-uploader" ]; then
    APP_DIR="/volume1/docker/rfms-uploader"
elif [ -d "/opt/rfms-uploader" ]; then
    APP_DIR="/opt/rfms-uploader"
elif [ -f "$(pwd)/docker-compose.yml" ]; then
    APP_DIR=$(pwd)
else
    echo "ERROR: Could not find application directory"
    echo "Please run this script from the application directory"
    exit 1
fi

cd "$APP_DIR"
echo "✓ Using application directory: $APP_DIR"

CONTAINER_NAME="rfms-uploader"
COMPOSE_FILE="docker-compose.yml"

# Step 1: Pull latest code from git
echo ""
echo "[1/6] Pulling latest code from git..."
if [ -d ".git" ]; then
    git fetch origin
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "stock-recv" ]; then
        echo "  Switching to stock-recv branch..."
        git checkout stock-recv
    fi
    git pull origin stock-recv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to pull latest code"
        exit 1
    fi
    echo "✓ Code updated from git"
else
    echo "⚠ No .git directory found - skipping git pull"
    echo "  Make sure code is updated manually"
fi

# Step 2: Stop the container
echo ""
echo "[2/6] Stopping container..."
# Detect docker-compose command
if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

$DOCKER_COMPOSE -f "$COMPOSE_FILE" down
if [ $? -ne 0 ]; then
    echo "WARNING: Container may not have been running"
fi
echo "✓ Container stopped"

# Step 3: Remove old images (optional - keeps cache if commented)
echo ""
echo "[3/6] Removing old images..."
$DOCKER_COMPOSE -f "$COMPOSE_FILE" down --rmi local 2>/dev/null || true
echo "✓ Old images removed"

# Step 4: Rebuild the container
echo ""
echo "[4/6] Rebuilding container (this may take a few minutes)..."
$DOCKER_COMPOSE -f "$COMPOSE_FILE" build --no-cache
if [ $? -ne 0 ]; then
    echo "ERROR: Build failed!"
    echo "Check the build output above for errors"
    exit 1
fi
echo "✓ Container rebuilt"

# Step 5: Start the container
echo ""
echo "[5/6] Starting container..."
$DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start container!"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=50
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
$DOCKER_COMPOSE -f "$COMPOSE_FILE" ps

echo ""
echo "=========================================="
echo "Recent Logs (last 30 lines):"
echo "=========================================="
$DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=30

echo ""
echo "=========================================="
echo "Checking if application is responding..."
echo "=========================================="
sleep 5
if curl -s http://localhost:5007 >/dev/null 2>&1; then
    echo "✓ Application is responding on port 5007"
else
    echo "⚠ Application is not responding yet (may still be starting)"
    echo "Check logs with: $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f"
fi

echo ""
echo "=========================================="
echo "✅ Update Complete!"
echo "=========================================="
echo "Container: $CONTAINER_NAME"
echo "Port: 5007"
echo "Directory: $APP_DIR"
echo ""
echo "Useful commands:"
echo "  View logs:    $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f"
echo "  Stop:         $DOCKER_COMPOSE -f $COMPOSE_FILE down"
echo "  Restart:      $DOCKER_COMPOSE -f $COMPOSE_FILE restart"
echo "  Shell:        docker exec -it $CONTAINER_NAME bash"
echo ""

