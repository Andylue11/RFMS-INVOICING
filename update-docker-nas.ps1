# PowerShell script to update and restart Docker container on Synology NAS
# Usage: .\update-docker-nas.ps1

param(
    [string]$NasUser = "atoz",
    [string]$NasHost = "192.168.0.201",
    [string]$NasPath = "/volume1/docker/pdf-extractor"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RFMS Uploader - NAS Docker Update Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if SSH is available
$sshAvailable = Get-Command ssh -ErrorAction SilentlyContinue
if (-not $sshAvailable) {
    Write-Host "Error: SSH not found. Please install OpenSSH client." -ForegroundColor Red
    Write-Host "Install with: Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0" -ForegroundColor Yellow
    exit 1
}

Write-Host "Connecting to NAS: ${NasUser}@${NasHost}" -ForegroundColor Yellow
Write-Host "Docker path: ${NasPath}" -ForegroundColor Yellow
Write-Host ""

# Step 1: Stop and remove existing container
Write-Host "[1/4] Stopping existing container..." -ForegroundColor Yellow
$stopCommand = "cd ${NasPath} && docker-compose down"
ssh "${NasUser}@${NasHost}" $stopCommand
if ($LASTEXITCODE -eq 0) {
    Write-Host "      Container stopped and removed" -ForegroundColor Green
} else {
    Write-Host "      No existing container found (this is OK)" -ForegroundColor Yellow
}

# Step 2: Remove old image (forces rebuild)
Write-Host "[2/4] Removing old Docker image..." -ForegroundColor Yellow
$removeImageCommand = "docker rmi pdf-extractor-pdf-extractor 2>/dev/null || true"
ssh "${NasUser}@${NasHost}" $removeImageCommand
Write-Host "      Old image removed (if it existed)" -ForegroundColor Green

# Step 3: Rebuild Docker image
Write-Host "[3/4] Rebuilding Docker image..." -ForegroundColor Yellow
$buildCommand = "cd ${NasPath} && docker-compose build --no-cache"
ssh "${NasUser}@${NasHost}" $buildCommand
if ($LASTEXITCODE -eq 0) {
    Write-Host "      Docker image rebuilt successfully" -ForegroundColor Green
} else {
    Write-Host "      Error: Docker build failed" -ForegroundColor Red
    exit 1
}

# Step 4: Start container
Write-Host "[4/4] Starting Docker container..." -ForegroundColor Yellow
$startCommand = "cd ${NasPath} && docker-compose up -d"
ssh "${NasUser}@${NasHost}" $startCommand
if ($LASTEXITCODE -eq 0) {
    Write-Host "      Container started successfully" -ForegroundColor Green
} else {
    Write-Host "      Error: Failed to start container" -ForegroundColor Red
    exit 1
}

# Wait a moment for container to start
Start-Sleep -Seconds 3

# Show container status
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Container Status:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
$statusCommand = "cd ${NasPath} && docker-compose ps"
ssh "${NasUser}@${NasHost}" $statusCommand

# Show logs
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Recent Logs:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
$logsCommand = "cd ${NasPath} && docker-compose logs --tail=20"
ssh "${NasUser}@${NasHost}" $logsCommand

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Update Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Application should be available at: http://${NasHost}:5005" -ForegroundColor Yellow
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  View logs:    ssh ${NasUser}@${NasHost} 'cd ${NasPath} && docker-compose logs -f'" -ForegroundColor White
Write-Host "  Stop:         ssh ${NasUser}@${NasHost} 'cd ${NasPath} && docker-compose down'" -ForegroundColor White
Write-Host "  Restart:      ssh ${NasUser}@${NasHost} 'cd ${NasPath} && docker-compose restart'" -ForegroundColor White
Write-Host "  Shell access: ssh ${NasUser}@${NasHost} 'docker exec -it pdf-extractor bash'" -ForegroundColor White
Write-Host ""

