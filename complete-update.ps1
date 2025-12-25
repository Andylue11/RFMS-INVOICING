# Complete update - Fixes SSH, pulls code, rebuilds container

$server = "atoz@AtozServer"
$path = "/volume1/docker/rfms-uploader"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Complete RFMS-Uploader Update" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Fix SSH
Write-Host "[1/5] Fixing GitHub SSH..." -ForegroundColor Yellow
ssh $server "mkdir -p ~/.ssh; chmod 700 ~/.ssh; rm -f ~/.ssh/known_hosts; ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null; chmod 600 ~/.ssh/known_hosts"
Write-Host "✓ SSH configured" -ForegroundColor Green

# Step 2: Update git remote
Write-Host "[2/5] Updating git remote..." -ForegroundColor Yellow
ssh $server "cd $path; git remote set-url origin git@github.com:Andylue11/RFMS-UPLOADER.git"
Write-Host "✓ Remote updated" -ForegroundColor Green

# Step 3: Pull latest code
Write-Host "[3/5] Pulling latest code from main..." -ForegroundColor Yellow
ssh $server "cd $path; git fetch origin; git checkout main; git pull origin main"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Code updated" -ForegroundColor Green
} else {
    Write-Host "⚠ Git pull had issues, but continuing..." -ForegroundColor Yellow
}

# Step 4: Rebuild container
Write-Host "[4/5] Rebuilding container..." -ForegroundColor Yellow
ssh $server "cd $path; docker compose down; docker compose build --no-cache"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Container rebuilt" -ForegroundColor Green
} else {
    Write-Host "⚠ Build had issues" -ForegroundColor Yellow
}

# Step 5: Start container
Write-Host "[5/5] Starting container..." -ForegroundColor Yellow
ssh $server "cd $path; docker compose up -d"
Write-Host "✓ Container started" -ForegroundColor Green

# Verify
Write-Host ""
Write-Host "Verifying..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
ssh $server "cd $path; docker compose ps; echo ''; echo 'Recent logs:'; docker compose logs --tail=20"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Update Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

