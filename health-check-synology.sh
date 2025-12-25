#!/bin/bash

# PDF Extractor Health Check Script for Synology NAS
# Run this script to check the health of your PDF Extractor application

echo "=========================================="
echo "PDF Extractor Health Check"
echo "=========================================="

APP_DIR="/volume1/docker/pdf-extractor"
NAS_IP=$(hostname -I | awk '{print $1}')

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application directory not found: $APP_DIR"
    exit 1
fi

cd "$APP_DIR"

echo "🔍 Checking application status..."

# Check if container is running
if docker ps | grep -q pdf-extractor; then
    echo "✅ Container is running"
    
    # Get container status
    CONTAINER_STATUS=$(docker ps --format "table {{.Status}}" | grep pdf-extractor)
    echo "📊 Container status: $CONTAINER_STATUS"
else
    echo "❌ Container is not running"
    echo "Attempting to start..."
    docker-compose up -d
    sleep 10
    if docker ps | grep -q pdf-extractor; then
        echo "✅ Container started successfully"
    else
        echo "❌ Failed to start container"
        exit 1
    fi
fi

# Check disk space
echo ""
echo "💾 Checking disk space..."
DISK_USAGE=$(df -h /volume1 | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "✅ Disk usage: ${DISK_USAGE}% (OK)"
else
    echo "⚠️  Disk usage: ${DISK_USAGE}% (High)"
fi

# Check application logs for errors
echo ""
echo "📝 Checking recent logs for errors..."
ERROR_COUNT=$(docker-compose logs --tail=100 2>&1 | grep -i error | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "✅ No errors in recent logs"
else
    echo "⚠️  Found $ERROR_COUNT errors in recent logs"
    echo "Recent errors:"
    docker-compose logs --tail=50 2>&1 | grep -i error | tail -5
fi

# Check database file
echo ""
echo "🗄️  Checking database..."
if [ -f "instance/rfms_xtracr.db" ]; then
    DB_SIZE=$(du -h instance/rfms_xtracr.db | cut -f1)
    echo "✅ Database exists (Size: $DB_SIZE)"
else
    echo "⚠️  Database file not found"
fi

# Check uploads directory
echo ""
echo "📁 Checking uploads directory..."
if [ -d "uploads" ]; then
    UPLOAD_COUNT=$(find uploads -type f | wc -l)
    UPLOAD_SIZE=$(du -sh uploads 2>/dev/null | cut -f1 || echo "0")
    echo "✅ Uploads directory exists ($UPLOAD_COUNT files, $UPLOAD_SIZE)"
else
    echo "⚠️  Uploads directory not found"
fi

# Test application endpoint
echo ""
echo "🌐 Testing application endpoint..."
if curl -s -f "http://localhost:5000/api/rfms-status" > /dev/null; then
    echo "✅ Application is responding"
else
    echo "❌ Application is not responding"
    echo "Check logs: docker-compose logs"
fi

# Check memory usage
echo ""
echo "🧠 Checking memory usage..."
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
echo "📊 Memory usage: ${MEMORY_USAGE}%"

# Check CPU usage
echo ""
echo "⚡ Checking CPU usage..."
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
echo "📊 CPU usage: ${CPU_USAGE}%"

# Summary
echo ""
echo "=========================================="
echo "📋 Health Check Summary"
echo "=========================================="
echo "🌐 Application URL: http://$NAS_IP:5000"
echo "📁 Application Directory: $APP_DIR"
echo "💾 Disk Usage: ${DISK_USAGE}%"
echo "🧠 Memory Usage: ${MEMORY_USAGE}%"
echo "⚡ CPU Usage: ${CPU_USAGE}%"

if [ "$ERROR_COUNT" -eq 0 ] && curl -s -f "http://localhost:5000/api/rfms-status" > /dev/null; then
    echo "✅ Overall Status: HEALTHY"
else
    echo "⚠️  Overall Status: NEEDS ATTENTION"
fi

echo "=========================================="

