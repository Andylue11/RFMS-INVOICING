#!/bin/bash

# PDF Extractor Installation Script for NAS Server
# Run this script on your NAS server

echo "=== PDF Extractor NAS Installation ==="

# Set variables
APP_DIR="/opt/pdf-extractor"
SERVICE_USER="www-data"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx supervisor

# Create application directory
echo "Creating application directory..."
mkdir -p $APP_DIR
cd $APP_DIR

# Copy application files (assuming they're in current directory)
echo "Copying application files..."
cp -r . $APP_DIR/

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p instance uploads static
chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR

# Install systemd service
echo "Installing systemd service..."
cp pdf-extractor.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable pdf-extractor
systemctl start pdf-extractor

# Configure Nginx (optional - for reverse proxy)
echo "Configuring Nginx..."
cat > /etc/nginx/sites-available/pdf-extractor << EOF
server {
    listen 80;
    server_name YOUR_NAS_IP;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/pdf-extractor /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Check service status
sleep 5
if systemctl is-active --quiet pdf-extractor; then
    echo "✅ PDF Extractor is running successfully!"
    echo "🌐 Access the application at: http://YOUR_NAS_IP"
    echo "📁 Application directory: $APP_DIR"
else
    echo "❌ Failed to start PDF Extractor. Check logs with: journalctl -u pdf-extractor"
    exit 1
fi

echo "=== Installation Complete ==="
