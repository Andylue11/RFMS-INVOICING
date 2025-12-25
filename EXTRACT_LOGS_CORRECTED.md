# Corrected Commands for Extracting Server Log Files

## Issue Found
The log file is NOT at `/app/logs/app.log` in the container. 
The application writes to `app.log` in the working directory (`/app/app.log`).

## Correct Commands for Docker Container

### Find where the log file actually is
```bash
# Check if log file exists at root of app directory
docker exec pdf-extractor ls -lh /app/app.log

# Or find the log file
docker exec pdf-extractor find /app -name "app.log" -type f
```

### Extract log file from correct location
```bash
# Copy app.log from /app/app.log (correct location)
docker cp pdf-extractor:/app/app.log ./app.log

# Copy with timestamp
docker cp pdf-extractor:/app/app.log "./app_$(date +%Y%m%d_%H%M%S).log"
```

### OR use Docker logs (recommended - includes stdout/stderr)
```bash
# Save all container logs (includes both stdout and app.log content)
docker logs pdf-extractor > server_logs.txt

# Save last 1000 lines
docker logs pdf-extractor --tail 1000 > server_logs_last_1000.txt

# Save with timestamps
docker logs pdf-extractor --timestamps > server_logs_with_timestamps.txt

# Save logs from last hour
docker logs pdf-extractor --since 1h > logs_last_hour.txt
```

### Filter for specific errors
```bash
# Filter for PDF creation errors
docker logs pdf-extractor 2>&1 | grep -i "create.*multiple\|504\|timeout\|PDF" > pdf_creation_logs.txt

# Filter for errors only
docker logs pdf-extractor 2>&1 | grep -i error > errors.log
```

## From SSH (Synology NAS)

If you're SSH'd into the server:

```bash
cd /volume1/docker/pdf-extractor

# Extract logs directly
docker logs pdf-extractor --tail 1000 > server_logs.txt

# Or copy from container
docker cp pdf-extractor:/app/app.log ./app.log

# Check if logs volume has the file (if volume mounted)
ls -lh logs/app.log 2>/dev/null || echo "Log file not in logs directory"
```

## Recommendation: Use Docker logs (Easiest)

**The easiest way is to use `docker logs` directly** - this captures all output including:
- Application logs (from FileHandler)
- stdout/stderr output
- All werkzeug HTTP logs
- All Python logging

```bash
# Simple one-liner to extract all logs
docker logs pdf-extractor > server_logs.txt

# Or last 1000 lines
docker logs pdf-extractor --tail 1000 > server_logs.txt
```

This is what you already did successfully with:
```bash
docker logs pdf-extractor --tail 1000 > server_logs.txt
docker logs pdf-extractor --since 1h > logs_last_hour.txt
```

These commands work perfectly! The log file at `/app/logs/app.log` doesn't exist because the app writes to `/app/app.log` instead.

