# Update without sudo - Check docker group and use appropriate method

$server = "atoz@AtozServer"
$path = "/volume1/docker/rfms-uploader"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "RFMS-Uploader Update (No Sudo)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if user is in docker group
Write-Host "Checking Docker access..." -ForegroundColor Yellow
$dockerCheck = ssh $server "groups | grep -q docker && echo 'in-docker-group' || echo 'not-in-docker-group'"
$dockerCheck = $dockerCheck.Trim()

if ($dockerCheck -eq "in-docker-group") {
    Write-Host "✓ User is in docker group" -ForegroundColor Green
    $useSudo = $false
} else {
    Write-Host "⚠ User not in docker group" -ForegroundColor Yellow
    Write-Host "Trying to find Docker without sudo..." -ForegroundColor Yellow
    
    # Try to find docker in common locations
    $dockerPath = ssh $server "if [ -f /usr/local/bin/docker ]; then echo '/usr/local/bin/docker'; elif [ -f /usr/bin/docker ]; then echo '/usr/bin/docker'; elif command -v docker >/dev/null 2>&1; then echo 'docker'; else echo 'not-found'; fi"
    $dockerPath = $dockerPath.Trim()
    
    if ($dockerPath -ne "not-found") {
        Write-Host "✓ Found Docker at: $dockerPath" -ForegroundColor Green
        $useSudo = $false
    } else {
        Write-Host "❌ Docker not accessible without sudo" -ForegroundColor Red
        Write-Host ""
        Write-Host "SOLUTION: Add user to docker group on server:" -ForegroundColor Yellow
        Write-Host "  ssh atoz@AtozServer 'sudo usermod -aG docker atoz'" -ForegroundColor Cyan
        Write-Host "  Then log out and back in, or use Docker GUI method" -ForegroundColor Cyan
        exit 1
    }
}

# Find docker-compose command
Write-Host ""
Write-Host "Detecting docker-compose command..." -ForegroundColor Yellow
$dockerComposeCmd = ssh $server "if docker compose version >/dev/null 2>&1; then echo 'docker compose'; elif command -v docker-compose >/dev/null 2>&1; then echo 'docker-compose'; else echo 'docker compose'; fi"
$dockerComposeCmd = $dockerComposeCmd.Trim()
Write-Host "Using: $dockerComposeCmd" -ForegroundColor Green

# Step 1: Setup GitHub SSH
Write-Host ""
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

