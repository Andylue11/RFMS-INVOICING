# Manual Server Update Script
# This version shows you the commands to run manually
# Copy and paste each command into PowerShell when prompted

$NasUser = "atoz"
$NasHost = "192.168.0.201"
$NasPath = "/volume1/docker/pdf-extractor"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Manual Server Update Instructions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Copy and paste these commands one at a time into PowerShell:" -ForegroundColor Yellow
Write-Host ""
Write-Host "[Step 1] Pull latest code from GitHub:" -ForegroundColor Green
Write-Host "ssh ${NasUser}@${NasHost} 'cd ${NasPath} && export HOME=${NasPath} && /bin/git pull origin main'" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter after running Step 1, then continue..." -ForegroundColor Yellow
Read-Host

Write-Host ""
Write-Host "[Step 2] Stop the container:" -ForegroundColor Green
Write-Host "ssh ${NasUser}@${NasHost} 'cd ${NasPath} && export HOME=${NasPath} && docker compose down'" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter after running Step 2, then continue..." -ForegroundColor Yellow
Read-Host

Write-Host ""
Write-Host "[Step 3] Rebuild and start the container:" -ForegroundColor Green
Write-Host "ssh ${NasUser}@${NasHost} 'cd ${NasPath} && export HOME=${NasPath} && docker compose up -d --build'" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter after running Step 3..." -ForegroundColor Yellow
Read-Host

Write-Host ""
Write-Host "[Step 4] Check container status:" -ForegroundColor Green
Write-Host "ssh ${NasUser}@${NasHost} 'cd ${NasPath} && docker compose ps'" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Update process complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

