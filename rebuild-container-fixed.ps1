# Rebuild container - Stops all containers first to free up port

$server = "atoz@AtozServer"
$path = "/volume1/docker/rfms-uploader"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Rebuilding RFMS-Uploader Container" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop all containers (including any orphaned ones)
Write-Host "[1/4] Stopping all containers..." -ForegroundColor Yellow
ssh $server "cd $path; docker compose down; docker stop rfms-uploader 2>/dev/null || true; docker rm rfms-uploader 2>/dev/null || true"

# Step 2: Check if port is still in use
Write-Host "[2/4] Checking port 5007..." -ForegroundColor Yellow
$portCheck = ssh $server "netstat -tuln | grep :5007 || echo 'port-free'"
if ($portCheck -notmatch "port-free") {
    Write-Host "⚠️  Port 5007 still in use. Finding process..." -ForegroundColor Yellow
    ssh $server "lsof -ti:5007 | xargs kill -9 2>/dev/null || true"
    Start-Sleep -Seconds 2
}

# Step 3: Rebuild container
Write-Host "[3/4] Rebuilding container (this may take a few minutes)..." -ForegroundColor Yellow
ssh $server "cd $path; docker compose build --no-cache"

# Step 4: Start container
Write-Host "[4/4] Starting container..." -ForegroundColor Yellow
ssh $server "cd $path; docker compose up -d"

# Verify
Write-Host ""
Write-Host "Verifying..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
ssh $server "cd $path; docker compose ps; echo ''; echo 'Recent logs:'; docker compose logs --tail=30"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Rebuild Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

