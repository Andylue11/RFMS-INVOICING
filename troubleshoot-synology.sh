#!/bin/bash

# PDF Extractor Troubleshooting Script for Synology NAS
# This script helps diagnose and fix common issues

echo "=========================================="
echo "PDF Extractor Troubleshooting Script"
echo "=========================================="

APP_DIR="/volume1/docker/pdf-extractor"

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application directory not found: $APP_DIR"
    echo "Please run the deployment script first."
    exit 1
fi

cd "$APP_DIR"

echo "🔍 Diagnosing issues..."

# Function to check and fix permissions
fix_permissions() {
    echo "🔐 Fixing permissions..."
    sudo chown -R $(whoami):users "$APP_DIR"
    sudo chmod -R 755 "$APP_DIR"
    echo "✅ Permissions fixed"
}

# Function to clean up Docker
cleanup_docker() {
    echo "🧹 Cleaning up Docker..."
    docker-compose down
    docker system prune -f
    echo "✅ Docker cleaned up"
}

# Function to rebuild application
rebuild_app() {
    echo "🔨 Rebuilding application..."
    docker-compose up -d --build --force-recreate
    echo "✅ Application rebuilt"
}

# Function to check logs
check_logs() {
    echo "📝 Checking application logs..."
    echo "Recent logs:"
    docker-compose logs --tail=20
    echo ""
    echo "Error logs:"
    docker-compose logs 2>&1 | grep -i error | tail -10
}

# Function to check system resources
check_resources() {
    echo "💻 Checking system resources..."
    echo "Disk usage:"
    df -h /volume1
    echo ""
    echo "Memory usage:"
    free -h
    echo ""
    echo "CPU usage:"
    top -bn1 | grep "Cpu(s)"
}

# Function to test network connectivity
test_network() {
    echo "🌐 Testing network connectivity..."
    echo "Testing localhost:5000..."
    if curl -s -f "http://localhost:5000/api/rfms-status" > /dev/null; then
        echo "✅ Local connection working"
    else
        echo "❌ Local connection failed"
    fi
    
    echo "Testing external access..."
    NAS_IP=$(hostname -I | awk '{print $1}')
    if curl -s -f "http://$NAS_IP:5000/api/rfms-status" > /dev/null; then
        echo "✅ External connection working"
    else
        echo "❌ External connection failed"
    fi
}

# Function to check firewall
check_firewall() {
    echo "🔥 Checking firewall..."
    if iptables -L | grep -q "5000"; then
        echo "✅ Port 5000 is open in firewall"
    else
        echo "⚠️  Port 5000 may not be open in firewall"
        echo "Please check DSM Control Panel > Security > Firewall"
    fi
}

# Function to check database
check_database() {
    echo "🗄️  Checking database..."
    if [ -f "instance/rfms_xtracr.db" ]; then
        DB_SIZE=$(du -h instance/rfms_xtracr.db | cut -f1)
        echo "✅ Database exists (Size: $DB_SIZE)"
        
        # Check if database is accessible
        if sqlite3 instance/rfms_xtracr.db "SELECT name FROM sqlite_master WHERE type='table';" > /dev/null 2>&1; then
            echo "✅ Database is accessible"
        else
            echo "❌ Database is corrupted"
            echo "Attempting to repair..."
            sqlite3 instance/rfms_xtracr.db "VACUUM;" 2>/dev/null || true
            echo "✅ Database repair attempted"
        fi
    else
        echo "❌ Database file not found"
        echo "Creating new database..."
        mkdir -p instance
        touch instance/rfms_xtracr.db
        echo "✅ New database created"
    fi
}

# Function to check uploads directory
check_uploads() {
    echo "📁 Checking uploads directory..."
    if [ -d "uploads" ]; then
        UPLOAD_COUNT=$(find uploads -type f | wc -l)
        UPLOAD_SIZE=$(du -sh uploads 2>/dev/null | cut -f1 || echo "0")
        echo "✅ Uploads directory exists ($UPLOAD_COUNT files, $UPLOAD_SIZE)"
    else
        echo "❌ Uploads directory not found"
        echo "Creating uploads directory..."
        mkdir -p uploads
        chmod 755 uploads
        echo "✅ Uploads directory created"
    fi
}

# Function to check logs directory
check_logs_dir() {
    echo "📝 Checking logs directory..."
    if [ -d "logs" ]; then
        LOG_COUNT=$(find logs -name "*.log" | wc -l)
        echo "✅ Logs directory exists ($LOG_COUNT log files)"
    else
        echo "❌ Logs directory not found"
        echo "Creating logs directory..."
        mkdir -p logs
        chmod 755 logs
        echo "✅ Logs directory created"
    fi
}

# Function to restart services
restart_services() {
    echo "🔄 Restarting services..."
    docker-compose down
    sleep 5
    docker-compose up -d
    sleep 15
    echo "✅ Services restarted"
}

# Function to show troubleshooting menu
show_menu() {
    echo ""
    echo "🔧 Troubleshooting Menu:"
    echo "1. Check application logs"
    echo "2. Check system resources"
    echo "3. Test network connectivity"
    echo "4. Check firewall"
    echo "5. Check database"
    echo "6. Check uploads directory"
    echo "7. Check logs directory"
    echo "8. Fix permissions"
    echo "9. Clean up Docker"
    echo "10. Rebuild application"
    echo "11. Restart services"
    echo "12. Run all checks"
    echo "13. Exit"
    echo ""
    read -p "Select an option (1-13): " choice
}

# Main troubleshooting loop
while true; do
    show_menu
    
    case $choice in
        1)
            check_logs
            ;;
        2)
            check_resources
            ;;
        3)
            test_network
            ;;
        4)
            check_firewall
            ;;
        5)
            check_database
            ;;
        6)
            check_uploads
            ;;
        7)
            check_logs_dir
            ;;
        8)
            fix_permissions
            ;;
        9)
            cleanup_docker
            ;;
        10)
            rebuild_app
            ;;
        11)
            restart_services
            ;;
        12)
            echo "🔍 Running all checks..."
            check_logs
            check_resources
            test_network
            check_firewall
            check_database
            check_uploads
            check_logs_dir
            ;;
        13)
            echo "👋 Exiting troubleshooting script"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 1-13."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done

