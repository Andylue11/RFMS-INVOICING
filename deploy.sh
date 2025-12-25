#!/bin/bash

# PDF Extractor Deployment Script for NAS Server
# Run this script on your NAS server

echo "=== PDF Extractor NAS Deployment ==="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p instance
mkdir -p uploads
mkdir -p static

# Set proper permissions
chmod 755 instance uploads static

# Build and start the application
echo "Building and starting PDF Extractor..."
docker-compose up -d --build

# Check if the service is running
sleep 10
if docker-compose ps | grep -q "Up"; then
    echo "✅ PDF Extractor is running successfully!"
    echo "🌐 Access the application at: http://YOUR_NAS_IP:5000"
    echo "📁 Data is persisted in: ./instance and ./uploads"
else
    echo "❌ Failed to start PDF Extractor. Check logs with: docker-compose logs"
    exit 1
fi

echo "=== Deployment Complete ==="
