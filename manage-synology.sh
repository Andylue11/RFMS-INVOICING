#!/bin/bash

# PDF Extractor Complete Management Suite for Synology NAS
# This script provides a comprehensive management interface

echo "=========================================="
echo "PDF Extractor Management Suite"
echo "=========================================="

APP_DIR="/volume1/docker/pdf-extractor"

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application directory not found: $APP_DIR"
    echo "Please run the deployment script first."
    exit 1
fi

cd "$APP_DIR"

# Function to show main menu
show_main_menu() {
    echo ""
    echo "🔧 PDF Extractor Management Suite"
    echo "=================================="
    echo "1. 📊 Status & Health Check"
    echo "2. 🚀 Start Application"
    echo "3. 🛑 Stop Application"
    echo "4. 🔄 Restart Application"
    echo "5. 📝 View Logs"
    echo "6. 💾 Backup Data"
    echo "7. 🔄 Update Application"
    echo "8. 🧹 Maintenance"
    echo "9. ⚙️  Configuration"
    echo "10. 🔍 Troubleshooting"
    echo "11. 🔒 Security Audit"
    echo "12. 📈 Performance Monitor"
    echo "13. 🌐 Network Test"
    echo "14. 📋 System Information"
    echo "15. ❌ Exit"
    echo ""
    read -p "Select an option (1-15): " choice
}

# Function to show status
show_status() {
    echo "📊 PDF Extractor Status"
    echo "======================="
    
    if docker ps | grep -q pdf-extractor; then
        echo "✅ Status: Running"
        CONTAINER_STATUS=$(docker ps --format "table {{.Status}}" | grep pdf-extractor)
        echo "📊 Container: $CONTAINER_STATUS"
    else
        echo "❌ Status: Stopped"
    fi
    
    echo ""
    echo "💾 Disk Usage:"
    df -h /volume1 | tail -1
    
    echo ""
    echo "🧠 Memory Usage:"
    free -h | grep Mem
    
    echo ""
    echo "⚡ CPU Usage:"
    top -bn1 | grep "Cpu(s)"
    
    echo ""
    echo "🌐 Network Status:"
    NAS_IP=$(hostname -I | awk '{print $1}')
    echo "   NAS IP: $NAS_IP"
    echo "   Application URL: http://$NAS_IP:5000"
    
    if curl -s -f "http://localhost:5000/api/rfms-status" > /dev/null; then
        echo "   ✅ Application responding"
    else
        echo "   ❌ Application not responding"
    fi
}

# Function to start application
start_application() {
    echo "🚀 Starting PDF Extractor..."
    docker-compose up -d
    sleep 10
    if docker ps | grep -q pdf-extractor; then
        echo "✅ Application started successfully"
    else
        echo "❌ Failed to start application"
        echo "Check logs: docker-compose logs"
    fi
}

# Function to stop application
stop_application() {
    echo "🛑 Stopping PDF Extractor..."
    docker-compose down
    echo "✅ Application stopped"
}

# Function to restart application
restart_application() {
    echo "🔄 Restarting PDF Extractor..."
    docker-compose restart
    sleep 10
    if docker ps | grep -q pdf-extractor; then
        echo "✅ Application restarted successfully"
    else
        echo "❌ Failed to restart application"
        echo "Check logs: docker-compose logs"
    fi
}

# Function to view logs
view_logs() {
    echo "📝 PDF Extractor Logs"
    echo "===================="
    echo "1. View recent logs"
    echo "2. View error logs"
    echo "3. View all logs"
    echo "4. Follow logs (real-time)"
    echo "5. Back to main menu"
    echo ""
    read -p "Select an option (1-5): " log_choice
    
    case $log_choice in
        1)
            echo "Recent logs:"
            docker-compose logs --tail=50
            ;;
        2)
            echo "Error logs:"
            docker-compose logs 2>&1 | grep -i error
            ;;
        3)
            echo "All logs:"
            docker-compose logs
            ;;
        4)
            echo "Following logs (Press Ctrl+C to stop):"
            docker-compose logs -f
            ;;
        5)
            return
            ;;
        *)
            echo "❌ Invalid option"
            ;;
    esac
}

# Function to backup data
backup_data() {
    echo "💾 Backing up PDF Extractor data..."
    ./backup-synology.sh
}

# Function to update application
update_application() {
    echo "🔄 Updating PDF Extractor..."
    ./update-synology.sh
}

# Function to run maintenance
run_maintenance() {
    echo "🧹 Running maintenance..."
    ./maintenance-synology.sh
}

# Function to configure application
configure_application() {
    echo "⚙️  Configuring PDF Extractor..."
    ./configure-synology.sh
}

# Function to troubleshoot
troubleshoot() {
    echo "🔍 Troubleshooting PDF Extractor..."
    ./troubleshoot-synology.sh
}

# Function to run security audit
security_audit() {
    echo "🔒 Running security audit..."
    ./security-audit.sh
}

# Function to monitor performance
performance_monitor() {
    echo "📈 Performance Monitor"
    echo "====================="
    echo "Monitoring for 60 seconds..."
    echo "Press Ctrl+C to stop early"
    echo ""
    
    for i in {1..60}; do
        echo "Time: $(date '+%H:%M:%S')"
        echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')%"
        echo "Memory: $(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')%"
        echo "Disk: $(df -h /volume1 | tail -1 | awk '{print $5}')"
        echo "Connections: $(netstat -an | grep :5000 | wc -l)"
        echo "---"
        sleep 1
    done
}

# Function to test network
network_test() {
    echo "🌐 Network Test"
    echo "=============="
    
    NAS_IP=$(hostname -I | awk '{print $1}')
    
    echo "Testing localhost:5000..."
    if curl -s -f "http://localhost:5000/api/rfms-status" > /dev/null; then
        echo "✅ Local connection: OK"
    else
        echo "❌ Local connection: FAILED"
    fi
    
    echo "Testing $NAS_IP:5000..."
    if curl -s -f "http://$NAS_IP:5000/api/rfms-status" > /dev/null; then
        echo "✅ External connection: OK"
    else
        echo "❌ External connection: FAILED"
    fi
    
    echo "Testing port 5000..."
    if netstat -tlnp | grep -q :5000; then
        echo "✅ Port 5000: LISTENING"
    else
        echo "❌ Port 5000: NOT LISTENING"
    fi
    
    echo "Testing firewall..."
    if iptables -L | grep -q "5000"; then
        echo "✅ Firewall: PORT 5000 OPEN"
    else
        echo "⚠️  Firewall: PORT 5000 NOT CONFIGURED"
    fi
}

# Function to show system information
system_info() {
    echo "📋 System Information"
    echo "===================="
    
    echo "🖥️  System:"
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
}

# Main menu loop
while true; do
    show_main_menu
    
    case $choice in
        1)
            show_status
            ;;
        2)
            start_application
            ;;
        3)
            stop_application
            ;;
        4)
            restart_application
            ;;
        5)
            view_logs
            ;;
        6)
            backup_data
            ;;
        7)
            update_application
            ;;
        8)
            run_maintenance
            ;;
        9)
            configure_application
            ;;
        10)
            troubleshoot
            ;;
        11)
            security_audit
            ;;
        12)
            performance_monitor
            ;;
        13)
            network_test
            ;;
        14)
            system_info
            ;;
        15)
            echo "👋 Exiting PDF Extractor Management Suite"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 1-15."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done

