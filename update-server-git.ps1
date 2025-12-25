# Update RFMS-Uploader on server using Git
# Usage: .\update-server-git.ps1

$ErrorActionPreference = "Stop"

$server = "atoz@192.168.0.201"
$remoteDir = "/volume1/docker/rfms-uploader"
$containerName = "rfms-uploader"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "RFMS-Uploader - Update Server via Git" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server: $server"
Write-Host "Remote Directory: $remoteDir"
Write-Host ""

# Step 1: Test SSH connection
Write-Host "[1/5] Testing SSH connection..." -ForegroundColor Yellow
$testResult = ssh -o ConnectTimeout=5 -o LogLevel=ERROR $server "echo 'Connection successful'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Cannot connect to server" -ForegroundColor Red
    Write-Host "Test connection manually: ssh $server" -ForegroundColor Yellow
    exit 1
}
Write-Host "  [OK] SSH connection successful" -ForegroundColor Green

# Step 2: Check if git repository exists on server
Write-Host ""
Write-Host "[2/5] Checking Git repository on server..." -ForegroundColor Yellow
$gitCheck = ssh -o LogLevel=ERROR $server "cd $remoteDir && git status" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] Git repository not found or not initialized" -ForegroundColor Yellow
    Write-Host "  Initializing git repository..." -ForegroundColor Gray
    
    # Initialize git if it doesn't exist
    ssh -o LogLevel=ERROR $server "cd $remoteDir && git init && git remote add origin https://github.com/YOUR_REPO.git 2>/dev/null || true" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [WARN] Could not initialize git (continuing with manual update...)" -ForegroundColor Yellow
    }
}

# Step 3: Pull latest changes from git
Write-Host ""
Write-Host "[3/5] Pulling latest changes from Git..." -ForegroundColor Yellow

$gitPullCommand = @"
cd $remoteDir && \
git fetch origin && \
git pull origin main || git pull origin master || git pull
"@

Write-Host "  Executing git pull..." -ForegroundColor Gray
$pullOutput = ssh -o LogLevel=ERROR $server $gitPullCommand 2>&1
Write-Host $pullOutput

if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] Git pull may have failed, but continuing..." -ForegroundColor Yellow
    Write-Host "  You may need to manually pull: ssh $server 'cd $remoteDir && git pull'" -ForegroundColor Yellow
}

Write-Host "  [OK] Git pull completed" -ForegroundColor Green

# Step 4: Rebuild container on server
Write-Host ""
Write-Host "[4/5] Rebuilding container on server..." -ForegroundColor Yellow
Write-Host "This may take several minutes..."

$rebuildCommand = @"
cd $remoteDir && \
docker compose down && \
docker compose build --no-cache && \
docker compose up -d
"@

Write-Host "  Executing rebuild commands..." -ForegroundColor Gray
ssh -o LogLevel=ERROR $server $rebuildCommand
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to rebuild container" -ForegroundColor Red
    Write-Host "Check server logs with: ssh $server 'cd $remoteDir && docker compose logs'" -ForegroundColor Yellow
    exit 1
}

Write-Host "  [OK] Container rebuilt and started" -ForegroundColor Green

# Step 5: Wait for container to start
Write-Host ""
Write-Host "[5/5] Waiting for container to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Step 6: Verify deployment
Write-Host ""
Write-Host "[6/6] Verifying deployment..." -ForegroundColor Yellow

# Check container status
$containerStatus = ssh $server "docker ps --filter name=$containerName --format '{{.Status}}'" 2>&1
if ($containerStatus -and $containerStatus -notmatch "error|Error") {
    Write-Host "  [OK] Container is running: $containerStatus" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Could not verify container status" -ForegroundColor Yellow
}

# Show recent logs
Write-Host ""
Write-Host "Recent container logs:" -ForegroundColor Cyan
ssh $server "cd $remoteDir && docker compose logs --tail=20" 2>&1

# Show git status
Write-Host ""
Write-Host "Git status on server:" -ForegroundColor Cyan
ssh $server "cd $remoteDir && git log --oneline -5 && echo '' && git status" 2>&1

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Update Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server: $server"
Write-Host "Container: $containerName"
Write-Host "Remote Directory: $remoteDir"
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  View logs:    ssh $server 'cd $remoteDir && docker compose logs -f'"
Write-Host "  Git status:   ssh $server 'cd $remoteDir && git status'"
Write-Host "  Git pull:     ssh $server 'cd $remoteDir && git pull'"
Write-Host "  Restart:      ssh $server 'cd $remoteDir && docker compose restart'"
Write-Host "  Stop:         ssh $server 'cd $remoteDir && docker compose down'"
Write-Host ""

