# Deployment Instructions

## Summary of Changes

This deployment includes:
1. ✅ Fixed "Script Block Loading" alert in Get Pics page
2. ✅ Real-time uppercase conversion for all text inputs
3. ✅ Backend uppercase conversion for RFMS compatibility
4. ✅ Enhanced #ST order search functionality

## Files Changed

- `app.py` - Added uppercase conversion to all endpoints
- `utils/text_utils.py` - NEW: Uppercase conversion utility
- `templates/base.html` - Real-time uppercase JavaScript
- `templates/installer_photos.html` - Removed blocking alert

## Manual Deployment Steps

### Option 1: Using PowerShell Script (Recommended)

1. **Test SSH connection first:**
   ```powershell
   ssh atoz@192.168.0.201 "echo 'Connection successful'"
   ```

2. **If connection works, run deployment:**
   ```powershell
   .\deploy-to-server.ps1
   ```

### Option 2: Manual Step-by-Step

1. **Upload files to server:**
   ```powershell
   scp app.py atoz@192.168.0.201:/volume1/docker/rfms-uploader/
   scp utils/text_utils.py atoz@192.168.0.201:/volume1/docker/rfms-uploader/utils/
   scp templates/base.html atoz@192.168.0.201:/volume1/docker/rfms-uploader/templates/
   scp templates/installer_photos.html atoz@192.168.0.201:/volume1/docker/rfms-uploader/templates/
   scp requirements.txt atoz@192.168.0.201:/volume1/docker/rfms-uploader/
   scp docker-compose.yml atoz@192.168.0.201:/volume1/docker/rfms-uploader/
   scp Dockerfile atoz@192.168.0.201:/volume1/docker/rfms-uploader/
   ```

2. **SSH into server and rebuild:**
   ```powershell
   ssh atoz@192.168.0.201
   ```

3. **On the server, run:**
   ```bash
   cd /volume1/docker/rfms-uploader
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

4. **Verify deployment:**
   ```bash
   docker compose ps
   docker compose logs --tail=50
   ```

### Option 3: Using Bash Script (if on Linux/Mac)

```bash
chmod +x deploy-to-server.sh
./deploy-to-server.sh
```

## Verification

After deployment, verify:

1. **Check container is running:**
   ```bash
   ssh atoz@192.168.0.201 "cd /volume1/docker/rfms-uploader && docker compose ps"
   ```

2. **Check logs:**
   ```bash
   ssh atoz@192.168.0.201 "cd /volume1/docker/rfms-uploader && docker compose logs --tail=50"
   ```

3. **Test the application:**
   - Open browser to the application URL
   - Test uppercase conversion in any text field
   - Test "Get Pics" button (should not show blocking alert)
   - Test stock receiving with #ST orders

## Troubleshooting

### SSH Permission Denied
- Make sure SSH key is set up: `ssh-keygen -t rsa` then copy to server
- Or use password authentication if configured

### Container Build Fails
- Check Docker is running: `docker ps`
- Check disk space: `df -h`
- View build logs: `docker compose build --no-cache 2>&1 | tee build.log`

### Container Won't Start
- Check logs: `docker compose logs`
- Check port 5007 is available: `netstat -tuln | grep 5007`
- Check .env file exists and has correct values

## Rollback

If something goes wrong:

```bash
ssh atoz@192.168.0.201
cd /volume1/docker/rfms-uploader
git checkout HEAD~1  # If using git
docker compose down
docker compose build --no-cache
docker compose up -d
```

