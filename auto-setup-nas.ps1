# Automated Setup Script for Synology NAS
$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Automated PDF Extractor Setup" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

$NAS_USER = "atoz"
$NAS_IP = "192.168.0.201"
$NAS_PASSWORD = "SimVek22`$`$22"
$NAS_PATH = "/volume1/docker/pdf-extractor"

Write-Host ""
Write-Host "Step 1: Copying files to NAS..." -ForegroundColor Yellow

# Create plink command file for password
$plinkCommands = @"
cd /volume1/docker/pdf-extractor
chmod +x setup-now.sh
bash setup-now.sh
"@

# Copy files using SSH with password
$copyCommand = "echo $NAS_PASSWORD | plink -pw '$NAS_PASSWORD' -batch $NAS_USER@$NAS_IP 'mkdir -p $NAS_PATH'"
Invoke-Expression $copyCommand

Write-Host "Copying setup-now.sh..." -ForegroundColor Cyan
plink -pw "$NAS_PASSWORD" -batch "$NAS_USER@$NAS_IP" "cd $NAS_PATH && cat > setup-now.sh" < setup-now.sh

Write-Host "Copying SETUP-GUIDE.md..." -ForegroundColor Cyan
plink -pw "$NAS_PASSWORD" -batch "$NAS_USER@$NAS_IP" "cd $NAS_PATH && cat > SETUP-GUIDE.md" < SETUP-GUIDE.md

Write-Host ""
Write-Host "Step 2: Running setup on NAS..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Cyan

# Run the setup commands
plink -pw "$NAS_PASSWORD" "$NAS_USER@$NAS_IP" "cd $NAS_PATH && chmod +x setup-now.sh && bash setup-now.sh"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your application should now be available at:" -ForegroundColor Yellow
Write-Host "http://$NAS_IP:5000" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to open it in your browser..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Start-Process "http://$NAS_IP:5000"
