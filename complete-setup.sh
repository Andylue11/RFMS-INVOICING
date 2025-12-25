#!/bin/bash

# Complete Docker setup for PDF Extractor on Synology NAS
# This handles all the setup steps

echo "=========================================="
echo "PDF Extractor Complete Setup"
echo "=========================================="

# Navigate to application directory
cd /volume1/docker/pdf-extractor

# Create directories if they don't exist
echo "📁 Creating directories..."
sudo mkdir -p instance uploads logs static
sudo chmod 755 instance uploads logs static
sudo chown -R atoz:users instance uploads logs static

# Make sure we're in the right directory
echo "📍 Current directory: $(pwd)"
echo "📋 Files in directory:"
ls -la

echo ""
echo "🔨 Building Docker image..."
echo "This may take 2-5 minutes on first build..."
sudo docker-compose build

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Build failed!"
    echo "Checking for common issues..."
    echo ""
    echo "Docker status:"
    sudo systemctl status docker
    echo ""
    echo "Disk space:"
    df -h /volume1
    exit 1
fi

echo ""
echo "🚀 Starting application..."
sudo docker-compose up -d

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Failed to start!"
    echo "Checking logs..."
    sudo docker-compose logs
    exit 1
fi

echo ""
echo "⏳ Waiting 20 seconds for application to start..."
sleep 20

echo ""
echo "📊 Checking container status..."
if sudo docker ps | grep -q pdf-extractor; then
    echo ""
    echo "🎉 SUCCESS! PDF Extractor is running!"
    echo ""
    echo "========================================="
    echo "Application is ready!"
    echo "========================================="
    echo ""
    echo "🌐 Access your application at:"
    echo "   http://192.168.0.201:5000"
    echo ""
    echo "📊 Container Status:"
    sudo docker ps | grep pdf-extractor
    echo ""
    echo "📁 Data Storage:"
    echo "   Instance DB: /volume1/docker/pdf-extractor/instance/"
    echo "   Uploads: /volume1/docker/pdf-extractor/uploads/"
    echo "   Logs: /volume1/docker/pdf-extractor/logs/"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: sudo docker-compose logs -f"
    echo "   Restart: sudo docker-compose restart"
    echo "   Stop: sudo docker-compose down"
    echo "   Start: sudo docker-compose up -d"
    echo "   Status: sudo docker ps | grep pdf-extractor"
    echo ""
else
    echo ""
    echo "⚠️ Container may still be starting or there's an issue"
    echo ""
    echo "Checking all containers:"
    sudo docker ps -a
    echo ""
    echo "Recent logs:"
    sudo docker-compose logs --tail=50
fi

echo ""
echo "=========================================="
