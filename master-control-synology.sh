#!/bin/bash

# PDF Extractor Master Control Script for Synology NAS
# This script provides complete control over your PDF Extractor installation

echo "=========================================="
echo "PDF Extractor Master Control"
echo "=========================================="

APP_DIR="/volume1/docker/pdf-extractor"
SCRIPTS_DIR="$APP_DIR/scripts"

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application directory not found: $APP_DIR"
    echo "Please run the setup script first."
    exit 1
fi

cd "$APP_DIR"

# Create scripts directory
mkdir -p "$SCRIPTS_DIR"

# Function to show master menu
show_master_menu() {
    echo ""
    echo "🎛️  PDF Extractor Master Control"
    echo "================================"
    echo "1. 🚀 Quick Setup"
    echo "2. 🔄 Complete Setup"
    echo "3. 📊 Status Dashboard"
    echo "4. 🛠️  Management Suite"
    echo "5. 🔧 Configuration"
    echo "6. 🔍 Troubleshooting"
    echo "7. 🔒 Security Hardening"
    echo "8. ⚡ Performance Optimization"
    echo "9. 💾 Backup & Recovery"
    echo "10. 🚨 Disaster Recovery"
    echo "11. 📈 Monitoring & Alerts"
    echo "12. 🎯 Maintenance"
    echo "13. 📋 System Information"
    echo "14. 🔄 Migration"
    echo "15. ❌ Exit"
    echo ""
    read -p "Select an option (1-15): " choice
}

# Function to quick setup
quick_setup() {
    echo "🚀 Starting quick setup..."
    if [ -f "quick-setup-synology.sh" ]; then
        ./quick-setup-synology.sh
    else
        echo "❌ Quick setup script not found"
    fi
}

# Function to complete setup
complete_setup() {
    echo "🔄 Starting complete setup..."
    if [ -f "auto-setup-synology.sh" ]; then
        ./auto-setup-synology.sh
    else
        echo "❌ Complete setup script not found"
    fi
}

# Function to show status dashboard
status_dashboard() {
    echo "📊 PDF Extractor Status Dashboard"
    echo "================================="
    
    # Container status
    if docker ps | grep -q pdf-extractor; then
        echo "✅ Container: Running"
        CONTAINER_STATUS=$(docker ps --format "table {{.Status}}" | grep pdf-extractor)
        echo "📊 Status: $CONTAINER_STATUS"
    else
        echo "❌ Container: Stopped"
    fi
    
    # Application health
    if curl -s -f "http://localhost:5000/api/rfms-status" > /dev/null; then
        echo "✅ Application: Healthy"
    else
        echo "❌ Application: Unhealthy"
    fi
    
    # Resource usage
    echo ""
    echo "💻 Resource Usage:"
    docker stats --no-stream pdf-extractor 2>/dev/null || echo "   Container not running"
    
    # Disk usage
    echo ""
    echo "💾 Disk Usage:"
    df -h /volume1 | tail -1
    
    # Memory usage
    echo ""
    echo "🧠 Memory Usage:"
    free -h | grep Mem
    
    # CPU usage
    echo ""
    echo "⚡ CPU Usage:"
    top -bn1 | grep "Cpu(s)"
    
    # Network status
    echo ""
    echo "🌐 Network Status:"
    NAS_IP=$(hostname -I | awk '{print $1}')
    echo "   NAS IP: $NAS_IP"
    echo "   Application URL: http://$NAS_IP:5000"
    
    # Recent errors
    echo ""
    echo "📝 Recent Errors:"
    docker-compose logs --tail=10 2>&1 | grep -i error | tail -3 || echo "   No recent errors"
    
    # Backup status
    echo ""
    echo "💾 Backup Status:"
    if [ -d "/volume1/backup/pdf-extractor" ]; then
        BACKUP_COUNT=$(ls /volume1/backup/pdf-extractor | wc -l)
        echo "   Backups available: $BACKUP_COUNT"
    else
        echo "   No backups found"
    fi
}

# Function to run management suite
management_suite() {
    echo "🛠️  Starting Management Suite..."
    if [ -f "manage-synology.sh" ]; then
        ./manage-synology.sh
    else
        echo "❌ Management suite script not found"
    fi
}

# Function to run configuration
configuration() {
    echo "🔧 Starting Configuration..."
    if [ -f "configure-synology.sh" ]; then
        ./configure-synology.sh
    else
        echo "❌ Configuration script not found"
    fi
}

# Function to run troubleshooting
troubleshooting() {
    echo "🔍 Starting Troubleshooting..."
    if [ -f "troubleshoot-synology.sh" ]; then
        ./troubleshoot-synology.sh
    else
        echo "❌ Troubleshooting script not found"
    fi
}

# Function to run security hardening
security_hardening() {
    echo "🔒 Starting Security Hardening..."
    if [ -f "security-harden-synology.sh" ]; then
        ./security-harden-synology.sh
    else
        echo "❌ Security hardening script not found"
    fi
}

# Function to run performance optimization
performance_optimization() {
    echo "⚡ Starting Performance Optimization..."
    if [ -f "optimize-performance-synology.sh" ]; then
        ./optimize-performance-synology.sh
    else
        echo "❌ Performance optimization script not found"
    fi
}

# Function to run backup and recovery
backup_recovery() {
    echo "💾 Starting Backup & Recovery..."
    echo "1. Create Backup"
    echo "2. Restore from Backup"
    echo "3. Verify Backup"
    echo "4. Back to main menu"
    echo ""
    read -p "Select an option (1-4): " backup_choice
    
    case $backup_choice in
        1)
            if [ -f "backup-synology.sh" ]; then
                ./backup-synology.sh
            else
                echo "❌ Backup script not found"
            fi
            ;;
        2)
            if [ -f "disaster-recovery-synology.sh" ]; then
                ./disaster-recovery-synology.sh
            else
                echo "❌ Recovery script not found"
            fi
            ;;
        3)
            if [ -d "/volume1/backup/pdf-extractor" ]; then
                echo "📦 Available backups:"
                ls -la /volume1/backup/pdf-extractor
            else
                echo "❌ No backups found"
            fi
            ;;
        4)
            return
            ;;
        *)
            echo "❌ Invalid option"
            ;;
    esac
}

# Function to run disaster recovery
disaster_recovery() {
    echo "🚨 Starting Disaster Recovery..."
    if [ -f "disaster-recovery-synology.sh" ]; then
        ./disaster-recovery-synology.sh
    else
        echo "❌ Disaster recovery script not found"
    fi
}

# Function to run monitoring and alerts
monitoring_alerts() {
    echo "📈 Starting Monitoring & Alerts..."
    echo "1. Start Monitoring"
    echo "2. View Monitoring Logs"
    echo "3. Configure Alerts"
    echo "4. Back to main menu"
    echo ""
    read -p "Select an option (1-4): " monitor_choice
    
    case $monitor_choice in
        1)
            if [ -f "monitor-synology.sh" ]; then
                ./monitor-synology.sh
            else
                echo "❌ Monitoring script not found"
            fi
            ;;
        2)
            if [ -d "logs" ]; then
                echo "📝 Monitoring logs:"
                tail -20 logs/monitor.log 2>/dev/null || echo "No monitoring logs found"
            else
                echo "❌ Logs directory not found"
            fi
            ;;
        3)
            echo "🔔 Alert Configuration:"
            echo "   Email alerts: Configure in monitor-synology.sh"
            echo "   Log alerts: Configure in logrotate.conf"
            echo "   System alerts: Configure in DSM"
            ;;
        4)
            return
            ;;
        *)
            echo "❌ Invalid option"
            ;;
    esac
}

# Function to run maintenance
maintenance() {
    echo "🎯 Starting Maintenance..."
    if [ -f "maintenance-synology.sh" ]; then
        ./maintenance-synology.sh
    else
        echo "❌ Maintenance script not found"
    fi
}

# Function to show system information
system_information() {
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
    
    echo ""
    echo "🔧 Available Scripts:"
    ls -la *.sh 2>/dev/null | while read line; do
        echo "   $(echo $line | awk '{print $9}')"
    done
}

# Function to run migration
migration() {
    echo "🔄 Starting Migration..."
    if [ -f "migrate-synology.sh" ]; then
        ./migrate-synology.sh
    else
        echo "❌ Migration script not found"
    fi
}

# Function to create all scripts
create_all_scripts() {
    echo "📝 Creating all management scripts..."
    
    # List of all scripts to create
    scripts=(
        "quick-setup-synology.sh"
        "auto-setup-synology.sh"
        "manage-synology.sh"
        "configure-synology.sh"
        "troubleshoot-synology.sh"
        "security-harden-synology.sh"
        "optimize-performance-synology.sh"
        "backup-synology.sh"
        "disaster-recovery-synology.sh"
        "monitor-synology.sh"
        "maintenance-synology.sh"
        "migrate-synology.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            echo "✅ $script exists"
        else
            echo "❌ $script not found"
        fi
    done
}

# Main control loop
while true; do
    show_master_menu
    
    case $choice in
        1)
            quick_setup
            ;;
        2)
            complete_setup
            ;;
        3)
            status_dashboard
            ;;
        4)
            management_suite
            ;;
        5)
            configuration
            ;;
        6)
            troubleshooting
            ;;
        7)
            security_hardening
            ;;
        8)
            performance_optimization
            ;;
        9)
            backup_recovery
            ;;
        10)
            disaster_recovery
            ;;
        11)
            monitoring_alerts
            ;;
        12)
            maintenance
            ;;
        13)
            system_information
            ;;
        14)
            migration
            ;;
        15)
            echo "👋 Exiting PDF Extractor Master Control"
            exit 0
            ;;
        *)
            echo "❌ Invalid option. Please select 1-15."
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done

