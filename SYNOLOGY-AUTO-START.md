# Synology NAS Auto-Start Setup

This guide explains how to set up automatic container startup after power loss/reboot on your Synology NAS.

## Method 1: Startup Script (Recommended)

### Installation Steps

1. **Copy the startup script to your NAS:**
   ```bash
   # From your local machine
   scp synology-startup.sh atoz@192.168.0.201:/volume1/docker/rfms-uploader/
   scp install-startup-script.sh atoz@192.168.0.201:/volume1/docker/rfms-uploader/
   ```

2. **SSH into your NAS:**
   ```bash
   ssh atoz@192.168.0.201
   ```

3. **Run the installation script:**
   ```bash
   cd /volume1/docker/rfms-uploader
   sudo bash install-startup-script.sh
   ```

4. **Verify installation:**
   ```bash
   ls -la /usr/local/etc/rc.d/S99rfms-uploader.sh
   ```

### What the Script Does

- Waits for Docker to be ready after boot
- Waits for network connectivity
- Automatically starts the `uploader` container
- Logs all activities to `/volume1/docker/rfms-uploader/logs/startup.log`

### Testing

Test the script manually:
```bash
sudo /usr/local/etc/rc.d/S99rfms-uploader.sh
```

Check the logs:
```bash
tail -f /volume1/docker/rfms-uploader/logs/startup.log
```

## Method 2: Synology Task Scheduler (Alternative)

If Method 1 doesn't work, use Synology's Task Scheduler:

1. **Open Synology DSM** → **Control Panel** → **Task Scheduler**

2. **Create a new task:**
   - **General Tab:**
     - Task: `RFMS Uploader Auto-Start`
     - User: `root`
     - Enabled: ✓
   
   - **Schedule Tab:**
     - Run on the following days: Select "Boot-up"
     - Time: Leave default
   
   - **Task Settings Tab:**
     - Run command: `bash /volume1/docker/rfms-uploader/synology-startup.sh`

3. **Save the task**

## Method 3: Docker Auto-Start (Already Configured)

The `docker-compose-nas.yml` already has `restart: unless-stopped` which means:
- Containers will automatically restart if they crash
- Containers will start automatically when Docker starts
- However, Docker itself needs to be running (handled by Synology Package Center)

## Ensuring Docker Auto-Starts

1. **Open Synology DSM** → **Package Center**
2. **Find Docker** → **Open**
3. **Settings** → Ensure "Auto-start" is enabled

## Power Loss Recovery

After a power loss:
1. NAS boots up (if connected to UPS or power restored)
2. Synology starts Docker service automatically
3. Startup script runs and starts containers
4. Application becomes accessible

## Troubleshooting

### Containers Not Starting After Reboot

1. Check startup log:
   ```bash
   cat /volume1/docker/rfms-uploader/logs/startup.log
   ```

2. Check Docker status:
   ```bash
   docker ps -a
   ```

3. Manually start containers:
   ```bash
   cd /volume1/docker/rfms-uploader
   docker-compose -f docker-compose-nas.yml up -d
   ```

### Script Not Running on Boot

1. Verify script exists and is executable:
   ```bash
   ls -la /usr/local/etc/rc.d/S99rfms-uploader.sh
   ```

2. Check script permissions:
   ```bash
   sudo chmod +x /usr/local/etc/rc.d/S99rfms-uploader.sh
   ```

3. Test script manually:
   ```bash
   sudo /usr/local/etc/rc.d/S99rfms-uploader.sh
   ```

## Manual Container Management

### Start containers:
```bash
cd /volume1/docker/rfms-uploader
docker-compose -f docker-compose-nas.yml up -d
```

### Stop containers:
```bash
cd /volume1/docker/rfms-uploader
docker-compose -f docker-compose-nas.yml down
```

### Restart containers:
```bash
cd /volume1/docker/rfms-uploader
docker-compose -f docker-compose-nas.yml restart
```

### View container status:
```bash
docker ps | grep uploader
```

### View container logs:
```bash
docker logs uploader
```

## Notes

- The startup script waits for Docker and network to be ready before starting containers
- All startup activities are logged for troubleshooting
- The script is idempotent - safe to run multiple times
- Containers have `restart: unless-stopped` policy for automatic recovery




