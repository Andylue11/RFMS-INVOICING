# QNAP NAS Deployment Guide

## Prerequisites
1. Enable SSH on your QNAP NAS
2. Install Container Station from App Center
3. Install Web Server (optional, for reverse proxy)

## Steps:

### 1. SSH into your QNAP NAS
```bash
ssh admin@YOUR_NAS_IP
```

### 2. Create application directory
```bash
mkdir -p /share/Container/pdf-extractor
cd /share/Container/pdf-extractor
```

### 3. Upload your application files
- Use File Station or SCP to upload your app files

### 4. Run Docker deployment
```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### 5. Configure QNAP Firewall
- Go to Control Panel > Security > Firewall
- Add rule for port 5000 (TCP)

### 6. Optional: Configure Virtual Host
- Go to Control Panel > Web Server > Virtual Host
- Add virtual host pointing to localhost:5000

## Access:
- Internal: http://YOUR_NAS_IP:5000
- External: http://yourdomain.com (if virtual host configured)

## Maintenance:
```bash
# View logs
docker-compose logs -f

# Restart service
docker-compose restart

# Update application
git pull && docker-compose up -d --build
```
