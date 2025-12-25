#!/bin/bash
# Quick update script - Copy app.py into running container and restart
# Use this for quick testing, but rebuild for production

echo "=========================================="
echo "Quick Update - Copy app.py to Container"
echo "=========================================="

cd /volume1/docker/pdf-extractor

# Check if container is running
if ! docker ps | grep -q pdf-extractor; then
    echo "ERROR: Container is not running!"
    echo "Please start the container first: docker-compose up -d"
    exit 1
fi

echo "Container is running. Copying app.py..."

# Copy app.py into the container
docker cp app.py pdf-extractor:/app/app.py

if [ $? -eq 0 ]; then
    echo "✓ app.py copied successfully"
    
    # Restart the container to apply changes
    echo "Restarting container..."
    docker-compose restart
    
    echo ""
    echo "✓ Container restarted"
    echo "Waiting for application to start..."
    sleep 5
    
    # Check logs
    echo ""
    echo "Recent logs:"
    docker-compose logs --tail=20
    
    echo ""
    echo "✅ Quick update complete!"
    echo "NOTE: This is a temporary fix. For production, rebuild the image."
else
    echo "ERROR: Failed to copy app.py"
    exit 1
fi

