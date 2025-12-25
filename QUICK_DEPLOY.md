# Quick Deployment Guide

## Run from Your Windows Machine (Not on Server)

The PowerShell script must be run from your **local Windows machine**, not on the server.

### Step 1: Run Deployment Script

From your Windows PowerShell or Git Bash, run:

```powershell
.\deploy-to-server.ps1
```

OR if you have Git Bash:

```bash
./deploy-to-server.sh
```

### Step 2: If Script Fails - Manual Steps

If the script fails due to SSH authentication, do this manually:

#### A. Upload Files (from Windows PowerShell):

```powershell
# Upload all changed files
scp app.py atoz@192.168.0.201:/volume1/docker/rfms-uploader/
scp utils/text_utils.py atoz@192.168.0.201:/volume1/docker/rfms-uploader/utils/
scp templates/base.html atoz@192.168.0.201:/volume1/docker/rfms-uploader/templates/
scp templates/installer_photos.html atoz@192.168.0.201:/volume1/docker/rfms-uploader/templates/
scp requirements.txt atoz@192.168.0.201:/volume1/docker/rfms-uploader/
scp docker-compose.yml atoz@192.168.0.201:/volume1/docker/rfms-uploader/
scp Dockerfile atoz@192.168.0.201:/volume1/docker/rfms-uploader/
```

#### B. SSH to Server and Rebuild:

```powershell
ssh atoz@192.168.0.201
```

Then on the server, run:

```bash
cd /volume1/docker/rfms-uploader
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs --tail=50
```

### Step 3: Verify

```bash
docker compose ps
curl http://localhost:5007
```

## Important Notes

- ✅ Run PowerShell scripts from **Windows**, not Linux server
- ✅ Run bash scripts from **Windows Git Bash** or **WSL**
- ✅ The server is Linux - use bash commands there, not PowerShell

