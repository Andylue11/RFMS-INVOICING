# Synology NAS Deployment Guide for PDF Extractor

## Prerequisites

### 1. Enable SSH on Synology NAS
1. Go to **Control Panel > Terminal & SNMP**
2. Enable **SSH service**
3. Set port (default: 22)
4. Note your NAS IP address

### 2. Install Required Packages
1. Open **Package Center**
2. Install **Docker** package
3. Install **Git Server** (optional, for easier updates)

### 3. Configure Firewall
1. Go to **Control Panel > Security > Firewall**
2. Create new rule for **Port 5000 (TCP)**
3. Allow access from your network

## Step-by-Step Deployment

### Step 1: Connect to Your Synology NAS
```bash
# SSH into your NAS (replace with your NAS IP)
ssh admin@192.168.1.100

# Or use admin user if available
ssh admin@192.168.1.100
```

### Step 2: Prepare the Application
```bash
# Navigate to docker directory
cd /volume1/docker

# Create application directory
sudo mkdir -p pdf-extractor
cd pdf-extractor

# Upload your application files using one of these methods:
```

#### Method A: Using SCP (from your computer)
```bash
# From your local computer, upload files to NAS
scp -r /path/to/PDF-Extracr-FINAL-v2-production-draft/* admin@192.168.1.100:/volume1/docker/pdf-extractor/
```

#### Method B: Using Git (if Git Server is installed)
```bash
# Clone your repository
git clone https://github.com/Andylue11/PDF-Extracr-FINAL-v2-production-draft.git .
```

#### Method C: Using File Station
1. Open **File Station** in DSM
2. Navigate to `/volume1/docker/pdf-extractor/`
3. Upload all your application files

### Step 3: Run Deployment Script
```bash
# Make the script executable
chmod +x deploy-synology.sh

# Run the deployment
./deploy-synology.sh
```

### Step 4: Verify Installation
```bash
# Check if container is running
docker ps

# View application logs
docker-compose logs -f

# Test the application
curl http://localhost:5000/api/rfms-status
```

## Access Your Application

### Internal Network Access
- **URL**: `http://YOUR_NAS_IP:5000`
- **Example**: `http://192.168.1.100:5000`

### External Access (Optional)
1. Go to **Control Panel > External Access > Router Configuration**
2. Add port forwarding rule for port 5000
3. Access via: `http://YOUR_EXTERNAL_IP:5000`

### Reverse Proxy Setup (Recommended for External Access)
1. Go to **Control Panel > Application Portal > Reverse Proxy**
2. Create new rule:
   - **Source**: `pdf-extractor.yourdomain.com`
   - **Destination**: `localhost:5000`
3. Access via: `https://pdf-extractor.yourdomain.com`

## Management Commands

### View Logs
```bash
cd /volume1/docker/pdf-extractor
docker-compose logs -f
```

### Restart Application
```bash
cd /volume1/docker/pdf-extractor
docker-compose restart
```

### Stop Application
```bash
cd /volume1/docker/pdf-extractor
docker-compose down
```

### Update Application
```bash
cd /volume1/docker/pdf-extractor
git pull  # If using Git
docker-compose up -d --build
```

### Backup Data
```bash
# Backup database and uploads
sudo cp -r /volume1/docker/pdf-extractor/instance /volume1/backup/pdf-extractor-$(date +%Y%m%d)
sudo cp -r /volume1/docker/pdf-extractor/uploads /volume1/backup/pdf-extractor-$(date +%Y%m%d)
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check permissions
ls -la /volume1/docker/pdf-extractor/
```

### Can't Access Application
1. Check firewall settings
2. Verify port 5000 is open
3. Check if container is running: `docker ps`
4. Test local access: `curl http://localhost:5000`

### Database Issues
```bash
# Check database file permissions
ls -la /volume1/docker/pdf-extractor/instance/

# Reset database (WARNING: This will delete all data)
sudo rm /volume1/docker/pdf-extractor/instance/rfms_xtracr.db
docker-compose restart
```

## Security Considerations

### 1. Change Default Passwords
- Update `SECRET_KEY` in docker-compose.yml
- Use strong passwords for any admin accounts

### 2. Enable HTTPS
- Set up SSL certificate in DSM
- Configure reverse proxy with HTTPS

### 3. Regular Backups
- Set up automated backups using Hyper Backup
- Include `/volume1/docker/pdf-extractor/instance/` and `/volume1/docker/pdf-extractor/uploads/`

### 4. Network Security
- Use VPN for external access instead of port forwarding
- Restrict firewall rules to specific IP ranges

## Performance Optimization

### 1. Resource Allocation
- Monitor CPU and memory usage in Resource Monitor
- Adjust Docker container limits if needed

### 2. Storage
- Use SSD storage for better performance
- Consider RAID configuration for redundancy

### 3. Network
- Use wired connection for NAS
- Ensure adequate bandwidth for file uploads

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify all prerequisites are met
3. Ensure proper file permissions
4. Check Synology system logs in **Control Panel > Info Center > Log Center**
