#!/bin/bash

# PDF Extractor Quick Setup - Now that permissions are fixed
cd /volume1/docker/pdf-extractor

echo "=========================================="
echo "PDF Extractor Setup"
echo "=========================================="

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p instance uploads logs static
chmod 755 instance uploads logs static

# Make scripts executable
echo "🔐 Setting permissions..."
chmod +x *.sh 2>/dev/null || true

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "📝 Creating docker-compose.yml..."
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  pdf-extractor:
    build: .
    container_name: pdf-extractor
    ports:
      - "5000:5000"
    volumes:
      - /volume1/docker/pdf-extractor/instance:/app/instance
      - /volume1/docker/pdf-extractor/uploads:/app/uploads
      - /volume1/docker/pdf-extractor/logs:/app/logs
      - /volume1/docker/pdf-extractor/static:/app/static
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=production-secret-key-change-this
    restart: unless-stopped
    networks:
      - pdf-extractor-network

networks:
  pdf-extractor-network:
    driver: bridge
EOF
fi

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "📝 Creating Dockerfile..."
    cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p uploads logs instance static

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "app.py"]
EOF
fi

echo ""
echo "🔨 Building Docker image (this may take a few minutes)..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Failed to build Docker image"
    echo "Check the error messages above"
    exit 1
fi

echo ""
echo "🚀 Starting application..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start application"
    exit 1
fi

echo ""
echo "⏳ Waiting for application to start..."
sleep 20

# Check status
echo ""
echo "📊 Checking status..."
if docker ps | grep -q pdf-extractor; then
    echo "🎉 SUCCESS! PDF Extractor is now running!"
    echo ""
    echo "📋 Application Information:"
    echo "   🌐 URL: http://192.168.0.201:5000"
    echo "   📁 Directory: /volume1/docker/pdf-extractor"
    echo ""
    echo "📊 Container Status:"
    docker ps | grep pdf-extractor
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Restart: docker-compose restart"
    echo "   Stop: docker-compose down"
    echo "   Start: docker-compose up -d"
else
    echo "❌ Application failed to start"
    echo ""
    echo "📝 Recent logs:"
    docker-compose logs --tail=30
fi

echo ""
echo "=========================================="
