#!/bin/bash

# PDF Extractor Synology NAS Deployment Script
# Run this script on your Synology NAS

set -e  # Exit on any error

echo "=========================================="
echo "PDF Extractor Synology NAS Deployment"
echo "=========================================="

# Configuration
APP_NAME="pdf-extractor"
APP_DIR="/volume1/docker/$APP_NAME"
BACKUP_DIR="/volume1/docker/$APP_NAME-backup"

# Check if running as root or admin
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Running as root. Consider using admin user instead."
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker package from Package Center first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not available. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker and docker-compose are available"

# Create application directory
echo "📁 Creating application directory: $APP_DIR"
sudo mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Create necessary subdirectories
echo "📁 Creating subdirectories..."
sudo mkdir -p instance uploads logs static
sudo chmod 755 instance uploads logs static

# Copy application files (assuming they're in current directory)
echo "📋 Copying application files..."
if [ -f "app.py" ]; then
    sudo cp app.py "$APP_DIR/"
    sudo cp -r utils "$APP_DIR/"
    sudo cp -r templates "$APP_DIR/"
    sudo cp -r static "$APP_DIR/"
    sudo cp models.py "$APP_DIR/"
    sudo cp requirements.txt "$APP_DIR/"
    sudo cp app_production.py "$APP_DIR/"
    sudo cp Dockerfile-synology "$APP_DIR/Dockerfile"
    sudo cp docker-compose-synology.yml "$APP_DIR/docker-compose.yml"
else
    echo "❌ Application files not found in current directory"
    echo "Please ensure you're running this script from the PDF Extractor directory"
    exit 1
fi

# Set proper ownership
echo "🔐 Setting proper permissions..."
sudo chown -R $(whoami):users "$APP_DIR"
sudo chmod -R 755 "$APP_DIR"

# Create backup of existing data if it exists
if [ -d "$APP_DIR/instance" ] && [ "$(ls -A $APP_DIR/instance)" ]; then
    echo "💾 Creating backup of existing data..."
    sudo mkdir -p "$BACKUP_DIR"
    sudo cp -r "$APP_DIR/instance" "$BACKUP_DIR/instance-$(date +%Y%m%d-%H%M%S)"
fi

# Build and start the application
echo "🔨 Building and starting PDF Extractor..."
cd "$APP_DIR"

# Stop existing container if running
if docker ps -q -f name=$APP_NAME | grep -q .; then
    echo "🛑 Stopping existing container..."
    docker stop $APP_NAME || true
    docker rm $APP_NAME || true
fi

# Build and start
docker-compose up -d --build

# Wait for container to start
echo "⏳ Waiting for application to start..."
sleep 15

# Check if the service is running
if docker ps | grep -q $APP_NAME; then
    echo "✅ PDF Extractor is running successfully!"
    echo ""
    echo "🌐 Access Information:"
    echo "   Internal: http://$(hostname -I | awk '{print $1}'):5000"
    echo "   Local: http://localhost:5000"
    echo ""
    echo "📁 Data Location: $APP_DIR"
    echo "   Database: $APP_DIR/instance/"
    echo "   Uploads: $APP_DIR/uploads/"
    echo "   Logs: $APP_DIR/logs/"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Restart: docker-compose restart"
    echo "   Stop: docker-compose down"
    echo "   Update: git pull && docker-compose up -d --build"
    echo ""
    echo "⚠️  Next Steps:"
    echo "   1. Configure Synology Firewall (Control Panel > Security > Firewall)"
    echo "   2. Add rule for port 5000 (TCP)"
    echo "   3. Optional: Set up reverse proxy for external access"
    echo "   4. Test the application in your browser"
else
    echo "❌ Failed to start PDF Extractor"
    echo "📋 Check logs with: docker-compose logs"
    exit 1
fi

echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
