#!/bin/bash

# PDF Extractor Monitoring Script for Synology NAS
# This script monitors the application and sends alerts

APP_DIR="/volume1/docker/pdf-extractor"
LOG_FILE="/volume1/docker/pdf-extractor/logs/monitor.log"
ALERT_EMAIL="admin@yourcompany.com"  # Change this to your email

# Create log file if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to send alert
send_alert() {
    local message="$1"
    log_message "ALERT: $message"
    
    # Send email if mail command is available
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "PDF Extractor Alert" "$ALERT_EMAIL"
    fi
    
    # Log to Synology system log
    logger "PDF Extractor Alert: $message"
}

# Check if container is running
check_container() {
    if ! docker ps | grep -q pdf-extractor; then
        send_alert "PDF Extractor container is not running"
        return 1
    fi
    return 0
}

# Check application response
check_application() {
    if ! curl -s -f "http://localhost:5000/api/rfms-status" > /dev/null; then
        send_alert "PDF Extractor application is not responding"
        return 1
    fi
    return 0
}

# Check disk space
check_disk_space() {
    local usage=$(df -h /volume1 | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$usage" -gt 90 ]; then
        send_alert "Disk usage is critical: ${usage}%"
        return 1
    elif [ "$usage" -gt 80 ]; then
        log_message "WARNING: Disk usage is high: ${usage}%"
    fi
    return 0
}

# Check memory usage
check_memory() {
    local usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$usage" -gt 90 ]; then
        send_alert "Memory usage is critical: ${usage}%"
        return 1
    elif [ "$usage" -gt 80 ]; then
        log_message "WARNING: Memory usage is high: ${usage}%"
    fi
    return 0
}

# Check for errors in logs
check_logs() {
    local error_count=$(docker-compose logs --tail=50 2>&1 | grep -i error | wc -l)
    if [ "$error_count" -gt 5 ]; then
        send_alert "High number of errors in logs: $error_count"
        return 1
    fi
    return 0
}

# Main monitoring function
monitor() {
    log_message "Starting PDF Extractor monitoring"
    
    local issues=0
    
    # Run all checks
    check_container || ((issues++))
    check_application || ((issues++))
    check_disk_space || ((issues++))
    check_memory || ((issues++))
    check_logs || ((issues++))
    
    if [ "$issues" -eq 0 ]; then
        log_message "All checks passed - Application is healthy"
    else
        log_message "Found $issues issues - Application needs attention"
    fi
    
    log_message "Monitoring cycle complete"
}

# Run monitoring
cd "$APP_DIR"
monitor

