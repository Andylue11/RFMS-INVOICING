#!/bin/bash

# PDF Extractor Update Script for Synology NAS
# Run this script to update your PDF Extractor application

set -e

echo "=========================================="
echo "PDF Extractor Update Script"
echo "=========================================="

APP_DIR="/volume1/docker/pdf-extractor"
BACKUP_DIR="/volume1/docker/pdf-extractor-backup"

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application directory not found: $APP_DIR"
    echo "Please run the deployment script first."
    exit 1
fi

cd "$APP_DIR"

# Create backup
echo "💾 Creating backup..."
BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
sudo mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
sudo cp -r instance "$BACKUP_DIR/$BACKUP_NAME/" 2>/dev/null || true
sudo cp -r uploads "$BACKUP_DIR/$BACKUP_NAME/" 2>/dev/null || true

# Detect docker-compose command (prefer docker compose v2 on Synology)
DOCKER_COMPOSE_CMD="docker compose"
if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif [ -f /usr/local/bin/docker-compose ]; then
    DOCKER_COMPOSE_CMD="/usr/local/bin/docker-compose"
elif [ -f /usr/bin/docker-compose ]; then
    DOCKER_COMPOSE_CMD="/usr/bin/docker-compose"
fi

# Stop the application
echo "🛑 Stopping application..."
$DOCKER_COMPOSE_CMD down

# Update application files
echo "📋 Updating application files..."
if [ -d ".git" ]; then
    if command -v git &> /dev/null || command -v /bin/git &> /dev/null; then
    echo "Using Git to update..."
        GIT_CMD=$(command -v git 2>/dev/null || echo /bin/git)
        $GIT_CMD pull
    else
        echo "⚠️  Git not installed on this system."
        echo "Please either:"
        echo "  1. Install Git Server from Package Center"
        echo "  2. Or manually copy files using SCP/File Station"
        echo ""
        read -p "Press Enter to continue without updating files, or Ctrl+C to cancel..."
    fi
else
    echo "⚠️  No Git repository found. Please manually update files."
    echo "Copy new files to: $APP_DIR"
    read -p "Press Enter when files are updated..."
fi

# Rebuild and start
echo "🔨 Rebuilding and starting application..."
$DOCKER_COMPOSE_CMD up -d --build

# Wait for startup
echo "⏳ Waiting for application to start..."
sleep 15

# Verify it's running
if docker ps | grep -q pdf-extractor; then
    echo "✅ Update completed successfully!"
    echo "🌐 Application is running at: http://$(hostname -I | awk '{print $1}'):5000"
else
    echo "❌ Update failed. Restoring from backup..."
    $DOCKER_COMPOSE_CMD down
    sudo cp -r "$BACKUP_DIR/$BACKUP_NAME/instance" ./
    sudo cp -r "$BACKUP_DIR/$BACKUP_NAME/uploads" ./
    $DOCKER_COMPOSE_CMD up -d
    echo "🔄 Restored from backup. Check logs: $DOCKER_COMPOSE_CMD logs"
fi

echo "=========================================="
