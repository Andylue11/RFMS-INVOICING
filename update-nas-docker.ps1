# PowerShell script to update and restart Docker container on Synology NAS
# Usage: .\update-nas-docker.ps1

param(
    [string]$NasUser = "atoz",
    [string]$NasHost = "192.168.0.201",
    [string]$NasPath = "/volume1/docker/pdf-extractor"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RFMS Uploader - NAS Docker Update" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NAS: ${NasUser}@${NasHost}" -ForegroundColor Yellow
Write-Host "Path: ${NasPath}" -ForegroundColor Yellow
Write-Host ""

# Check if SSH is available
try {
    $null = Get-Command ssh -ErrorAction Stop
} catch {
    Write-Host "Error: SSH not found. Install OpenSSH Client first." -ForegroundColor Red
    Write-Host "Run: Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0" -ForegroundColor Yellow
    exit 1
}

# Function to run SSH command
function Invoke-SSHCommand {
    param([string]$Command)
    $fullCommand = "ssh -o StrictHostKeyChecking=no ${NasUser}@${NasHost} `"${Command}`""
    Invoke-Expression $fullCommand
    return $LASTEXITCODE
}

# Step 1: Stop existing container
Write-Host "[1/5] Stopping existing container..." -ForegroundColor Yellow
$exitCode = Invoke-SSHCommand "cd ${NasPath} && docker-compose down"
if ($exitCode -eq 0) {
    Write-Host "      ✓ Container stopped" -ForegroundColor Green
} else {
    Write-Host "      ⚠ No container found (OK for first run)" -ForegroundColor Yellow
}

# Step 2: Remove old image
Write-Host "[2/5] Removing old Docker image..." -ForegroundColor Yellow
Invoke-SSHCommand "docker rmi pdf-extractor-pdf-extractor 2>/dev/null || true" | Out-Null
Write-Host "      ✓ Old image cleanup done" -ForegroundColor Green

# Step 3: Rebuild Docker image
Write-Host "[3/5] Rebuilding Docker image (this may take a few minutes)..." -ForegroundColor Yellow
$exitCode = Invoke-SSHCommand "cd ${NasPath} && docker-compose build --no-cache"
if ($exitCode -eq 0) {
    Write-Host "      ✓ Docker image rebuilt successfully" -ForegroundColor Green
} else {
    Write-Host "      ✗ Error: Docker build failed" -ForegroundColor Red
    Write-Host "      Check the error messages above" -ForegroundColor Yellow
    exit 1
}

# Step 4: Start container
Write-Host "[4/5] Starting Docker container..." -ForegroundColor Yellow
$exitCode = Invoke-SSHCommand "cd ${NasPath} && docker-compose up -d"
if ($exitCode -eq 0) {
    Write-Host "      ✓ Container started successfully" -ForegroundColor Green
} else {
    Write-Host "      ✗ Error: Failed to start container" -ForegroundColor Red
    exit 1
}

# Wait for container to start
Write-Host "[5/5] Waiting for container to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Show container status
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Container Status:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Invoke-SSHCommand "cd ${NasPath} && docker-compose ps"

# Show recent logs
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Recent Logs (last 15 lines):" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Invoke-SSHCommand "cd ${NasPath} && docker-compose logs --tail=15"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Update Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Application URL: http://${NasHost}:5005" -ForegroundColor Yellow
Write-Host ""
Write-Host "Quick Commands:" -ForegroundColor Cyan
Write-Host "  View logs:    ssh ${NasUser}@${NasHost} 'cd ${NasPath} && docker-compose logs -f'" -ForegroundColor White
Write-Host "  Stop:         ssh ${NasUser}@${NasHost} 'cd ${NasPath} && docker-compose down'" -ForegroundColor White
Write-Host "  Restart:      ssh ${NasUser}@${NasHost} 'cd ${NasPath} && docker-compose restart'" -ForegroundColor White
Write-Host "  Status:       ssh ${NasUser}@${NasHost} 'cd ${NasPath} && docker-compose ps'" -ForegroundColor White
Write-Host ""

