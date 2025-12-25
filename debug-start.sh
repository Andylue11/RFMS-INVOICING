# Check what happened and try to start the container

# Check if the build completed successfully
echo "Checking for Docker images..."
sudo docker images | grep pdf-extractor

echo ""
echo "Checking docker-compose status..."
cd /volume1/docker/pdf-extractor
sudo docker-compose ps

echo ""
echo "Trying to start the container..."
sudo docker-compose up -d

echo ""
echo "Waiting 10 seconds..."
sleep 10

echo ""
echo "Checking if container is running now..."
sudo docker ps

echo ""
echo "If still not running, checking logs..."
sudo docker-compose logs --tail=50
