# PowerShell script to update and restart local Docker container
# Usage: .\update-docker-local.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RFMS Uploader - Docker Update Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Navigate to project directory
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir
Write-Host "[1/6] Changed to project directory: $projectDir" -ForegroundColor Green

# Step 2: Pull latest changes from git (optional - comment out if not using git)
Write-Host "[2/6] Pulling latest changes from git..." -ForegroundColor Yellow
try {
    git pull
    Write-Host "      Git pull completed successfully" -ForegroundColor Green
} catch {
    Write-Host "      Warning: Git pull failed or not in a git repository" -ForegroundColor Yellow
}

# Step 3: Stop and remove existing container
Write-Host "[3/6] Stopping existing container..." -ForegroundColor Yellow
docker-compose -f docker-compose.local.yml down
if ($LASTEXITCODE -eq 0) {
    Write-Host "      Container stopped and removed" -ForegroundColor Green
} else {
    Write-Host "      No existing container found (this is OK)" -ForegroundColor Yellow
}

# Step 4: Remove old image (optional - forces rebuild)
Write-Host "[4/6] Removing old Docker image..." -ForegroundColor Yellow
docker rmi pdf-extractor-local-pdf-extractor 2>$null
Write-Host "      Old image removed (if it existed)" -ForegroundColor Green

# Step 5: Rebuild Docker image
Write-Host "[5/6] Rebuilding Docker image..." -ForegroundColor Yellow
docker-compose -f docker-compose.local.yml build --no-cache
if ($LASTEXITCODE -eq 0) {
    Write-Host "      Docker image rebuilt successfully" -ForegroundColor Green
} else {
    Write-Host "      Error: Docker build failed" -ForegroundColor Red
    exit 1
}

# Step 6: Start container
Write-Host "[6/6] Starting Docker container..." -ForegroundColor Yellow
docker-compose -f docker-compose.local.yml up -d
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
docker-compose -f docker-compose.local.yml ps

# Show logs
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Recent Logs:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
docker-compose -f docker-compose.local.yml logs --tail=20

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Update Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Application should be available at: http://localhost:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  View logs:    docker-compose -f docker-compose.local.yml logs -f" -ForegroundColor White
Write-Host "  Stop:         docker-compose -f docker-compose.local.yml down" -ForegroundColor White
Write-Host "  Restart:      docker-compose -f docker-compose.local.yml restart" -ForegroundColor White
Write-Host "  Shell access: docker exec -it pdf-extractor-local bash" -ForegroundColor White
Write-Host ""

