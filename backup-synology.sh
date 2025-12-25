#!/bin/bash

# PDF Extractor Backup Script for Synology NAS
# Run this script to backup your PDF Extractor data

set -e

echo "=========================================="
echo "PDF Extractor Backup Script"
echo "=========================================="

APP_DIR="/volume1/docker/pdf-extractor"
BACKUP_DIR="/volume1/backup/pdf-extractor"
DATE=$(date +%Y%m%d-%H%M%S)

# Create backup directory
sudo mkdir -p "$BACKUP_DIR"

echo "💾 Creating backup: $DATE"

# Backup database
if [ -d "$APP_DIR/instance" ]; then
    echo "📊 Backing up database..."
    sudo cp -r "$APP_DIR/instance" "$BACKUP_DIR/instance-$DATE"
fi

# Backup uploads
if [ -d "$APP_DIR/uploads" ]; then
    echo "📁 Backing up uploads..."
    sudo cp -r "$APP_DIR/uploads" "$BACKUP_DIR/uploads-$DATE"
fi

# Backup logs
if [ -d "$APP_DIR/logs" ]; then
    echo "📝 Backing up logs..."
    sudo cp -r "$APP_DIR/logs" "$BACKUP_DIR/logs-$DATE"
fi

# Create compressed archive
echo "🗜️  Creating compressed archive..."
cd "$BACKUP_DIR"
sudo tar -czf "pdf-extractor-backup-$DATE.tar.gz" "instance-$DATE" "uploads-$DATE" "logs-$DATE" 2>/dev/null || true

# Clean up individual directories
sudo rm -rf "instance-$DATE" "uploads-$DATE" "logs-$DATE"

# Set proper permissions
sudo chown -R $(whoami):users "$BACKUP_DIR"

echo "✅ Backup completed: $BACKUP_DIR/pdf-extractor-backup-$DATE.tar.gz"

# Show backup size
BACKUP_SIZE=$(du -h "$BACKUP_DIR/pdf-extractor-backup-$DATE.tar.gz" | cut -f1)
echo "📏 Backup size: $BACKUP_SIZE"

# Clean old backups (keep last 10)
echo "🧹 Cleaning old backups (keeping last 10)..."
cd "$BACKUP_DIR"
ls -t pdf-extractor-backup-*.tar.gz | tail -n +11 | xargs -r sudo rm

echo "=========================================="
echo "✅ Backup Complete!"
echo "=========================================="
