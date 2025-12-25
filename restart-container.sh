#!/bin/bash
# Commands to restart the PDF extractor container
# Run these on the server: ssh atoz@AtozServer

cd /volume1/docker/pdf-extractor

echo "=== Restarting PDF Extractor Container ==="
echo ""

echo "Step 1: Stopping container..."
docker-compose -f docker-compose-synology.yml down

echo ""
echo "Step 2: Starting container..."
docker-compose -f docker-compose-synology.yml up -d

echo ""
echo "Step 3: Waiting for container to start..."
sleep 5

echo ""
echo "Step 4: Checking container status..."
docker ps | grep pdf-extractor

echo ""
echo "Step 5: Showing recent logs..."
docker logs pdf-extractor --tail 30

echo ""
echo "=== Container restarted! ==="
echo "App should be accessible at: http://192.168.0.201:5005"
echo ""

