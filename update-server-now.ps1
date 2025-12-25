# PowerShell script to update RFMS-Uploader on server
# Fixed for Windows line endings and Synology docker-compose

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Updating RFMS-Uploader on Server" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Setup GitHub SSH
Write-Host "[1/6] Setting up GitHub SSH..." -ForegroundColor Yellow
ssh atoz@AtozServer "mkdir -p ~/.ssh; chmod 700 ~/.ssh; ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null; chmod 600 ~/.ssh/known_hosts"

# Step 2: Update git remote
Write-Host "[2/6] Updating git remote..." -ForegroundColor Yellow
ssh atoz@AtozServer "cd /volume1/docker/rfms-uploader; git remote set-url origin git@github.com:Andylue11/RFMS-UPLOADER.git"

# Step 3: Pull latest code
Write-Host "[3/6] Pulling latest code from main..." -ForegroundColor Yellow
ssh atoz@AtozServer "cd /volume1/docker/rfms-uploader; git fetch origin; git checkout main; git pull origin main"

# Step 4: Stop container
Write-Host "[4/6] Stopping container..." -ForegroundColor Yellow
ssh atoz@AtozServer "cd /volume1/docker/rfms-uploader; docker-compose down"

# Step 5: Rebuild container
Write-Host "[5/6] Rebuilding container (this may take a few minutes)..." -ForegroundColor Yellow
ssh atoz@AtozServer "cd /volume1/docker/rfms-uploader; docker-compose build --no-cache"

# Step 6: Start container
Write-Host "[6/6] Starting container..." -ForegroundColor Yellow
ssh atoz@AtozServer "cd /volume1/docker/rfms-uploader; docker-compose up -d"

# Check status
Write-Host ""
Write-Host "Checking status..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
ssh atoz@AtozServer "cd /volume1/docker/rfms-uploader; docker-compose ps"

Write-Host ""
Write-Host "Recent logs:" -ForegroundColor Yellow
ssh atoz@AtozServer "cd /volume1/docker/rfms-uploader; docker-compose logs --tail=30"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Update Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
