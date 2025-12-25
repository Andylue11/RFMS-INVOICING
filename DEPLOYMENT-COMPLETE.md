# Deployment Complete! ✅

## Status
The RFMS Uploader application has been successfully deployed to the NAS.

## Deployment Details
- **NAS IP**: 192.168.0.201
- **Deployment Path**: `/volume1/docker/rfms-uploader`
- **Container Name**: `uploader`
- **Port**: 5007
- **Status**: Running

## Access the Application
The application is now available at:
- **http://192.168.0.201:5007**

Since you mentioned the reverse proxy is already set up, it should also be accessible via your configured domain.

## Container Information
- **Image**: `rfms-uploader-uploader`
- **Network**: `rfms-uploader_uploader-network`
- **Restart Policy**: `unless-stopped`
- **Health Check**: Enabled (checking every 30s)

## Volume Mounts
The following directories are mounted from the NAS:
- `/volume1/docker/rfms-uploader/instance` → `/app/instance` (database)
- `/volume1/docker/rfms-uploader/uploads` → `/app/uploads` (uploaded files)
- `/volume1/docker/rfms-uploader/logs` → `/app/logs` (application logs)
- `/volume1/docker/rfms-uploader/static` → `/app/static` (static files)
- `/volume1/docker/rfms-uploader/data` → `/app/data` (data files)

## Management Commands

### View Logs
```bash
ssh atoz@192.168.0.201 'cd /volume1/docker/rfms-uploader && /usr/local/bin/docker-compose -f docker-compose-nas.yml logs -f'
```

Or directly:
```bash
ssh atoz@192.168.0.201 '/usr/local/bin/docker logs uploader -f'
```

### Check Container Status
```bash
ssh atoz@192.168.0.201 '/usr/local/bin/docker ps | grep uploader'
```

### Restart Container
```bash
ssh atoz@192.168.0.201 'cd /volume1/docker/rfms-uploader && /usr/local/bin/docker-compose -f docker-compose-nas.yml restart'
```

### Stop Container
```bash
ssh atoz@192.168.0.201 'cd /volume1/docker/rfms-uploader && /usr/local/bin/docker-compose -f docker-compose-nas.yml down'
```

### Start Container
```bash
ssh atoz@192.168.0.201 'cd /volume1/docker/rfms-uploader && /usr/local/bin/docker-compose -f docker-compose-nas.yml up -d'
```

### Rebuild and Restart (after code updates)
```bash
ssh atoz@192.168.0.201 'cd /volume1/docker/rfms-uploader && /usr/local/bin/docker-compose -f docker-compose-nas.yml up -d --build'
```

## Files Created
- `docker-compose-nas.yml` - Docker Compose configuration for NAS deployment
- `env.template` - Environment variables template (copy to `.env` and configure)

## Next Steps
1. ✅ Container is running
2. ✅ Reverse proxy is configured (as you mentioned)
3. Test the application at http://192.168.0.201:5007
4. Monitor logs to ensure everything is working correctly

## Troubleshooting

### Container Not Responding
- Check logs: `docker logs uploader`
- Verify port 5007 is accessible
- Check if container is running: `docker ps | grep uploader`

### Database Issues
- Ensure `instance/` directory has proper permissions
- Check database file: `ls -la /volume1/docker/rfms-uploader/instance/`

### File Upload Issues
- Verify `uploads/` directory permissions: `chmod 755 /volume1/docker/rfms-uploader/uploads`
- Check disk space: `df -h`

## Notes
- Docker is located at: `/usr/local/bin/docker`
- Docker Compose is located at: `/usr/local/bin/docker-compose`
- The container will automatically restart on NAS reboot (restart policy: unless-stopped)




