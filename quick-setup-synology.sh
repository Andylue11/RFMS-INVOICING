#!/bin/bash

# Quick Setup Script for PDF Extractor on Synology NAS
# This script will guide you through the entire setup process

echo "=========================================="
echo "PDF Extractor Synology NAS Quick Setup"
echo "=========================================="

# Check if running on Synology
if [ ! -d "/volume1" ]; then
    echo "❌ This script is designed for Synology NAS only."
    echo "Please run this on your Synology NAS via SSH."
    exit 1
fi

echo "✅ Running on Synology NAS"

# Get NAS IP
NAS_IP=$(hostname -I | awk '{print $1}')
echo "🌐 NAS IP Address: $NAS_IP"

# Check prerequisites
echo ""
echo "🔍 Checking prerequisites..."

# Check Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed"
else
    echo "❌ Docker is not installed"
    echo "Please install Docker from Package Center first."
    exit 1
fi

# Check docker-compose
if command -v docker-compose &> /dev/null; then
    echo "✅ docker-compose is available"
else
    echo "❌ docker-compose is not available"
    echo "Please install Docker Compose."
    exit 1
fi

# Create application directory
APP_DIR="/volume1/docker/pdf-extractor"
echo ""
echo "📁 Setting up application directory: $APP_DIR"
sudo mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Create subdirectories
sudo mkdir -p instance uploads logs static
sudo chmod 755 instance uploads logs static

echo "✅ Directory structure created"

# Check if application files exist
if [ -f "app.py" ]; then
    echo "✅ Application files found"
else
    echo ""
    echo "📋 Application files not found in current directory."
    echo "Please upload your PDF Extractor files to: $APP_DIR"
    echo ""
    echo "You can do this by:"
    echo "1. Using File Station in DSM"
    echo "2. Using SCP from your computer:"
    echo "   scp -r /path/to/PDF-Extracr-FINAL-v2-production-draft/* admin@$NAS_IP:$APP_DIR/"
    echo ""
    read -p "Press Enter when files are uploaded..."
fi

# Copy deployment files
echo ""
echo "📋 Setting up deployment files..."

# Create docker-compose.yml
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
      - SECRET_KEY=your-super-secret-key-change-this-in-production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/rfms-status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads logs instance static
RUN chmod 755 uploads logs instance static

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/rfms-status || exit 1

CMD ["python", "app.py"]
EOF

# Set permissions
sudo chown -R $(whoami):users "$APP_DIR"
sudo chmod -R 755 "$APP_DIR"

echo "✅ Deployment files created"

# Build and start
echo ""
echo "🔨 Building and starting PDF Extractor..."
docker-compose up -d --build

# Wait for startup
echo "⏳ Waiting for application to start..."
sleep 20

# Check status
if docker ps | grep -q pdf-extractor; then
    echo ""
    echo "🎉 SUCCESS! PDF Extractor is now running!"
    echo ""
    echo "🌐 Access your application at:"
    echo "   http://$NAS_IP:5000"
    echo ""
    echo "📁 Data is stored in:"
    echo "   Database: $APP_DIR/instance/"
    echo "   Uploads: $APP_DIR/uploads/"
    echo "   Logs: $APP_DIR/logs/"
    echo ""
    echo "🔧 Management commands:"
    echo "   View logs: cd $APP_DIR && docker-compose logs -f"
    echo "   Restart: cd $APP_DIR && docker-compose restart"
    echo "   Stop: cd $APP_DIR && docker-compose down"
    echo ""
    echo "⚠️  Next steps:"
    echo "   1. Configure firewall (Control Panel > Security > Firewall)"
    echo "   2. Add rule for port 5000 (TCP)"
    echo "   3. Test the application in your browser"
    echo "   4. Set up regular backups"
else
    echo "❌ Failed to start PDF Extractor"
    echo "Check logs with: docker-compose logs"
    exit 1
fi

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
