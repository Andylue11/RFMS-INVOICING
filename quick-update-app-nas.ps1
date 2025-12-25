# PowerShell script to quickly update app.py in running container
# Use this for quick testing, but rebuild for production

param(
    [string]$NasUser = "atoz",
    [string]$NasHost = "192.168.0.201",
    [string]$NasPath = "/volume1/docker/pdf-extractor"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Quick Update - Copy app.py to Container" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if container is running
$containerStatus = ssh "${NasUser}@${NasHost}" "docker ps | grep pdf-extractor"
if (-not $containerStatus) {
    Write-Host "ERROR: Container is not running!" -ForegroundColor Red
    Write-Host "Please start the container first" -ForegroundColor Yellow
    exit 1
}

Write-Host "Container is running. Copying app.py..." -ForegroundColor Yellow

# Copy app.py into the container
ssh "${NasUser}@${NasHost}" "cd ${NasPath} && docker cp app.py pdf-extractor:/app/app.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ app.py copied successfully" -ForegroundColor Green
    
    # Restart the container
    Write-Host "Restarting container..." -ForegroundColor Yellow
    ssh "${NasUser}@${NasHost}" "cd ${NasPath} && docker-compose restart"
    
    Write-Host "✓ Container restarted" -ForegroundColor Green
    Write-Host "Waiting for application to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Check logs
    Write-Host ""
    Write-Host "Recent logs:" -ForegroundColor Cyan
    ssh "${NasUser}@${NasHost}" "cd ${NasPath} && docker-compose logs --tail=20"
    
    Write-Host ""
    Write-Host "✅ Quick update complete!" -ForegroundColor Green
    Write-Host "NOTE: This is a temporary fix. For production, rebuild the image." -ForegroundColor Yellow
} else {
    Write-Host "ERROR: Failed to copy app.py" -ForegroundColor Red
    exit 1
}

