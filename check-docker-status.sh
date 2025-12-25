#!/bin/bash
# Check Docker container status and logs

echo "=========================================="
echo "Checking Docker Container Status"
echo "=========================================="

# Check if container is running
echo ""
echo "Container Status:"
docker ps -a | grep pdf-extractor

# Check if image exists
echo ""
echo "Docker Images:"
docker images | grep pdf-extractor

# Check container logs
echo ""
echo "Recent Logs (last 30 lines):"
docker-compose logs --tail=30

# Check if port is listening
echo ""
echo "Port Status:"
netstat -tuln | grep 5005 || ss -tuln | grep 5005

echo ""
echo "=========================================="

