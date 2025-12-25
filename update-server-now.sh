#!/bin/bash
# Simple update script - Copy and paste this entire command

ssh atoz@AtozServer 'cd /volume1/docker/rfms-uploader && \
mkdir -p ~/.ssh && \
chmod 700 ~/.ssh && \
ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null && \
chmod 600 ~/.ssh/known_hosts && \
git remote set-url origin git@github.com:Andylue11/RFMS-UPLOADER.git && \
git fetch origin && \
git checkout main && \
git pull origin main && \
docker-compose down && \
docker-compose build --no-cache && \
docker-compose up -d && \
sleep 10 && \
docker-compose ps && \
echo "" && \
echo "=== Recent Logs ===" && \
docker-compose logs --tail=30'

