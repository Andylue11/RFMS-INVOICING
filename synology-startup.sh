#!/bin/bash
#
# Synology NAS Startup Script
# This script ensures Docker containers are running after system reboot
# Place this in: /usr/local/etc/rc.d/S99rfms-uploader.sh
# Or schedule it via Synology Task Scheduler to run at boot
#

APP_NAME="rfms-uploader"
APP_DIR="/volume1/docker/rfms-uploader"
LOG_FILE="/volume1/docker/rfms-uploader/logs/startup.log"
MAX_RETRIES=5
RETRY_DELAY=10

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Wait for Docker to be ready
wait_for_docker() {
    local retries=0
    log_message "Waiting for Docker to be ready..."
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if docker ps > /dev/null 2>&1; then
            log_message "Docker is ready"
            return 0
        fi
        retries=$((retries + 1))
        log_message "Docker not ready yet, waiting... (attempt $retries/$MAX_RETRIES)"
        sleep $RETRY_DELAY
    done
    
    log_message "ERROR: Docker did not become ready after $MAX_RETRIES attempts"
    return 1
}

# Wait for network to be ready
wait_for_network() {
    local retries=0
    log_message "Waiting for network to be ready..."
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
            log_message "Network is ready"
            return 0
        fi
        retries=$((retries + 1))
        log_message "Network not ready yet, waiting... (attempt $retries/$MAX_RETRIES)"
        sleep $RETRY_DELAY
    done
    
    log_message "WARNING: Network check failed, but continuing anyway"
    return 0
}

# Start the application containers
start_containers() {
    log_message "Starting $APP_NAME containers..."
    
    if [ ! -d "$APP_DIR" ]; then
        log_message "ERROR: Application directory not found: $APP_DIR"
        return 1
    fi
    
    cd "$APP_DIR" || {
        log_message "ERROR: Cannot change to directory: $APP_DIR"
        return 1
    }
    
    # Check if docker-compose file exists
    if [ ! -f "docker-compose-nas.yml" ]; then
        log_message "ERROR: docker-compose-nas.yml not found"
        return 1
    fi
    
    # Determine docker-compose command
    if command -v docker-compose > /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version > /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        log_message "ERROR: docker-compose not found"
        return 1
    fi
    
    # Start containers
    log_message "Running: $DOCKER_COMPOSE_CMD -f docker-compose-nas.yml up -d"
    $DOCKER_COMPOSE_CMD -f docker-compose-nas.yml up -d >> "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        log_message "Containers started successfully"
        
        # Wait a moment for containers to initialize
        sleep 5
        
        # Check container status
        if docker ps | grep -q uploader; then
            log_message "Container 'uploader' is running"
        else
            log_message "WARNING: Container 'uploader' may not be running"
        fi
        
        return 0
    else
        log_message "ERROR: Failed to start containers"
        return 1
    fi
}

# Main execution
main() {
    log_message "=========================================="
    log_message "RFMS Uploader Startup Script"
    log_message "=========================================="
    
    # Wait for Docker
    if ! wait_for_docker; then
        log_message "FATAL: Cannot proceed without Docker"
        exit 1
    fi
    
    # Wait for network (optional, but good for API calls)
    wait_for_network
    
    # Start containers
    if start_containers; then
        log_message "Startup completed successfully"
        exit 0
    else
        log_message "Startup completed with errors"
        exit 1
    fi
}

# Run main function
main "$@"




