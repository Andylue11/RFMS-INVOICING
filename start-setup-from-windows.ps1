# PowerShell Script to Connect to Synology NAS and Run Setup
# Run this script to automatically SSH into your NAS and complete the setup

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Synology NAS Setup Assistant" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

$NAS_USER = "atoz"
$NAS_IP = "192.168.0.201"
$NAS_PATH = "/volume1/docker/pdf-extractor"

Write-Host ""
Write-Host "Connecting to NAS..." -ForegroundColor Yellow
Write-Host "NAS: $NAS_USER@$NAS_IP" -ForegroundColor Cyan
Write-Host "Path: $NAS_PATH" -ForegroundColor Cyan
Write-Host ""

# First, copy the setup script to the NAS
Write-Host "Step 1: Copying setup script to NAS..." -ForegroundColor Magenta
scp -o StrictHostKeyChecking=no setup-now.sh "${NAS_USER}@${NAS_IP}:${NAS_PATH}/"

Write-Host ""
Write-Host "Step 2: Now we'll SSH into the NAS..." -ForegroundColor Magenta
Write-Host "Please enter your NAS password when prompted." -ForegroundColor Yellow
Write-Host ""

# SSH into the NAS and run the setup
$setupCommands = @"
cd $NAS_PATH
chmod +x setup-now.sh
bash setup-now.sh
"@

Write-Host "Step 3: Running setup script..." -ForegroundColor Magenta
ssh -o StrictHostKeyChecking=no "${NAS_USER}@${NAS_IP}" $setupCommands

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your application should now be running at:" -ForegroundColor Yellow
Write-Host "http://$NAS_IP:5005" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to open it in your browser..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Start-Process "http://$NAS_IP:5005"
