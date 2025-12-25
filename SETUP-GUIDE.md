# PDF Extractor - Quick Setup Guide for Synology NAS

## 🚀 Quick Setup (If files are already on the server)

Since your files are already at `\\AtozServer\docker\pdf-extractor` (which maps to `/volume1/docker/pdf-extractor` on the NAS), follow these steps:

### Step 1: Connect to Your Synology NAS

You can either:
1. **SSH into the NAS** (recommended):
   ```bash
   ssh atoz@192.168.0.201
   ```

2. **Use File Station** in DSM (Synology's web interface)

### Step 2: Navigate to the Application Directory

```bash
cd /volume1/docker/pdf-extractor
```

### Step 3: Run the Setup Script

```bash
bash setup-now.sh
```

This will:
- ✅ Check for Docker
- ✅ Create necessary directories
- ✅ Set proper permissions
- ✅ Build the Docker image
- ✅ Start the application

### Step 4: Access Your Application

Open your web browser and go to:
```
http://192.168.0.201:5000
```

---

## 📋 Manual Setup (Alternative Method)

If the script doesn't work, you can set up manually:

### 1. Make scripts executable:
```bash
cd /volume1/docker/pdf-extractor
chmod +x *.sh
```

### 2. Create directories:
```bash
mkdir -p instance uploads logs static
chmod 755 instance uploads logs static
```

### 3. Build and start with Docker Compose:
```bash
docker-compose build
docker-compose up -d
```

### 4. Check status:
```bash
docker-compose ps
docker-compose logs -f
```

---

## 🔧 Management Commands

### View Logs:
```bash
docker-compose logs -f
```

### Restart Application:
```bash
docker-compose restart
```

### Stop Application:
```bash
docker-compose down
```

### Start Application:
```bash
docker-compose up -d
```

### Check Status:
```bash
docker ps | grep pdf-extractor
```

---

## 🛠️ Available Management Scripts

Once set up, you can use these scripts:

- **`master-control-synology.sh`** - Complete management interface
- **`backup-synology.sh`** - Backup your data
- **`troubleshoot-synology.sh`** - Troubleshooting tools
- **`monitor-synology.sh`** - Monitor application health
- **`configure-synology.sh`** - Configure settings
- **`update-synology.sh`** - Update the application

---

## ⚠️ Troubleshooting

### Port Already in Use

If port 5000 is already in use, edit `docker-compose.yml`:

```yaml
ports:
  - "5001:5000"  # Change external port to 5001
```

Then access the app at `http://192.168.0.201:5001`

### Permission Denied

If you get permission errors:

```bash
sudo chown -R atoz:users /volume1/docker/pdf-extractor
sudo chmod -R 755 /volume1/docker/pdf-extractor
```

### Docker Not Running

Make sure Docker is running:

```bash
sudo synoservice --status pkgctl-Docker
```

If not running, start it:
```bash
sudo synoservice --start pkgctl-Docker
```

### Check Logs for Errors

```bash
docker-compose logs | grep -i error
docker-compose logs app
```

---

## 🌐 Network Access

### Internal Network (Your Office):
```
http://192.168.0.201:5000
```

### External Access (Outside Office):

To access from outside your office network:

1. **Configure Port Forwarding** on your router:
   - External Port: 5000 (or any available port)
   - Internal IP: 192.168.0.201
   - Internal Port: 5000

2. **Or use Synology's VPN**:
   - Set up VPN in DSM Control Panel
   - Connect to VPN when outside office
   - Access using internal IP

3. **Or use Synology's Reverse Proxy**:
   - Set up reverse proxy in Control Panel > Login Portal
   - Use HTTPS for security

---

## 📊 System Requirements

- **Minimum:**
  - Synology NAS with DSM 6.0 or later
  - Docker installed (from Package Center)
  - At least 1GB free RAM
  - At least 500MB free disk space

- **Recommended:**
  - 2GB RAM
  - 1GB disk space
  - Docker Compose support

---

## 🔒 Security Recommendations

1. **Change Default Password:**
   - Edit `.env` file
   - Change `SECRET_KEY` to a random string

2. **Enable Firewall:**
   - Control Panel > Security > Firewall
   - Add rule for port 5000 (TCP)

3. **Use HTTPS:**
   - Set up reverse proxy with SSL certificate
   - Available in Control Panel > Login Portal

4. **Regular Backups:**
   - Run `./backup-synology.sh` regularly
   - Store backups off-site

---

## 📞 Need Help?

Check the logs first:
```bash
docker-compose logs -f
```

Run the troubleshooting script:
```bash
./troubleshoot-synology.sh
```

Or check the main README for more information.

---

## ✅ Setup Complete Checklist

- [ ] Files uploaded to `/volume1/docker/pdf-extractor`
- [ ] Docker installed and running
- [ ] Setup script executed successfully
- [ ] Application accessible at http://192.168.0.201:5000
- [ ] Firewall configured
- [ ] Backups scheduled
- [ ] Documentation reviewed

---

**Congratulations!** Your PDF Extractor is now running on your Synology NAS! 🎉
