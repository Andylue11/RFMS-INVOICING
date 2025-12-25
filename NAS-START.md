# Starting the RFMS Uploader on NAS

## Quick Start

The application is already set up on the NAS at `/volume1/docker/rfms-uploader`.

### 1. Connect to NAS

```bash
ssh admin@192.168.0.201
```

### 2. Navigate to Application Directory

```bash
cd /volume1/docker/rfms-uploader
```

### 3. Create .env File (if not exists)

```bash
cp .env.example .env
nano .env
```

Update the `.env` file with your actual credentials:
- `SECRET_KEY` - Generate a secure random key
- `RFMS_STORE_CODE` - Your RFMS store code
- `RFMS_USERNAME` - Your RFMS username
- `RFMS_API_KEY` - Your RFMS API key
- `GEMINI_API_KEY` - If using AI features

### 4. Start the Container

```bash
docker-compose -f docker-compose-nas.yml up -d --build
```

### 5. Check Status

```bash
docker-compose -f docker-compose-nas.yml ps
docker-compose -f docker-compose-nas.yml logs -f uploaded
```

### 6. Access Application

The application will be available at:
- **http://192.168.0.201:5007**

## Common Commands

### View Logs
```bash
docker-compose -f docker-compose-nas.yml logs -f uploader
```

### Stop Container
```bash
docker-compose -f docker-compose-nas.yml stop
```

### Start Container
```bash
docker-compose -f docker-compose-nas.yml start
```

### Restart Container
```bash
docker-compose -f docker-compose-nas.yml restart uploader
```

### Rebuild and Restart (after code updates)
```bash
docker-compose -f docker-compose-nas.yml up -d --build
```

### Stop and Remove Container
```bash
docker-compose -f docker-compose-nas.yml down
```

## Troubleshooting

### Container Won't Start
- Check logs: `docker-compose -f docker-compose-nas.yml logs uploader`
- Verify .env file exists: `ls -la .env`
- Check directory permissions: `ls -la instance uploads logs`

### Port Already in Use
- Check what's using port 5007: `netstat -tuln | grep 5007`
- Or change port in `docker-compose-nas.yml` and `.env`

### Database Issues
- Ensure `instance/` directory has write permissions: `chmod 755 instance`
- Check database file: `ls -la instance/rfms_xtracr.db`

### File Upload Issues
- Verify `uploads/` directory has write permissions: `chmod 755 uploads`
- Check disk space: `df -h`

