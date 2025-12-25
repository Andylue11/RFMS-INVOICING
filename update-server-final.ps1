# Final update script - Detects docker-compose vs docker compose

$server = "atoz@AtozServer"
$path = "/volume1/docker/rfms-uploader"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Updating RFMS-Uploader on Server" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Detect docker-compose command
Write-Host "Detecting docker-compose command..." -ForegroundColor Yellow
$dockerComposeCmd = ssh $server "if command -v docker-compose >/dev/null 2>&1; then echo 'docker-compose'; elif docker compose version >/dev/null 2>&1; then echo 'docker compose'; else echo 'docker compose'; fi"
$dockerComposeCmd = $dockerComposeCmd.Trim()
Write-Host "Using: $dockerComposeCmd" -ForegroundColor Green
Write-Host ""

# Step 1: Setup GitHub SSH
Write-Host "[1/6] Setting up GitHub SSH..." -ForegroundColor Yellow
ssh $server "mkdir -p ~/.ssh; chmod 700 ~/.ssh; ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null; chmod 600 ~/.ssh/known_hosts"

# Step 2: Update git remote
Write-Host "[2/6] Updating git remote..." -ForegroundColor Yellow
ssh $server "cd $path; git remote set-url origin git@github.com:Andylue11/RFMS-UPLOADER.git"

# Step 3: Pull latest code
Write-Host "[3/6] Pulling latest code from main..." -ForegroundColor Yellow
ssh $server "cd $path; git fetch origin; git checkout main; git pull origin main"

# Step 4: Stop container
Write-Host "[4/6] Stopping container..." -ForegroundColor Yellow
ssh $server "cd $path; $dockerComposeCmd down"

# Step 5: Rebuild container
Write-Host "[5/6] Rebuilding container (this may take a few minutes)..." -ForegroundColor Yellow
ssh $server "cd $path; $dockerComposeCmd build --no-cache"

# Step 6: Start container
Write-Host "[6/6] Starting container..." -ForegroundColor Yellow
ssh $server "cd $path; $dockerComposeCmd up -d"

# Check status
Write-Host ""
Write-Host "Checking status..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
ssh $server "cd $path; $dockerComposeCmd ps"

Write-Host ""
Write-Host "Recent logs:" -ForegroundColor Yellow
ssh $server "cd $path; $dockerComposeCmd logs --tail=30"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Update Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

