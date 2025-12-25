#!/bin/bash

# PDF Extractor Disaster Recovery Script for Synology NAS
# This script helps recover from various disaster scenarios

echo "=========================================="
echo "PDF Extractor Disaster Recovery"
echo "=========================================="

APP_DIR="/volume1/docker/pdf-extractor"
BACKUP_DIR="/volume1/backup/pdf-extractor"
RECOVERY_DIR="/volume1/docker/pdf-extractor-recovery"

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application directory not found: $APP_DIR"
    echo "Please run the setup script first."
    exit 1
fi

cd "$APP_DIR"

# Function to show recovery menu
show_recovery_menu() {
    echo ""
    echo "🚨 Disaster Recovery Menu"
    echo "========================"
    echo "1. 🔄 Complete System Recovery"
    echo "2. 🗄️  Database Recovery"
    echo "3. 📁 Data Recovery"
    echo "4. 🐳 Container Recovery"
    echo "5. 🔧 Configuration Recovery"
    echo "6. 📝 Log Recovery"
    echo "7. 🌐 Network Recovery"
    echo "8. 💾 Backup Verification"
    echo "9. 🔍 System Diagnostics"
    echo "10. ❌ Exit"
    echo ""
    read -p "Select recovery option (1-10): " choice
}

# Function to complete system recovery
complete_system_recovery() {
    echo "🔄 Starting complete system recovery..."
    
    # Stop all containers
    docker-compose down
    
    # Clean up Docker
    docker system prune -f
    
    # Restore from latest backup
    if [ -d "$BACKUP_DIR" ]; then
        LATEST_BACKUP=$(ls -t "$BACKUP_DIR" | head -1)
        if [ -n "$LATEST_BACKUP" ]; then
            echo "📦 Restoring from backup: $LATEST_BACKUP"
            sudo cp -r "$BACKUP_DIR/$LATEST_BACKUP"/* "$APP_DIR/"
        else
            echo "❌ No backup found"
            return 1
        fi
    else
        echo "❌ Backup directory not found"
        return 1
    fi
    
    # Rebuild and start
    docker-compose up -d --build
    
    # Wait for startup
    sleep 20
    
    if docker ps | grep -q pdf-extractor; then
        echo "✅ Complete system recovery successful"
    else
        echo "❌ Complete system recovery failed"
    fi
}

# Function to database recovery
database_recovery() {
    echo "🗄️  Starting database recovery..."
    
    # Check for database backups
    if [ -d "$BACKUP_DIR" ]; then
        DB_BACKUPS=$(find "$BACKUP_DIR" -name "rfms_xtracr*.db" | sort -r)
        if [ -n "$DB_BACKUPS" ]; then
            LATEST_DB=$(echo "$DB_BACKUPS" | head -1)
            echo "📊 Restoring database from: $LATEST_DB"
            
            # Stop application
            docker-compose down
            
            # Backup current database
            if [ -f "instance/rfms_xtracr.db" ]; then
                sudo cp "instance/rfms_xtracr.db" "instance/rfms_xtracr.db.backup.$(date +%Y%m%d-%H%M%S)"
            fi
            
            # Restore database
            sudo cp "$LATEST_DB" "instance/rfms_xtracr.db"
            
            # Start application
            docker-compose up -d
            
            # Wait for startup
            sleep 15
            
            if docker ps | grep -q pdf-extractor; then
                echo "✅ Database recovery successful"
            else
                echo "❌ Database recovery failed"
            fi
        else
            echo "❌ No database backups found"
        fi
    else
        echo "❌ Backup directory not found"
    fi
}

# Function to data recovery
data_recovery() {
    echo "📁 Starting data recovery..."
    
    # Check for data backups
    if [ -d "$BACKUP_DIR" ]; then
        DATA_BACKUPS=$(find "$BACKUP_DIR" -name "uploads-*" | sort -r)
        if [ -n "$DATA_BACKUPS" ]; then
            LATEST_DATA=$(echo "$DATA_BACKUPS" | head -1)
            echo "📁 Restoring data from: $LATEST_DATA"
            
            # Stop application
            docker-compose down
            
            # Backup current data
            if [ -d "uploads" ]; then
                sudo mv "uploads" "uploads.backup.$(date +%Y%m%d-%H%M%S)"
            fi
            
            # Restore data
            sudo cp -r "$LATEST_DATA" "uploads"
            
            # Start application
            docker-compose up -d
            
            # Wait for startup
            sleep 15
            
            if docker ps | grep -q pdf-extractor; then
                echo "✅ Data recovery successful"
            else
                echo "❌ Data recovery failed"
            fi
        else
            echo "❌ No data backups found"
        fi
    else
        echo "❌ Backup directory not found"
    fi
}

# Function to container recovery
container_recovery() {
    echo "🐳 Starting container recovery..."
    
    # Stop all containers
    docker-compose down
    
    # Remove problematic containers
    docker rm -f pdf-extractor 2>/dev/null || true
    
    # Clean up Docker
    docker system prune -f
    
    # Rebuild containers
    docker-compose up -d --build --force-recreate
    
    # Wait for startup
    sleep 20
    
    if docker ps | grep -q pdf-extractor; then
        echo "✅ Container recovery successful"
    else
        echo "❌ Container recovery failed"
    fi
}

# Function to configuration recovery
configuration_recovery() {
    echo "🔧 Starting configuration recovery..."
    
    # Check for configuration backups
    if [ -d "$BACKUP_DIR" ]; then
        CONFIG_BACKUPS=$(find "$BACKUP_DIR" -name "config-*" | sort -r)
        if [ -n "$CONFIG_BACKUPS" ]; then
            LATEST_CONFIG=$(echo "$CONFIG_BACKUPS" | head -1)
            echo "⚙️  Restoring configuration from: $LATEST_CONFIG"
            
            # Stop application
            docker-compose down
            
            # Backup current configuration
            sudo cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d-%H%M%S)
            
            # Restore configuration
            sudo cp "$LATEST_CONFIG"/*.yml .
            
            # Start application
            docker-compose up -d
            
            # Wait for startup
            sleep 15
            
            if docker ps | grep -q pdf-extractor; then
                echo "✅ Configuration recovery successful"
            else
                echo "❌ Configuration recovery failed"
            fi
        else
            echo "❌ No configuration backups found"
        fi
    else
        echo "❌ Backup directory not found"
    fi
}

# Function to log recovery
log_recovery() {
    echo "📝 Starting log recovery..."
    
    # Check for log backups
    if [ -d "$BACKUP_DIR" ]; then
        LOG_BACKUPS=$(find "$BACKUP_DIR" -name "logs-*" | sort -r)
        if [ -n "$LOG_BACKUPS" ]; then
            LATEST_LOGS=$(echo "$LOG_BACKUPS" | head -1)
            echo "📝 Restoring logs from: $LATEST_LOGS"
            
            # Backup current logs
            if [ -d "logs" ]; then
                sudo mv "logs" "logs.backup.$(date +%Y%m%d-%H%M%S)"
            fi
            
            # Restore logs
            sudo cp -r "$LATEST_LOGS" "logs"
            
            echo "✅ Log recovery successful"
        else
            echo "❌ No log backups found"
        fi
    else
        echo "❌ Backup directory not found"
    fi
}

# Function to network recovery
network_recovery() {
    echo "🌐 Starting network recovery..."
    
    # Check network connectivity
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        echo "✅ Internet connectivity: OK"
    else
        echo "❌ Internet connectivity: FAILED"
    fi
    
    # Check local network
    NAS_IP=$(hostname -I | awk '{print $1}')
    if ping -c 1 "$NAS_IP" > /dev/null 2>&1; then
        echo "✅ Local network: OK"
    else
        echo "❌ Local network: FAILED"
    fi
    
    # Check port 5000
    if netstat -tlnp | grep -q :5000; then
        echo "✅ Port 5000: LISTENING"
    else
        echo "❌ Port 5000: NOT LISTENING"
    fi
    
    # Check firewall
    if iptables -L | grep -q "5000"; then
        echo "✅ Firewall: PORT 5000 OPEN"
    else
        echo "⚠️  Firewall: PORT 5000 NOT CONFIGURED"
    fi
    
    # Restart network services
    echo "🔄 Restarting network services..."
    docker-compose restart
    
    # Wait for startup
    sleep 15
    
    if docker ps | grep -q pdf-extractor; then
        echo "✅ Network recovery successful"
    else
        echo "❌ Network recovery failed"
    fi
}

# Function to backup verification
backup_verification() {
    echo "💾 Verifying backups..."
    
    if [ -d "$BACKUP_DIR" ]; then
        echo "📁 Backup directory exists: $BACKUP_DIR"
        
        # List all backups
        echo "📦 Available backups:"
        ls -la "$BACKUP_DIR"
        
        # Check backup integrity
        for backup in "$BACKUP_DIR"/*; do
            if [ -f "$backup" ]; then
                echo "🔍 Checking: $(basename "$backup")"
                if tar -tzf "$backup" > /dev/null 2>&1; then
                    echo "✅ Backup integrity: OK"
                else
                    echo "❌ Backup integrity: CORRUPTED"
                fi
            fi
        done
    else
        echo "❌ Backup directory not found"
    fi
}

# Function to system diagnostics
system_diagnostics() {
    echo "🔍 Running system diagnostics..."
    
    echo "🖥️  System Information:"
    echo "   OS: $(uname -a)"
    echo "   Uptime: $(uptime)"
    echo "   Load: $(cat /proc/loadavg)"
    
    echo ""
    echo "💾 Storage:"
    df -h
    
    echo ""
    echo "🧠 Memory:"
    free -h
    
    echo ""
    echo "⚡ CPU:"
    lscpu | grep "Model name"
    lscpu | grep "CPU(s)"
    
    echo ""
    echo "🌐 Network:"
    echo "   IP Address: $(hostname -I | awk '{print $1}')"
    echo "   Hostname: $(hostname)"
    
    echo ""
    echo "🐳 Docker:"
    echo "   Version: $(docker --version)"
    echo "   Containers: $(docker ps -q | wc -l) running"
    echo "   Images: $(docker images -q | wc -l) available"
    
    echo ""
    echo "📁 PDF Extractor:"
    echo "   Directory: $APP_DIR"
    echo "   Database: $(du -h instance/rfms_xtracr.db 2>/dev/null | cut -f1 || echo 'Not found')"
    echo "   Uploads: $(find uploads -type f 2>/dev/null | wc -l) files"
    echo "   Logs: $(find logs -name "*.log" 2>/dev/null | wc -l) files"
    
    echo ""
    echo "🔍 Error Analysis:"
    if [ -d "logs" ]; then
        echo "   Recent errors:"
        find logs -name "*.log" -exec grep -l "ERROR" {} \; | head -5 | while read logfile; do
            echo "     $(basename "$logfile"): $(grep -c "ERROR" "$logfile") errors"
        done
    fi
}

# Main recovery loop
while true; do
    show_recovery_menu
    
    case $choice in
        1)
            complete_system_recovery
            ;;
        2)
            database_recovery
            ;;
        3)
            data_recovery
            ;;
        4)
            container_recovery
            ;;
        5)
            configuration_recovery
            ;;
        6)
            log_recovery
            ;;
        7)
            network_recovery
            ;;
        8)
            backup_verification
            ;;
        9)
            system_diagnostics
            ;;
        10)
            echo "👋 Exiting disaster recovery"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 1-10."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done

