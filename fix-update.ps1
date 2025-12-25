# Fix Update Script - Force update and rebuild
# Run this if the update didn't work

$NasUser = "atoz"
$NasHost = "192.168.0.201"
$NasPath = "/volume1/docker/pdf-extractor"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Force Update Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "1. Pull latest code from GitHub" -ForegroundColor White
Write-Host "2. Force stop and remove container" -ForegroundColor White
Write-Host "3. Force rebuild Docker image (no cache)" -ForegroundColor White
Write-Host "4. Start container" -ForegroundColor White
Write-Host ""
Write-Host "Run these commands one by one in PowerShell:" -ForegroundColor Yellow
Write-Host ""

Write-Host "[Step 1] Pull latest code:" -ForegroundColor Green
Write-Host "ssh ${NasUser}@${NasHost} 'cd ${NasPath} && export HOME=${NasPath} && /bin/git pull origin main'" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter after running Step 1..."

Write-Host ""
Write-Host "[Step 2] Force stop and remove container and images:" -ForegroundColor Green
Write-Host "ssh ${NasUser}@${NasHost} 'cd ${NasPath} && export HOME=${NasPath} && docker compose down && docker rmi pdf-extractor-pdf-extractor 2>/dev/null || true'" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter after running Step 2..."

Write-Host ""
Write-Host "[Step 3] Force rebuild (no cache) and start:" -ForegroundColor Green
Write-Host "ssh ${NasUser}@${NasHost} 'cd ${NasPath} && export HOME=${NasPath} && docker compose build --no-cache && docker compose up -d'" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter after running Step 3..."

Write-Host ""
Write-Host "[Step 4] Check status:" -ForegroundColor Green
Write-Host "ssh ${NasUser}@${NasHost} 'cd ${NasPath} && docker compose ps'" -ForegroundColor White
Write-Host ""
Write-Host "[Step 5] View recent logs:" -ForegroundColor Green
Write-Host "ssh ${NasUser}@${NasHost} 'cd ${NasPath} && docker compose logs --tail=30'" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Update commands ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

