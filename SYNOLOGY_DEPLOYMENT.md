# Synology NAS Deployment Guide

## Prerequisites
1. Enable SSH on your Synology NAS
2. Install Docker package from Package Center
3. Enable Web Station (optional, for reverse proxy)

## Steps:

### 1. SSH into your Synology NAS
```bash
ssh admin@YOUR_NAS_IP
```

### 2. Create application directory
```bash
sudo mkdir -p /volume1/docker/pdf-extractor
cd /volume1/docker/pdf-extractor
```

### 3. Upload your application files
- Use File Station or SCP to upload your app files
- Or clone from Git if available

### 4. Run Docker deployment
```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### 5. Configure Synology Firewall
- Go to Control Panel > Security > Firewall
- Add rule for port 5000 (TCP)

### 6. Optional: Configure Reverse Proxy
- Go to Control Panel > Application Portal > Reverse Proxy
- Add rule: Source: pdf-extractor.yourdomain.com → Destination: localhost:5000

## Access:
- Internal: http://YOUR_NAS_IP:5000
- External: http://pdf-extractor.yourdomain.com (if reverse proxy configured)

## Maintenance:
```bash
# View logs
docker-compose logs -f

# Restart service
docker-compose restart

# Update application
git pull && docker-compose up -d --build
```
