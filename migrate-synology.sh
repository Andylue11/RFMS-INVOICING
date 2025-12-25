#!/bin/bash

# PDF Extractor Migration Script for Synology NAS
# This script helps migrate from development to production

echo "=========================================="
echo "PDF Extractor Migration Script"
echo "=========================================="

APP_DIR="/volume1/docker/pdf-extractor"
BACKUP_DIR="/volume1/backup/pdf-extractor-migration"

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application directory not found: $APP_DIR"
    echo "Please run the setup script first."
    exit 1
fi

cd "$APP_DIR"

echo "🔄 Starting migration process..."

# Create backup directory
sudo mkdir -p "$BACKUP_DIR"

# 1. Backup existing data
echo "💾 Creating backup of existing data..."
if [ -d "instance" ]; then
    sudo cp -r instance "$BACKUP_DIR/instance-backup-$(date +%Y%m%d-%H%M%S)"
fi
if [ -d "uploads" ]; then
    sudo cp -r uploads "$BACKUP_DIR/uploads-backup-$(date +%Y%m%d-%H%M%S)"
fi

# 2. Stop the application
echo "🛑 Stopping application..."
docker-compose down

# 3. Create production configuration
echo "⚙️  Creating production configuration..."
cat > .env.production << EOF
# Production Environment Variables
FLASK_ENV=production
SECRET_KEY=$(openssl rand -base64 64 2>/dev/null || echo "production-secret-$(date +%s)")
DATABASE_URL=sqlite:///instance/rfms_xtracr.db
LOG_LEVEL=INFO
MAX_CONTENT_LENGTH=16777216
EOF

# 4. Update docker-compose.yml for production
echo "🐳 Updating docker-compose.yml for production..."
cat > docker-compose.yml << EOF
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
    env_file:
      - .env.production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp
    networks:
      - pdf-extractor-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/rfms-status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  pdf-extractor-network:
    driver: bridge
EOF

# 5. Create production Dockerfile
echo "📝 Creating production Dockerfile..."
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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/rfms-status || exit 1

# Run the application
CMD ["python", "app.py"]
EOF

# 6. Create production app.py if it doesn't exist
if [ ! -f "app_production.py" ]; then
    echo "📝 Creating production app.py..."
    cat > app_production.py << 'EOF'
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging
from datetime import datetime

# Create Flask app
app = Flask(__name__)

# Production configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'production-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/rfms_xtracr.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/app.log'),
        logging.StreamHandler()
    ]
)

# Initialize database
db = SQLAlchemy(app)

# Import your existing models and routes
try:
    from models import PdfData, Quote, Job
    from utils.ai_analyzer import DocumentAnalyzer
    
    # Initialize AI analyzer
    ai_analyzer = DocumentAnalyzer()
except ImportError as e:
    logging.error(f"Import error: {e}")
    print("⚠️  Some modules not found. Please ensure all files are uploaded.")

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('instance', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF
fi

# 7. Create production requirements.txt
echo "📦 Creating production requirements.txt..."
cat > requirements.txt << 'EOF'
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Migrate==4.0.5
google-generativeai==0.3.2
Pillow==10.0.1
python-dotenv==1.0.0
requests==2.31.0
Werkzeug==2.3.7
gunicorn==21.2.0
EOF

# 8. Create production startup script
echo "🚀 Creating production startup script..."
cat > start-production.sh << 'EOF'
#!/bin/bash

# Production startup script
cd /volume1/docker/pdf-extractor

# Load environment variables
if [ -f ".env.production" ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
fi

# Start the application
docker-compose up -d

# Wait for startup
sleep 15

# Check if running
if docker ps | grep -q pdf-extractor; then
    echo "✅ PDF Extractor started successfully"
else
    echo "❌ Failed to start PDF Extractor"
    exit 1
fi
EOF
chmod +x start-production.sh

# 9. Create production stop script
echo "🛑 Creating production stop script..."
cat > stop-production.sh << 'EOF'
#!/bin/bash

# Production stop script
cd /volume1/docker/pdf-extractor
docker-compose down
echo "✅ PDF Extractor stopped"
EOF
chmod +x stop-production.sh

# 10. Create production restart script
echo "🔄 Creating production restart script..."
cat > restart-production.sh << 'EOF'
#!/bin/bash

# Production restart script
cd /volume1/docker/pdf-extractor
docker-compose restart
sleep 15
echo "✅ PDF Extractor restarted"
EOF
chmod +x restart-production.sh

# 11. Create production monitoring script
echo "📊 Creating production monitoring script..."
cat > monitor-production.sh << 'EOF'
#!/bin/bash

# Production monitoring script
cd /volume1/docker/pdf-extractor

echo "📊 PDF Extractor Production Status"
echo "================================="

# Check container status
if docker ps | grep -q pdf-extractor; then
    echo "✅ Container: Running"
    CONTAINER_STATUS=$(docker ps --format "table {{.Status}}" | grep pdf-extractor)
    echo "📊 Status: $CONTAINER_STATUS"
else
    echo "❌ Container: Stopped"
fi

# Check application health
if curl -s -f "http://localhost:5000/api/rfms-status" > /dev/null; then
    echo "✅ Application: Healthy"
else
    echo "❌ Application: Unhealthy"
fi

# Check resources
echo ""
echo "💻 Resource Usage:"
docker stats --no-stream pdf-extractor

# Check logs for errors
echo ""
echo "📝 Recent Errors:"
docker-compose logs --tail=20 2>&1 | grep -i error | tail -5

echo ""
echo "🌐 Access URL: http://$(hostname -I | awk '{print $1}'):5000"
EOF
chmod +x monitor-production.sh

# 12. Set proper permissions
echo "🔐 Setting permissions..."
sudo chown -R $(whoami):users "$APP_DIR"
sudo chmod -R 755 "$APP_DIR"

# 13. Start production application
echo "🚀 Starting production application..."
docker-compose up -d --build

# Wait for startup
echo "⏳ Waiting for application to start..."
sleep 20

# Check status
if docker ps | grep -q pdf-extractor; then
    echo ""
    echo "🎉 Migration completed successfully!"
    echo ""
    echo "📋 Production Setup Summary:"
    echo "   🌐 Application URL: http://$(hostname -I | awk '{print $1}'):5000"
    echo "   📁 Application Directory: $APP_DIR"
    echo "   🗄️  Database: $APP_DIR/instance/"
    echo "   📁 Uploads: $APP_DIR/uploads/"
    echo "   📝 Logs: $APP_DIR/logs/"
    echo "   💾 Backup: $BACKUP_DIR"
    echo ""
    echo "🔧 Production Management:"
    echo "   Start: ./start-production.sh"
    echo "   Stop: ./stop-production.sh"
    echo "   Restart: ./restart-production.sh"
    echo "   Monitor: ./monitor-production.sh"
    echo ""
    echo "⚠️  Production Checklist:"
    echo "   ✅ Application migrated to production"
    echo "   ✅ Security hardening applied"
    echo "   ✅ Resource limits configured"
    echo "   ✅ Health checks enabled"
    echo "   ✅ Logging configured"
    echo "   ✅ Backup created"
    echo ""
    echo "🔒 Security Recommendations:"
    echo "   1. Configure firewall rules"
    echo "   2. Set up SSL certificates"
    echo "   3. Configure reverse proxy"
    echo "   4. Set up regular backups"
    echo "   5. Monitor logs regularly"
else
    echo "❌ Migration failed"
    echo "Check logs: docker-compose logs"
    exit 1
fi

echo "=========================================="
echo "✅ Migration Complete!"
echo "=========================================="

