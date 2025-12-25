# Commands for Extracting Server Log Files

## Local Development

### View logs in real-time (tail)
```bash
# Windows PowerShell
Get-Content app.log -Tail 50 -Wait

# Windows CMD
tail -f app.log

# Or open the file directly
notepad app.log
```

### Copy/Extract log file
```bash
# Copy log file to another location
copy app.log logs_backup\app_$(Get-Date -Format 'yyyyMMdd_HHmmss').log

# Or just view it
type app.log
```

## Production (Docker/Synology)

### View Docker container logs

#### View last N lines
```bash
docker logs pdf-extractor --tail 100

# Or using docker-compose
docker-compose logs --tail 100 pdf-extractor

# View all logs
docker logs pdf-extractor

# Follow logs in real-time
docker logs pdf-extractor -f

# Or using docker-compose
docker-compose logs -f pdf-extractor
```

#### View logs with timestamp
```bash
docker logs pdf-extractor --timestamps --tail 100
```

#### View logs since specific time
```bash
docker logs pdf-extractor --since 1h
docker logs pdf-extractor --since 30m
docker logs pdf-extractor --since 2024-01-01T00:00:00
```

### Extract/Copy logs from Docker container

#### Copy log file from container to local machine
```bash
# Copy app.log from container to current directory
docker cp pdf-extractor:/app/logs/app.log ./app.log

# Copy with timestamp in filename
docker cp pdf-extractor:/app/logs/app.log "./app_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Copy entire logs directory
docker cp pdf-extractor:/app/logs ./logs_backup
```

#### Save Docker logs to file
```bash
# Save container logs to file
docker logs pdf-extractor > app_logs.txt

# Save with timestamps
docker logs pdf-extractor --timestamps > app_logs_with_timestamps.txt

# Save last 1000 lines
docker logs pdf-extractor --tail 1000 > app_logs_last_1000.txt

# Save all logs from last hour
docker logs pdf-extractor --since 1h > app_logs_last_hour.txt
```

### Extract logs via SSH (if SSH access available)

If you have SSH access to the Synology NAS:

```bash
# SSH into the server
ssh username@192.168.0.201

# Navigate to application directory
cd /volume1/docker/pdf-extractor

# View logs
cat logs/app.log
tail -f logs/app.log
tail -n 100 logs/app.log

# Copy logs to a backup location
cp logs/app.log logs/app_backup_$(date +%Y%m%d_%H%M%S).log

# Or if logs are in Docker volume, extract via docker cp from SSH session
docker cp pdf-extractor:/app/logs/app.log /volume1/docker/pdf-extractor/logs_backup/
```

### Extract logs directly from host (if volume mounted)

If the logs directory is mounted as a volume:

```bash
# On Synology NAS via SSH
cd /volume1/docker/pdf-extractor
ls -lh logs/
cat logs/app.log
tail -f logs/app.log

# Copy to backup
cp logs/app.log logs/app_backup_$(date +%Y%m%d_%H%M%S).log
```

## Filter Logs for Specific Errors

### Search for errors in logs
```bash
# Docker logs - filter for errors
docker logs pdf-extractor 2>&1 | grep -i error

# Docker logs - filter for specific text
docker logs pdf-extractor 2>&1 | grep -i "504\|timeout\|PDF"

# Save filtered logs
docker logs pdf-extractor 2>&1 | grep -i error > errors.log

# Windows PowerShell - filter logs
Get-Content app.log | Select-String -Pattern "error|504|timeout" -CaseSensitive:$false
```

### Extract logs for specific time period
```bash
# Extract logs from last 24 hours
docker logs pdf-extractor --since 24h > logs_last_24h.txt

# Extract logs from specific date
docker logs pdf-extractor --since "2024-01-15T00:00:00" --until "2024-01-16T00:00:00" > logs_jan15.txt
```

## Quick Reference Commands

### Most Common - View recent logs
```bash
docker logs pdf-extractor --tail 100 -f
```

### Most Common - Extract logs to file
```bash
docker logs pdf-extractor --tail 1000 > server_logs.txt
```

### Most Common - Copy log file from container
```bash
docker cp pdf-extractor:/app/logs/app.log ./app.log
```

## Container Name Check

If you're unsure of the container name:
```bash
# List all running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Filter for pdf-extractor
docker ps | grep pdf-extractor
```

## For Multiple PDF Creation Debugging

### Extract logs with PDF creation keywords
```bash
# Filter for multiple PDF creation errors
docker logs pdf-extractor 2>&1 | grep -i "create.*multiple\|504\|timeout\|PDF" > pdf_creation_logs.txt

# View logs around PDF creation time
docker logs pdf-extractor --since 1h | grep -i "multiple.*installer\|PDF" > recent_pdf_logs.txt
```

## Log File Locations Summary

- **Local Development**: `app.log` (in project root)
- **Docker Container**: `/app/logs/app.log` (inside container)
- **Synology (if volume mounted)**: `/volume1/docker/pdf-extractor/logs/app.log`

