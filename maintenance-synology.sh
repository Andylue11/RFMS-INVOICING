#!/bin/bash

# PDF Extractor Maintenance Script for Synology NAS
# This script performs routine maintenance tasks

echo "=========================================="
echo "PDF Extractor Maintenance Script"
echo "=========================================="

APP_DIR="/volume1/docker/pdf-extractor"
BACKUP_DIR="/volume1/backup/pdf-extractor"

# Create backup directory
sudo mkdir -p "$BACKUP_DIR"

cd "$APP_DIR"

echo "🧹 Starting maintenance tasks..."

# 1. Clean up old Docker images
echo "🐳 Cleaning up old Docker images..."
docker image prune -f

# 2. Clean up old containers
echo "📦 Cleaning up old containers..."
docker container prune -f

# 3. Clean up old volumes
echo "💾 Cleaning up old volumes..."
docker volume prune -f

# 4. Clean up old logs (keep last 7 days)
echo "📝 Cleaning up old logs..."
if [ -d "logs" ]; then
    find logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
    echo "✅ Old logs cleaned"
else
    echo "⚠️  Logs directory not found"
fi

# 5. Clean up old uploads (keep last 30 days)
echo "📁 Cleaning up old uploads..."
if [ -d "uploads" ]; then
    find uploads -type f -mtime +30 -delete 2>/dev/null || true
    echo "✅ Old uploads cleaned"
else
    echo "⚠️  Uploads directory not found"
fi

# 6. Optimize database
echo "🗄️  Optimizing database..."
if [ -f "instance/rfms_xtracr.db" ]; then
    # Create backup before optimization
    sudo cp "instance/rfms_xtracr.db" "$BACKUP_DIR/rfms_xtracr_$(date +%Y%m%d).db"
    
    # Optimize SQLite database
    sqlite3 "instance/rfms_xtracr.db" "VACUUM; ANALYZE;" 2>/dev/null || true
    echo "✅ Database optimized"
else
    echo "⚠️  Database file not found"
fi

# 7. Check disk space
echo "💾 Checking disk space..."
DISK_USAGE=$(df -h /volume1 | tail -1 | awk '{print $5}' | sed 's/%//')
echo "📊 Disk usage: ${DISK_USAGE}%"

# 8. Restart application if needed
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "⚠️  Disk usage is high, restarting application..."
    docker-compose restart
    sleep 10
    echo "✅ Application restarted"
fi

# 9. Update system packages (if needed)
echo "📦 Checking for system updates..."
if command -v apt-get &> /dev/null; then
    apt-get update > /dev/null 2>&1
    UPDATES=$(apt-get upgrade -s | grep -c "upgraded" || echo "0")
    if [ "$UPDATES" -gt 0 ]; then
        echo "⚠️  $UPDATES system updates available"
    else
        echo "✅ System is up to date"
    fi
fi

# 10. Generate maintenance report
echo ""
echo "📋 Generating maintenance report..."
REPORT_FILE="logs/maintenance-$(date +%Y%m%d).log"
cat > "$REPORT_FILE" << EOF
PDF Extractor Maintenance Report
Date: $(date)
Disk Usage: ${DISK_USAGE}%
Container Status: $(docker ps --format "table {{.Status}}" | grep pdf-extractor || echo "Not running")
Database Size: $(du -h instance/rfms_xtracr.db 2>/dev/null | cut -f1 || echo "Not found")
Uploads Count: $(find uploads -type f 2>/dev/null | wc -l)
Log Files Count: $(find logs -name "*.log" 2>/dev/null | wc -l)
EOF

echo "✅ Maintenance report saved to: $REPORT_FILE"

echo ""
echo "=========================================="
echo "✅ Maintenance Complete!"
echo "=========================================="
echo "📊 Disk Usage: ${DISK_USAGE}%"
echo "📁 Backup Location: $BACKUP_DIR"
echo "📝 Report: $REPORT_FILE"
echo "=========================================="

