#!/bin/bash

# PDF Extractor Upload Script for Synology NAS
# This script uploads all files to the Synology NAS

echo "=========================================="
echo "PDF Extractor NAS Upload"
echo "=========================================="

# Configuration
NAS_USER="atoz"
NAS_IP="192.168.0.201"
NAS_PATH="/volume1/docker/pdf-extractor"
LOCAL_PATH="."

echo "🌐 Uploading to: $NAS_USER@$NAS_IP"
echo "📁 Target path: $NAS_PATH"
echo "📂 Source path: $LOCAL_PATH"

# Check if SCP is available
if ! command -v scp &> /dev/null; then
    echo "❌ SCP is not available. Please install OpenSSH client."
    exit 1
fi

# Test connection to NAS
echo ""
echo "🔍 Testing connection to NAS..."
if ssh -o ConnectTimeout=10 -o BatchMode=yes "$NAS_USER@$NAS_IP" "echo 'Connection successful'" 2>/dev/null; then
    echo "✅ Connection to NAS successful"
else
    echo "❌ Cannot connect to NAS"
    echo "Please ensure:"
    echo "1. SSH is enabled on your Synology NAS"
    echo "2. The IP address is correct: $NAS_IP"
    echo "3. The username is correct: $NAS_USER"
    echo "4. You have SSH key authentication set up or will enter password"
    exit 1
fi

# Create directory on NAS
echo ""
echo "📁 Creating directory on NAS..."
ssh "$NAS_USER@$NAS_IP" "sudo mkdir -p $NAS_PATH && sudo chown -R $NAS_USER:users $NAS_PATH"

# Upload application files
echo ""
echo "📤 Uploading application files..."

# Upload main application files
echo "   📄 Uploading main application files..."
scp app.py "$NAS_USER@$NAS_IP:$NAS_PATH/"
scp models.py "$NAS_USER@$NAS_IP:$NAS_PATH/"
scp requirements.txt "$NAS_USER@$NAS_IP:$NAS_PATH/"

# Upload utils directory
if [ -d "utils" ]; then
    echo "   🔧 Uploading utils directory..."
    scp -r utils "$NAS_USER@$NAS_IP:$NAS_PATH/"
fi

# Upload templates directory
if [ -d "templates" ]; then
    echo "   🎨 Uploading templates directory..."
    scp -r templates "$NAS_USER@$NAS_IP:$NAS_PATH/"
fi

# Upload static directory
if [ -d "static" ]; then
    echo "   📁 Uploading static directory..."
    scp -r static "$NAS_USER@$NAS_IP:$NAS_PATH/"
fi

# Upload all Synology scripts
echo "   🐧 Uploading Synology management scripts..."
for script in *-synology.sh; do
    if [ -f "$script" ]; then
        echo "     📄 Uploading $script..."
        scp "$script" "$NAS_USER@$NAS_IP:$NAS_PATH/"
    fi
done

# Upload Docker files
echo "   🐳 Uploading Docker configuration files..."
for file in Dockerfile* docker-compose*.yml; do
    if [ -f "$file" ]; then
        echo "     📄 Uploading $file..."
        scp "$file" "$NAS_USER@$NAS_IP:$NAS_PATH/"
    fi
done

# Upload any other Python files
echo "   🐍 Uploading Python files..."
for file in *.py; do
    if [ -f "$file" ]; then
        echo "     📄 Uploading $file..."
        scp "$file" "$NAS_USER@$NAS_IP:$NAS_PATH/"
    fi
done

# Upload any configuration files
echo "   ⚙️  Uploading configuration files..."
for file in *.conf *.env*; do
    if [ -f "$file" ]; then
        echo "     📄 Uploading $file..."
        scp "$file" "$NAS_USER@$NAS_IP:$NAS_PATH/"
    fi
done

# Upload documentation
echo "   📚 Uploading documentation..."
for file in *.md README*; do
    if [ -f "$file" ]; then
        echo "     📄 Uploading $file..."
        scp "$file" "$NAS_USER@$NAS_IP:$NAS_PATH/"
    fi
done

# Set proper permissions on NAS
echo ""
echo "🔐 Setting permissions on NAS..."
ssh "$NAS_USER@$NAS_IP" "cd $NAS_PATH && sudo chown -R $NAS_USER:users . && sudo chmod -R 755 . && sudo chmod +x *.sh"

# Create necessary directories on NAS
echo ""
echo "📁 Creating necessary directories on NAS..."
ssh "$NAS_USER@$NAS_IP" "cd $NAS_PATH && sudo mkdir -p instance uploads logs static && sudo chown -R $NAS_USER:users instance uploads logs static && sudo chmod -R 755 instance uploads logs static"

# Verify upload
echo ""
echo "🔍 Verifying upload..."
ssh "$NAS_USER@$NAS_IP" "cd $NAS_PATH && echo '📋 Files uploaded:' && ls -la"

echo ""
echo "✅ Upload completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. SSH into your NAS: ssh $NAS_USER@$NAS_IP"
echo "2. Navigate to: cd $NAS_PATH"
echo "3. Run quick setup: ./quick-setup-synology.sh"
echo "4. Or run master control: ./master-control-synology.sh"
echo ""
echo "🌐 Your application will be available at:"
echo "   http://$NAS_IP:5000"
echo ""
echo "🔧 Management commands:"
echo "   View logs: docker-compose logs -f"
echo "   Restart: docker-compose restart"
echo "   Stop: docker-compose down"
echo "   Start: docker-compose up -d"
echo ""
echo "=========================================="
echo "✅ Upload Complete!"
echo "=========================================="

