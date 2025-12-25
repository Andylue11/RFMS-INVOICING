# Complete check and restart script
echo "Checking current app.py configuration..."
grep -A 2 "host = " app.py

echo ""
echo "Making sure app.py has 0.0.0.0..."
sed -i "s/host = '127.0.0.1'/host = os.getenv('HOST', '0.0.0.0')/" app.py

echo "Updated line:"
grep -A 2 "host = " app.py

echo ""
echo "Stopping container..."
sudo docker-compose down

echo ""
echo "Rebuilding with updated app.py..."
sudo docker-compose build

echo ""
echo "Starting container..."
sudo docker-compose up -d

echo ""
echo "Waiting 20 seconds..."
sleep 20

echo ""
echo "Checking container status:"
sudo docker ps | grep pdf-extractor

echo ""
echo "Checking logs:"
sudo docker-compose logs --tail=20

echo ""
echo "Testing connection from inside container:"
sudo docker exec pdf-extractor curl -s http://localhost:5000 || echo "Can't curl from inside"

echo ""
echo "Your application should be accessible at: http://192.168.0.201:5005"
