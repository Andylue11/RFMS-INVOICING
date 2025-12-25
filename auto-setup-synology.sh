#!/bin/bash

# PDF Extractor Automated Setup Script for Synology NAS
# This script automates the entire setup process

echo "=========================================="
echo "PDF Extractor Automated Setup"
echo "=========================================="

# Configuration
APP_NAME="pdf-extractor"
APP_DIR="/volume1/docker/$APP_NAME"
NAS_IP=$(hostname -I | awk '{print $1}')

echo "🌐 NAS IP Address: $NAS_IP"
echo "📁 Application Directory: $APP_DIR"

# Check if running on Synology
if [ ! -d "/volume1" ]; then
    echo "❌ This script is designed for Synology NAS only."
    exit 1
fi

# Check prerequisites
echo ""
echo "🔍 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker from Package Center."
    exit 1
fi

# Check docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not available. Please install Docker Compose."
    exit 1
fi

echo "✅ Prerequisites met"

# Create application directory
echo ""
echo "📁 Creating application directory..."
sudo mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Create subdirectories
sudo mkdir -p instance uploads logs static
sudo chmod 755 instance uploads logs static

# Create production app.py
echo "📝 Creating production configuration..."
cat > app_production.py << 'EOF'
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging

# Create Flask app
app = Flask(__name__)

# Production configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'production-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/rfms_xtracr.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure logging
logging.basicConfig(
    level=logging.INFO,
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

# Create Dockerfile
echo "🐳 Creating Dockerfile..."
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
ENV FLASK_APP=app_production.py
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/rfms-status || exit 1

# Run the application
CMD ["python", "app_production.py"]
EOF

# Create docker-compose.yml
echo "📋 Creating docker-compose.yml..."
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
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=production-secret-key-$(date +%s)
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
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

networks:
  pdf-extractor-network:
    driver: bridge
EOF

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo "📦 Creating requirements.txt..."
    cat > requirements.txt << 'EOF'
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Migrate==4.0.5
google-generativeai==0.3.2
Pillow==10.0.1
python-dotenv==1.0.0
requests==2.31.0
Werkzeug==2.3.7
EOF
fi

# Create basic models.py if it doesn't exist
if [ ! -f "models.py" ]; then
    echo "🗄️  Creating basic models.py..."
    cat > models.py << 'EOF'
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class PdfData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    extracted_data = db.Column(db.Text)
    processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(100), nullable=False)
    customer_name = db.Column(db.String(255))
    amount = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_number = db.Column(db.String(100), nullable=False)
    customer_name = db.Column(db.String(255))
    amount = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
EOF
fi

# Create basic utils directory and files
if [ ! -d "utils" ]; then
    echo "🔧 Creating utils directory..."
    mkdir -p utils
    cat > utils/__init__.py << 'EOF'
# Utils package
EOF
    
    cat > utils/ai_analyzer.py << 'EOF'
import logging

class DocumentAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("AI analyzer initialized")
    
    def analyze_document(self, file_path):
        # Placeholder for AI analysis
        return {
            'po_number': 'DEMO-001',
            'job_description': 'Demo job description',
            'amount': '1000.00',
            'main_contacts': [{'first_name': 'Demo', 'last_name': 'User'}]
        }
EOF
fi

# Create basic templates directory
if [ ! -d "templates" ]; then
    echo "🎨 Creating templates directory..."
    mkdir -p templates
    cat > templates/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>PDF Extractor</title>
</head>
<body>
    <h1>PDF Extractor</h1>
    <p>Application is running successfully!</p>
    <p>Upload your PDF files here.</p>
</body>
</html>
EOF
fi

# Create basic static directory
if [ ! -d "static" ]; then
    echo "📁 Creating static directory..."
    mkdir -p static
fi

# Set proper permissions
echo "🔐 Setting permissions..."
sudo chown -R $(whoami):users "$APP_DIR"
sudo chmod -R 755 "$APP_DIR"

# Build and start the application
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
    echo "📋 Setup Summary:"
    echo "   🌐 Application URL: http://$NAS_IP:5000"
    echo "   📁 Application Directory: $APP_DIR"
    echo "   🗄️  Database: $APP_DIR/instance/"
    echo "   📁 Uploads: $APP_DIR/uploads/"
    echo "   📝 Logs: $APP_DIR/logs/"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: cd $APP_DIR && docker-compose logs -f"
    echo "   Restart: cd $APP_DIR && docker-compose restart"
    echo "   Stop: cd $APP_DIR && docker-compose down"
    echo ""
    echo "⚠️  Next Steps:"
    echo "   1. Upload your complete application files to: $APP_DIR"
    echo "   2. Configure firewall (Control Panel > Security > Firewall)"
    echo "   3. Add rule for port 5000 (TCP)"
    echo "   4. Test the application in your browser"
    echo "   5. Set up regular backups"
    echo ""
    echo "📚 Available Scripts:"
    echo "   ./manage-synology.sh - Complete management suite"
    echo "   ./backup-synology.sh - Backup data"
    echo "   ./update-synology.sh - Update application"
    echo "   ./troubleshoot-synology.sh - Troubleshooting"
    echo "   ./security-harden-synology.sh - Security hardening"
else
    echo "❌ Failed to start PDF Extractor"
    echo "Check logs with: docker-compose logs"
    exit 1
fi

echo "=========================================="
echo "✅ Automated Setup Complete!"
echo "=========================================="

