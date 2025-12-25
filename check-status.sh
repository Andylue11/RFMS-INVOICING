# Quick status check and test
echo "Container Status:"
sudo docker ps | grep pdf-extractor

echo ""
echo "Recent Logs:"
sudo docker-compose logs --tail=20

echo ""
echo "Application should be available at: http://192.168.0.201:5005"
echo "Health check status:"
sleep 5
sudo docker inspect pdf-extractor | grep -A 5 Health
