#!/bin/bash

# Quick start script for RFMS Uploader on NAS
# Usage: ./start-nas.sh

set -e

APP_DIR="/volume1/docker/rfms-uploader"

echo "=========================================="
echo "Starting RFMS Uploader"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f "${APP_DIR}/.env" ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from .env.example..."
    if [ -f "${APP_DIR}/.env.example" ]; then
        cp "${APP_DIR}/.env.example" "${APP_DIR}/.env"
        echo "✅ Created .env file"
        echo "⚠️  Please edit .env file with your actual credentials before starting!"
        echo "   Run: nano ${APP_DIR}/.env"
        exit 1
    else
        echo "❌ .env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Navigate to app directory
cd "${APP_DIR}"

# Ensure directories exist
echo "📁 Ensuring directories exist..."
mkdir -p instance uploads logs static data
chmod 755 instance uploads logs static data

# Build and start
echo "🐳 Building and starting container..."
docker-compose -f docker-compose-nas.yml up -d --build

echo ""
echo "✅ Container started!"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose-nas.yml logs -f uploader"
echo ""
echo "To check status:"
echo "  docker-compose -f docker-compose-nas.yml ps"
echo ""
echo "Application should be available at:"
echo "  http://192.168.0.201:5007"

