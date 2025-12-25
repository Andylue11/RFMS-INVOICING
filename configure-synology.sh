#!/bin/bash

# PDF Extractor Configuration Script for Synology NAS
# This script helps configure various settings for the PDF Extractor

echo "=========================================="
echo "PDF Extractor Configuration Script"
echo "=========================================="

APP_DIR="/volume1/docker/pdf-extractor"

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application directory not found: $APP_DIR"
    echo "Please run the deployment script first."
    exit 1
fi

cd "$APP_DIR"

echo "⚙️  PDF Extractor Configuration"
echo ""

# Function to update docker-compose.yml
update_docker_compose() {
    local key="$1"
    local value="$2"
    
    if grep -q "^[[:space:]]*$key:" docker-compose.yml; then
        sed -i "s/^[[:space:]]*$key:.*/$key: $value/" docker-compose.yml
    else
        # Add to environment section
        sed -i "/environment:/a\\      - $key=$value" docker-compose.yml
    fi
}

# 1. Configure secret key
echo "🔐 Configuring secret key..."
read -p "Enter a secret key (or press Enter for auto-generated): " secret_key
if [ -z "$secret_key" ]; then
    secret_key=$(openssl rand -base64 32 2>/dev/null || echo "your-secret-key-$(date +%s)")
fi
update_docker_compose "SECRET_KEY" "$secret_key"
echo "✅ Secret key configured"

# 2. Configure port
echo ""
echo "🌐 Configuring port..."
read -p "Enter port number (default: 5000): " port
if [ -z "$port" ]; then
    port="5000"
fi
sed -i "s/\"5000:5000\"/\"$port:5000\"/" docker-compose.yml
echo "✅ Port configured: $port"

# 3. Configure resource limits
echo ""
echo "💻 Configuring resource limits..."
read -p "Enter memory limit in MB (default: 1024): " memory_limit
if [ -z "$memory_limit" ]; then
    memory_limit="1024"
fi

# Add resource limits to docker-compose.yml
if ! grep -q "deploy:" docker-compose.yml; then
    sed -i "/restart: unless-stopped/a\\    deploy:\\n      resources:\\n        limits:\\n          memory: ${memory_limit}M" docker-compose.yml
fi
echo "✅ Memory limit configured: ${memory_limit}MB"

# 4. Configure log rotation
echo ""
echo "📝 Configuring log rotation..."
cat > logrotate.conf << EOF
/volume1/docker/pdf-extractor/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
echo "✅ Log rotation configured"

# 5. Configure backup schedule
echo ""
echo "💾 Configuring backup schedule..."
read -p "Enable automatic backups? (y/n): " enable_backup
if [ "$enable_backup" = "y" ] || [ "$enable_backup" = "Y" ]; then
    # Create cron job for daily backups
    (crontab -l 2>/dev/null; echo "0 2 * * * $APP_DIR/backup-synology.sh") | crontab -
    echo "✅ Daily backups scheduled at 2:00 AM"
else
    echo "⚠️  Automatic backups disabled"
fi

# 6. Configure monitoring
echo ""
echo "📊 Configuring monitoring..."
read -p "Enable monitoring alerts? (y/n): " enable_monitoring
if [ "$enable_monitoring" = "y" ] || [ "$enable_monitoring" = "Y" ]; then
    # Create cron job for monitoring
    (crontab -l 2>/dev/null; echo "*/5 * * * * $APP_DIR/monitor-synology.sh") | crontab -
    echo "✅ Monitoring enabled (every 5 minutes)"
else
    echo "⚠️  Monitoring disabled"
fi

# 7. Configure maintenance schedule
echo ""
echo "🧹 Configuring maintenance schedule..."
read -p "Enable weekly maintenance? (y/n): " enable_maintenance
if [ "$enable_maintenance" = "y" ] || [ "$enable_maintenance" = "Y" ]; then
    # Create cron job for weekly maintenance
    (crontab -l 2>/dev/null; echo "0 3 * * 0 $APP_DIR/maintenance-synology.sh") | crontab -
    echo "✅ Weekly maintenance scheduled (Sundays at 3:00 AM)"
else
    echo "⚠️  Automatic maintenance disabled"
fi

# 8. Configure firewall
echo ""
echo "🔥 Configuring firewall..."
read -p "Open port $port in firewall? (y/n): " open_firewall
if [ "$open_firewall" = "y" ] || [ "$open_firewall" = "Y" ]; then
    # Note: This would need to be done through Synology DSM
    echo "⚠️  Please manually configure firewall in DSM:"
    echo "   Control Panel > Security > Firewall"
    echo "   Add rule for port $port (TCP)"
fi

# 9. Create startup script
echo ""
echo "🚀 Creating startup script..."
cat > start.sh << 'EOF'
#!/bin/bash
cd /volume1/docker/pdf-extractor
docker-compose up -d
EOF
chmod +x start.sh
echo "✅ Startup script created"

# 10. Create stop script
echo ""
echo "🛑 Creating stop script..."
cat > stop.sh << 'EOF'
#!/bin/bash
cd /volume1/docker/pdf-extractor
docker-compose down
EOF
chmod +x stop.sh
echo "✅ Stop script created"

# 11. Create restart script
echo ""
echo "🔄 Creating restart script..."
cat > restart.sh << 'EOF'
#!/bin/bash
cd /volume1/docker/pdf-extractor
docker-compose restart
EOF
chmod +x restart.sh
echo "✅ Restart script created"

# Apply configuration
echo ""
echo "🔄 Applying configuration..."
docker-compose down
docker-compose up -d

# Wait for startup
echo "⏳ Waiting for application to start..."
sleep 15

# Verify configuration
if docker ps | grep -q pdf-extractor; then
    echo ""
    echo "✅ Configuration applied successfully!"
    echo ""
    echo "📋 Configuration Summary:"
    echo "   Port: $port"
    echo "   Memory Limit: ${memory_limit}MB"
    echo "   Secret Key: Configured"
    echo "   Log Rotation: Enabled"
    if [ "$enable_backup" = "y" ] || [ "$enable_backup" = "Y" ]; then
        echo "   Automatic Backups: Enabled"
    fi
    if [ "$enable_monitoring" = "y" ] || [ "$enable_monitoring" = "Y" ]; then
        echo "   Monitoring: Enabled"
    fi
    if [ "$enable_maintenance" = "y" ] || [ "$enable_maintenance" = "Y" ]; then
        echo "   Maintenance: Enabled"
    fi
    echo ""
    echo "🌐 Access your application at: http://$(hostname -I | awk '{print $1}'):$port"
else
    echo "❌ Failed to apply configuration"
    echo "Check logs: docker-compose logs"
fi

echo "=========================================="
echo "✅ Configuration Complete!"
echo "=========================================="

