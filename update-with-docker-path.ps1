# Update script that finds and uses correct Docker path

$server = "atoz@AtozServer"
$path = "/volume1/docker/rfms-uploader"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "RFMS-Uploader Update (with Docker path detection)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Find Docker paths
Write-Host "Detecting Docker installation..." -ForegroundColor Yellow
$dockerCmd = ssh $server "if command -v docker >/dev/null 2>&1; then echo 'docker'; elif [ -f /usr/local/bin/docker ]; then echo '/usr/local/bin/docker'; elif [ -f /usr/bin/docker ]; then echo '/usr/bin/docker'; else echo 'docker'; fi"
$dockerCmd = $dockerCmd.Trim()

# Find docker-compose
$dockerComposeCmd = ssh $server "if command -v docker-compose >/dev/null 2>&1; then echo 'docker-compose'; elif docker compose version >/dev/null 2>&1; then echo 'docker compose'; elif [ -f /usr/local/bin/docker-compose ]; then echo '/usr/local/bin/docker-compose'; else echo 'docker compose'; fi"
$dockerComposeCmd = $dockerComposeCmd.Trim()

Write-Host "Using Docker: $dockerCmd" -ForegroundColor Green
Write-Host "Using Docker Compose: $dockerComposeCmd" -ForegroundColor Green
Write-Host ""

# Step 1: Setup GitHub SSH
Write-Host "[1/5] Setting up GitHub SSH..." -ForegroundColor Yellow
ssh $server "mkdir -p ~/.ssh; chmod 700 ~/.ssh; ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null; chmod 600 ~/.ssh/known_hosts"

# Step 2: Update git remote and pull
Write-Host "[2/5] Updating code..." -ForegroundColor Yellow
ssh $server "cd $path; git remote set-url origin git@github.com:Andylue11/RFMS-UPLOADER.git; git fetch origin; git checkout main; git pull origin main"

# Step 3: Stop container
Write-Host "[3/5] Stopping container..." -ForegroundColor Yellow
ssh $server "cd $path; $dockerComposeCmd down"

# Step 4: Rebuild container
Write-Host "[4/5] Rebuilding container (this may take a few minutes)..." -ForegroundColor Yellow
ssh $server "cd $path; $dockerComposeCmd build --no-cache"

# Step 5: Start container
Write-Host "[5/5] Starting container..." -ForegroundColor Yellow
ssh $server "cd $path; $dockerComposeCmd up -d"

# Verify
Write-Host ""
Write-Host "Verifying..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
ssh $server "cd $path; $dockerComposeCmd ps; echo ''; echo 'Recent logs:'; $dockerComposeCmd logs --tail=20"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Update Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

