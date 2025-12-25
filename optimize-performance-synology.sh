#!/bin/bash

# PDF Extractor Performance Optimization Script for Synology NAS
# This script optimizes the performance of your PDF Extractor installation

echo "=========================================="
echo "PDF Extractor Performance Optimization"
echo "=========================================="

APP_DIR="/volume1/docker/pdf-extractor"

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application directory not found: $APP_DIR"
    echo "Please run the setup script first."
    exit 1
fi

cd "$APP_DIR"

echo "⚡ Starting performance optimization..."

# 1. Optimize Docker configuration
echo "🐳 Optimizing Docker configuration..."
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
      - SECRET_KEY=optimized-secret-key-$(date +%s)
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
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
      - /tmp:size=100M
      - /var/tmp:size=100M
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
    ulimits:
      nofile:
        soft: 65536
        hard: 65536

networks:
  pdf-extractor-network:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.enable_icc: "true"
      com.docker.network.bridge.enable_ip_masquerade: "true"
EOF

# 2. Optimize Dockerfile
echo "📝 Optimizing Dockerfile..."
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

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

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

# Set environment variables for performance
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/rfms-status || exit 1

# Run the application
CMD ["python", "app.py"]
EOF

# 3. Optimize requirements.txt
echo "📦 Optimizing requirements.txt..."
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
psutil==5.9.6
EOF

# 4. Create performance monitoring script
echo "📊 Creating performance monitoring script..."
cat > performance-monitor.sh << 'EOF'
#!/bin/bash

# Performance monitoring script
LOG_FILE="/volume1/docker/pdf-extractor/logs/performance.log"

log_performance() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - PERFORMANCE: $1" >> "$LOG_FILE"
}

# Monitor CPU usage
monitor_cpu() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    log_performance "CPU Usage: ${cpu_usage}%"
    
    if [ "$cpu_usage" -gt 80 ]; then
        log_performance "WARNING: High CPU usage detected"
    fi
}

# Monitor memory usage
monitor_memory() {
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    log_performance "Memory Usage: ${memory_usage}%"
    
    if [ "$memory_usage" -gt 80 ]; then
        log_performance "WARNING: High memory usage detected"
    fi
}

# Monitor disk usage
monitor_disk() {
    local disk_usage=$(df -h /volume1 | tail -1 | awk '{print $5}' | sed 's/%//')
    log_performance "Disk Usage: ${disk_usage}%"
    
    if [ "$disk_usage" -gt 80 ]; then
        log_performance "WARNING: High disk usage detected"
    fi
}

# Monitor network usage
monitor_network() {
    local connections=$(netstat -an | grep :5000 | wc -l)
    log_performance "Active Connections: $connections"
    
    if [ "$connections" -gt 100 ]; then
        log_performance "WARNING: High number of connections"
    fi
}

# Monitor application performance
monitor_application() {
    local response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:5000/api/rfms-status)
    log_performance "Response Time: ${response_time}s"
    
    if [ "$response_time" -gt 5 ]; then
        log_performance "WARNING: Slow response time detected"
    fi
}

# Run all monitoring functions
monitor_cpu
monitor_memory
monitor_disk
monitor_network
monitor_application
EOF
chmod +x performance-monitor.sh

# 5. Create performance optimization script
echo "⚡ Creating performance optimization script..."
cat > optimize-performance.sh << 'EOF'
#!/bin/bash

# Performance optimization script
echo "⚡ Optimizing PDF Extractor performance..."

# Optimize database
optimize_database() {
    echo "🗄️  Optimizing database..."
    if [ -f "instance/rfms_xtracr.db" ]; then
        sqlite3 instance/rfms_xtracr.db "VACUUM; ANALYZE; PRAGMA optimize;" 2>/dev/null || true
        echo "✅ Database optimized"
    fi
}

# Optimize file system
optimize_filesystem() {
    echo "📁 Optimizing file system..."
    
    # Clean up old files
    find uploads -type f -mtime +30 -delete 2>/dev/null || true
    find logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    # Optimize file permissions
    find . -type f -exec chmod 644 {} \;
    find . -type d -exec chmod 755 {} \;
    
    echo "✅ File system optimized"
}

# Optimize Docker
optimize_docker() {
    echo "🐳 Optimizing Docker..."
    
    # Clean up unused images
    docker image prune -f
    
    # Clean up unused containers
    docker container prune -f
    
    # Clean up unused volumes
    docker volume prune -f
    
    # Clean up unused networks
    docker network prune -f
    
    echo "✅ Docker optimized"
}

# Optimize system
optimize_system() {
    echo "🖥️  Optimizing system..."
    
    # Clear system cache
    sync
    echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
    
    # Optimize swap
    if [ -f /proc/sys/vm/swappiness ]; then
        echo 10 > /proc/sys/vm/swappiness 2>/dev/null || true
    fi
    
    echo "✅ System optimized"
}

# Run all optimization functions
optimize_database
optimize_filesystem
optimize_docker
optimize_system

echo "✅ Performance optimization complete"
EOF
chmod +x optimize-performance.sh

# 6. Create performance tuning script
echo "🎛️  Creating performance tuning script..."
cat > tune-performance.sh << 'EOF'
#!/bin/bash

# Performance tuning script
echo "🎛️  Tuning PDF Extractor performance..."

# Tune Docker settings
tune_docker() {
    echo "🐳 Tuning Docker settings..."
    
    # Increase Docker daemon memory limit
    if [ -f /etc/docker/daemon.json ]; then
        sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.backup
    fi
    
    sudo tee /etc/docker/daemon.json > /dev/null << 'EOF'
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "storage-opts": [
        "overlay2.override_kernel_check=true"
    ],
    "default-ulimits": {
        "nofile": {
            "Name": "nofile",
            "Hard": 65536,
            "Soft": 65536
        }
    }
}
EOF
    
    echo "✅ Docker settings tuned"
}

# Tune system settings
tune_system() {
    echo "🖥️  Tuning system settings..."
    
    # Tune network settings
    echo 'net.core.rmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
    echo 'net.core.wmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
    echo 'net.ipv4.tcp_rmem = 4096 65536 16777216' | sudo tee -a /etc/sysctl.conf
    echo 'net.ipv4.tcp_wmem = 4096 65536 16777216' | sudo tee -a /etc/sysctl.conf
    
    # Tune file system settings
    echo 'fs.file-max = 65536' | sudo tee -a /etc/sysctl.conf
    
    # Apply settings
    sudo sysctl -p
    
    echo "✅ System settings tuned"
}

# Tune application settings
tune_application() {
    echo "⚙️  Tuning application settings..."
    
    # Create optimized app configuration
    cat > app_optimized.py << 'EOF'
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import logging

# Create Flask app
app = Flask(__name__)

# Optimized configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'optimized-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/rfms_xtracr.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Optimized logging
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

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('instance', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run the application with optimizations
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
EOF
    
    echo "✅ Application settings tuned"
}

# Run all tuning functions
tune_docker
tune_system
tune_application

echo "✅ Performance tuning complete"
EOF
chmod +x tune-performance.sh

# 7. Create performance benchmark script
echo "📊 Creating performance benchmark script..."
cat > benchmark-performance.sh << 'EOF'
#!/bin/bash

# Performance benchmark script
echo "📊 Benchmarking PDF Extractor performance..."

# Benchmark CPU performance
benchmark_cpu() {
    echo "⚡ CPU Benchmark:"
    time python3 -c "
import time
start = time.time()
for i in range(1000000):
    pass
end = time.time()
print(f'CPU benchmark completed in {end - start:.2f} seconds')
"
}

# Benchmark memory performance
benchmark_memory() {
    echo "🧠 Memory Benchmark:"
    python3 -c "
import psutil
import time

# Get initial memory usage
initial_memory = psutil.virtual_memory().used

# Allocate memory
data = []
for i in range(100000):
    data.append(i)

# Get final memory usage
final_memory = psutil.virtual_memory().used
memory_used = final_memory - initial_memory

print(f'Memory benchmark: {memory_used / 1024 / 1024:.2f} MB allocated')
"
}

# Benchmark disk performance
benchmark_disk() {
    echo "💾 Disk Benchmark:"
    time dd if=/dev/zero of=/tmp/benchmark_test bs=1M count=100 2>/dev/null
    time dd if=/tmp/benchmark_test of=/dev/null bs=1M 2>/dev/null
    rm -f /tmp/benchmark_test
}

# Benchmark network performance
benchmark_network() {
    echo "🌐 Network Benchmark:"
    time curl -o /dev/null -s http://localhost:5000/api/rfms-status
}

# Benchmark application performance
benchmark_application() {
    echo "📱 Application Benchmark:"
    python3 -c "
import requests
import time

# Test multiple requests
start = time.time()
for i in range(10):
    response = requests.get('http://localhost:5000/api/rfms-status')
    if response.status_code != 200:
        print(f'Request {i+1} failed')
        break
end = time.time()

print(f'Application benchmark: 10 requests completed in {end - start:.2f} seconds')
print(f'Average response time: {(end - start) / 10:.2f} seconds per request')
"
}

# Run all benchmarks
benchmark_cpu
benchmark_memory
benchmark_disk
benchmark_network
benchmark_application

echo "✅ Performance benchmark complete"
EOF
chmod +x benchmark-performance.sh

# 8. Set proper permissions
echo "🔐 Setting permissions..."
sudo chown -R $(whoami):users "$APP_DIR"
sudo chmod -R 755 "$APP_DIR"

# 9. Apply optimizations
echo "🔄 Applying performance optimizations..."
docker-compose down
docker-compose up -d --build

# Wait for startup
echo "⏳ Waiting for application to start..."
sleep 20

# Check status
if docker ps | grep -q pdf-extractor; then
    echo ""
    echo "🎉 Performance optimization completed successfully!"
    echo ""
    echo "⚡ Performance Optimizations Applied:"
    echo "   ✅ Docker configuration optimized"
    echo "   ✅ Dockerfile optimized"
    echo "   ✅ Requirements optimized"
    echo "   ✅ Performance monitoring enabled"
    echo "   ✅ Performance optimization script created"
    echo "   ✅ Performance tuning script created"
    echo "   ✅ Performance benchmark script created"
    echo ""
    echo "🔧 Performance Management:"
    echo "   Monitor: ./performance-monitor.sh"
    echo "   Optimize: ./optimize-performance.sh"
    echo "   Tune: ./tune-performance.sh"
    echo "   Benchmark: ./benchmark-performance.sh"
    echo ""
    echo "📊 Performance Monitoring:"
    echo "   CPU Usage: Monitored"
    echo "   Memory Usage: Monitored"
    echo "   Disk Usage: Monitored"
    echo "   Network Usage: Monitored"
    echo "   Application Performance: Monitored"
    echo ""
    echo "⚠️  Performance Recommendations:"
    echo "   1. Run performance monitoring regularly"
    echo "   2. Optimize performance weekly"
    echo "   3. Tune performance monthly"
    echo "   4. Benchmark performance quarterly"
    echo "   5. Monitor logs for performance issues"
else
    echo "❌ Performance optimization failed"
    echo "Check logs: docker-compose logs"
    exit 1
fi

echo "=========================================="
echo "✅ Performance Optimization Complete!"
echo "=========================================="

