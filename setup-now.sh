#!/bin/bash

# PDF Extractor Quick Setup Script for Synology NAS
# Run this script on your Synology NAS

echo "=========================================="
echo "PDF Extractor Quick Setup"
echo "=========================================="

APP_DIR="/volume1/docker/pdf-extractor"

# Navigate to application directory
cd "$APP_DIR" || {
    echo "❌ Cannot access $APP_DIR"
    echo "Please ensure the files are in the correct location"
    exit 1
}

echo "📍 Current directory: $(pwd)"
echo ""

# Check if files exist
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found. Please ensure all files are uploaded."
    exit 1
fi

echo "✅ Found application files"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker from Package Center."
    exit 1
fi

echo "✅ Docker is installed"

# Check docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not available. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker Compose is available"
echo ""

# Make scripts executable
echo "🔐 Setting permissions..."
chmod +x *.sh 2>/dev/null || true
chmod 755 *.py 2>/dev/null || true

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p instance uploads logs static
chmod 755 instance uploads logs static

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "📝 Creating Dockerfile..."
    cat > Dockerfile << 'EOF'
FROM python:3.9-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads logs instance static
RUN chmod 755 uploads logs instance static
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Run the application
CMD ["python", "app.py"]
EOF
fi

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
      - SECRET_KEY=production-secret-key
    restart: unless-stopped
    networks:
      - pdf-extractor-network

networks:
  pdf-extractor-network:
    driver: bridge
EOF
fi

echo ""
echo "🔨 Building Docker image..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Failed to build Docker image"
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
sleep 15

# Check if container is running
if docker ps | grep -q pdf-extractor; then
    echo ""
    echo "🎉 SUCCESS! PDF Extractor is now running!"
    echo ""
    echo "📋 Application Information:"
    echo "   🌐 URL: http://192.168.0.201:5000"
    echo "   📁 Directory: $APP_DIR"
    echo "   🗄️  Database: $APP_DIR/instance/"
    echo "   📁 Uploads: $APP_DIR/uploads/"
    echo "   📝 Logs: $APP_DIR/logs/"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Restart: docker-compose restart"
    echo "   Stop: docker-compose down"
    echo "   Start: docker-compose up -d"
    echo ""
    echo "🛠️  Available Scripts:"
    echo "   ./master-control-synology.sh - Complete management suite"
    echo "   ./backup-synology.sh - Backup data"
    echo "   ./troubleshoot-synology.sh - Troubleshooting"
    echo "   ./monitor-synology.sh - Monitor application"
    echo ""
    echo "⚠️  Next Steps:"
    echo "   1. Open http://192.168.0.201:5000 in your browser"
    echo "   2. Test the application"
    echo "   3. Configure firewall if needed"
    echo "   4. Set up regular backups"
    echo ""
else
    echo "❌ Application failed to start"
    echo "Check logs: docker-compose logs"
    exit 1
fi

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
