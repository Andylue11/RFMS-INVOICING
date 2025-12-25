#!/bin/bash

# Run setup with sudo to bypass permission issues
cd /volume1/docker/pdf-extractor

echo "=========================================="
echo "PDF Extractor Setup (with sudo)"
echo "=========================================="

# Create directories
echo "📁 Creating directories..."
sudo mkdir -p instance uploads logs static
sudo chmod 755 instance uploads logs static

# Set ownership
sudo chown -R atoz:users instance uploads logs static

echo ""
echo "🔨 Building Docker image..."
sudo docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Failed to build Docker image"
    exit 1
fi

echo ""
echo "🚀 Starting application..."
sudo docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start application"
    exit 1
fi

echo ""
echo "⏳ Waiting for application to start..."
sleep 20

# Check status (without sudo since we're just reading)
echo ""
echo "📊 Checking status..."
if sudo docker ps | grep -q pdf-extractor; then
    echo "🎉 SUCCESS! PDF Extractor is now running!"
    echo ""
    echo "🌐 URL: http://192.168.0.201:5000"
    echo ""
    echo "📊 Container Status:"
    sudo docker ps | grep pdf-extractor
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: sudo docker-compose logs -f"
    echo "   Restart: sudo docker-compose restart"
    echo "   Stop: sudo docker-compose down"
    echo "   Start: sudo docker-compose up -d"
else
    echo "❌ Application failed to start"
    echo "Logs:"
    sudo docker-compose logs --tail=30
fi

echo ""
echo "=========================================="
