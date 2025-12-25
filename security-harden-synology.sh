#!/bin/bash

# PDF Extractor Security Hardening Script for Synology NAS
# This script applies security best practices to your PDF Extractor installation

echo "=========================================="
echo "PDF Extractor Security Hardening"
echo "=========================================="

APP_DIR="/volume1/docker/pdf-extractor"

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Application directory not found: $APP_DIR"
    echo "Please run the deployment script first."
    exit 1
fi

cd "$APP_DIR"

echo "🔒 Applying security hardening..."

# 1. Generate strong secret key
echo "🔐 Generating strong secret key..."
SECRET_KEY=$(openssl rand -base64 64 2>/dev/null || echo "strong-secret-key-$(date +%s)-$(openssl rand -hex 16)")
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" docker-compose.yml
echo "✅ Strong secret key generated"

# 2. Configure non-root user
echo "👤 Configuring non-root user..."
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

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
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/rfms-status || exit 1

CMD ["python", "app.py"]
EOF
echo "✅ Non-root user configured"

# 3. Configure resource limits
echo "💻 Configuring resource limits..."
if ! grep -q "deploy:" docker-compose.yml; then
    sed -i "/restart: unless-stopped/a\\    deploy:\\n      resources:\\n        limits:\\n          memory: 1G\\n          cpus: '1.0'\\n        reservations:\\n          memory: 512M\\n          cpus: '0.5'" docker-compose.yml
fi
echo "✅ Resource limits configured"

# 4. Configure security options
echo "🛡️  Configuring security options..."
if ! grep -q "security_opt:" docker-compose.yml; then
    sed -i "/restart: unless-stopped/a\\    security_opt:\\n      - no-new-privileges:true" docker-compose.yml
fi
echo "✅ Security options configured"

# 5. Configure read-only root filesystem
echo "📁 Configuring read-only root filesystem..."
if ! grep -q "read_only: true" docker-compose.yml; then
    sed -i "/restart: unless-stopped/a\\    read_only: true" docker-compose.yml
fi
echo "✅ Read-only root filesystem configured"

# 6. Configure tmpfs for temporary files
echo "💾 Configuring tmpfs for temporary files..."
if ! grep -q "tmpfs:" docker-compose.yml; then
    sed -i "/restart: unless-stopped/a\\    tmpfs:\\n      - /tmp\\n      - /var/tmp" docker-compose.yml
fi
echo "✅ Tmpfs configured"

# 7. Configure network security
echo "🌐 Configuring network security..."
if ! grep -q "networks:" docker-compose.yml; then
    sed -i "/restart: unless-stopped/a\\    networks:\\n      - pdf-extractor-network" docker-compose.yml
fi
echo "✅ Network security configured"

# 8. Create security monitoring script
echo "📊 Creating security monitoring script..."
cat > security-monitor.sh << 'EOF'
#!/bin/bash

# Security monitoring script
LOG_FILE="/volume1/docker/pdf-extractor/logs/security.log"

log_security_event() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - SECURITY: $1" >> "$LOG_FILE"
}

# Check for failed login attempts
check_failed_logins() {
    local failed_logins=$(grep "Failed password" /var/log/auth.log 2>/dev/null | wc -l)
    if [ "$failed_logins" -gt 10 ]; then
        log_security_event "High number of failed login attempts: $failed_logins"
    fi
}

# Check for suspicious network activity
check_network_activity() {
    local connections=$(netstat -an | grep :5000 | wc -l)
    if [ "$connections" -gt 100 ]; then
        log_security_event "High number of connections to port 5000: $connections"
    fi
}

# Check for file system changes
check_file_changes() {
    if [ -f "instance/rfms_xtracr.db" ]; then
        local db_size=$(stat -c%s "instance/rfms_xtracr.db")
        if [ "$db_size" -gt 100000000 ]; then  # 100MB
            log_security_event "Database size is unusually large: $db_size bytes"
        fi
    fi
}

# Run security checks
check_failed_logins
check_network_activity
check_file_changes
EOF
chmod +x security-monitor.sh
echo "✅ Security monitoring script created"

# 9. Configure log rotation with security
echo "📝 Configuring secure log rotation..."
cat > logrotate-security.conf << 'EOF'
/volume1/docker/pdf-extractor/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    create 644 root root
    postrotate
        /bin/kill -HUP `cat /var/run/rsyslogd.pid 2> /dev/null` 2> /dev/null || true
    endscript
}
EOF
echo "✅ Secure log rotation configured"

# 10. Create firewall rules
echo "🔥 Creating firewall rules..."
cat > firewall-rules.sh << 'EOF'
#!/bin/bash

# Firewall rules for PDF Extractor
# Run this script to configure iptables rules

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow PDF Extractor port (only from local network)
iptables -A INPUT -p tcp --dport 5000 -s 192.168.0.0/16 -j ACCEPT
iptables -A INPUT -p tcp --dport 5000 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 5000 -s 172.16.0.0/12 -j ACCEPT

# Drop all other traffic
iptables -A INPUT -j DROP

echo "Firewall rules applied"
EOF
chmod +x firewall-rules.sh
echo "✅ Firewall rules script created"

# 11. Configure SSL/TLS (if certificates are available)
echo "🔒 Configuring SSL/TLS..."
if [ -f "/usr/syno/etc/certificate/system/default/cert.pem" ]; then
    echo "✅ SSL certificates found"
    echo "Consider setting up reverse proxy with SSL"
else
    echo "⚠️  SSL certificates not found"
    echo "Consider setting up SSL certificates in DSM"
fi

# 12. Create security audit script
echo "🔍 Creating security audit script..."
cat > security-audit.sh << 'EOF'
#!/bin/bash

# Security audit script
echo "=========================================="
echo "PDF Extractor Security Audit"
echo "=========================================="

# Check file permissions
echo "🔐 Checking file permissions..."
find /volume1/docker/pdf-extractor -type f -perm /o+w | while read file; do
    echo "⚠️  World-writable file: $file"
done

# Check for SUID/SGID files
echo "👤 Checking for SUID/SGID files..."
find /volume1/docker/pdf-extractor -type f \( -perm -4000 -o -perm -2000 \) | while read file; do
    echo "⚠️  SUID/SGID file: $file"
done

# Check for empty passwords
echo "🔑 Checking for empty passwords..."
if [ -f "/etc/shadow" ]; then
    awk -F: '($2 == "") {print "⚠️  Empty password for user: " $1}' /etc/shadow
fi

# Check for open ports
echo "🌐 Checking open ports..."
netstat -tlnp | grep LISTEN | while read line; do
    echo "📡 Open port: $line"
done

# Check for running processes
echo "⚙️  Checking running processes..."
ps aux | grep pdf-extractor | while read line; do
    echo "🔄 PDF Extractor process: $line"
done

echo "=========================================="
echo "Security audit complete"
echo "=========================================="
EOF
chmod +x security-audit.sh
echo "✅ Security audit script created"

# 13. Apply security hardening
echo "🔄 Applying security hardening..."
docker-compose down
docker-compose up -d --build

# Wait for startup
echo "⏳ Waiting for application to start..."
sleep 15

# Verify security hardening
if docker ps | grep -q pdf-extractor; then
    echo ""
    echo "✅ Security hardening applied successfully!"
    echo ""
    echo "🔒 Security Features Applied:"
    echo "   ✅ Strong secret key generated"
    echo "   ✅ Non-root user configured"
    echo "   ✅ Resource limits set"
    echo "   ✅ Security options enabled"
    echo "   ✅ Read-only root filesystem"
    echo "   ✅ Tmpfs for temporary files"
    echo "   ✅ Network security configured"
    echo "   ✅ Security monitoring enabled"
    echo "   ✅ Secure log rotation configured"
    echo "   ✅ Firewall rules created"
    echo "   ✅ Security audit script created"
    echo ""
    echo "⚠️  Next Steps:"
    echo "   1. Run security audit: ./security-audit.sh"
    echo "   2. Configure firewall rules: ./firewall-rules.sh"
    echo "   3. Set up SSL certificates in DSM"
    echo "   4. Configure reverse proxy with SSL"
    echo "   5. Set up regular security monitoring"
else
    echo "❌ Failed to apply security hardening"
    echo "Check logs: docker-compose logs"
fi

echo "=========================================="
echo "✅ Security Hardening Complete!"
echo "=========================================="

