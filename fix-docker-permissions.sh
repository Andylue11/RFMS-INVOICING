#!/bin/bash

# Fix Docker Permissions and Setup PDF Extractor
# Run this script with sudo on your Synology NAS

echo "=========================================="
echo "Fixing Docker Permissions"
echo "=========================================="

# Add atoz user to docker group
echo "Adding atoz user to docker group..."
sudo usermod -aG docker atoz

# Set proper permissions for docker.sock
echo "Setting Docker socket permissions..."
sudo chmod 666 /var/run/docker.sock

# Apply the group changes (requires logout/login or use newgrp)
echo "Activating docker group for current session..."
newgrp docker << 'EOF'
cd /volume1/docker/pdf-extractor

echo ""
echo "🔨 Building and starting PDF Extractor..."
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
sleep 20

# Check if container is running
if docker ps | grep -q pdf-extractor; then
    echo ""
    echo "🎉 SUCCESS! PDF Extractor is now running!"
    echo ""
    echo "📋 Application Information:"
    echo "   🌐 URL: http://192.168.0.201:5000"
    echo "   📁 Directory: /volume1/docker/pdf-extractor"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Restart: docker-compose restart"
    echo "   Stop: docker-compose down"
    echo "   Start: docker-compose up -d"
else
    echo "❌ Application failed to start"
    echo "Check logs: docker-compose logs"
    exit 1
fi
EOF

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: For the docker group changes to fully take effect,"
echo "you should log out and log back in to SSH, or restart your SSH session."
echo ""
echo "After logging back in, you can use docker commands without sudo."
