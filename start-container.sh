cd /volume1/docker/pdf-extractor
sudo docker-compose up -d
sleep 15
sudo docker ps
sudo docker-compose logs --tail=30
