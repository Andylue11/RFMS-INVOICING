# Update RFMS-Uploader Container on Office Server

## Quick Update Command

Run this command from your local machine to update the container on the office server:

```bash
ssh atoz@AtozServer 'cd /volume1/docker/RFMS-UPLOADER && git pull origin stock-recv && docker-compose down && docker-compose build --no-cache && docker-compose up -d'
```

## If Path is Different

First, find the correct path:

```bash
ssh atoz@AtozServer 'find /volume1/docker -name "docker-compose.yml" -type f | xargs grep -l "rfms-uploader"'
```

Then update the path in the command above.

## Step-by-Step Process

1. **SSH into the server:**
   ```bash
   ssh atoz@AtozServer
   ```

2. **Navigate to the application directory:**
   ```bash
   cd /volume1/docker/RFMS-UPLOADER
   # OR wherever the app is located
   ```

3. **Pull latest code:**
   ```bash
   git pull origin stock-recv
   ```

4. **Stop the container:**
   ```bash
   docker-compose down
   ```

5. **Rebuild the container:**
   ```bash
   docker-compose build --no-cache
   ```

6. **Start the container:**
   ```bash
   docker-compose up -d
   ```

7. **Check status:**
   ```bash
   docker-compose ps
   docker-compose logs --tail=50
   ```

## Verify Update

Check if the application is running:

```bash
curl http://localhost:5007
```

Or check the container logs:

```bash
docker-compose logs -f rfms-uploader
```

## Troubleshooting

If the container fails to start:

1. Check logs: `docker-compose logs`
2. Check if port 5007 is available: `netstat -tuln | grep 5007`
3. Verify .env file exists and has correct settings
4. Check Docker is running: `docker ps`

## Rollback (if needed)

If something goes wrong, you can rollback to previous version:

```bash
cd /volume1/docker/RFMS-UPLOADER
git log --oneline -10  # See recent commits
git checkout <previous-commit-hash>
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

