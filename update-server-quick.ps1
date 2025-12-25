# Quick Server Update Script
# Run this from Windows PowerShell to update your NAS server
# This script works even if Git is not installed on the NAS

$NasUser = "atoz"
$NasHost = "192.168.0.201"
$NasPath = "/volume1/docker/pdf-extractor"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Updating PDF Extractor on NAS Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Git is available on NAS
Write-Host "[1/5] Checking Git availability on NAS..." -ForegroundColor Yellow
# Check for git in common locations (Synology has it at /bin/git)
$gitPath = ssh "${NasUser}@${NasHost}" "if [ -f /bin/git ]; then echo '/bin/git'; elif command -v git 2>/dev/null; then command -v git; else echo ''; fi"
$gitRepoExists = ssh "${NasUser}@${NasHost}" "cd ${NasPath} && test -d .git && echo 'yes' || echo 'no'"

if ($gitPath -and ($gitRepoExists -eq "yes")) {
    Write-Host "      Using Git to update files..." -ForegroundColor Green
    Write-Host "[2/5] Pulling latest code from Git..." -ForegroundColor Yellow
    # Use the full path to git (e.g., /bin/git) with HOME set to app directory
    ssh "${NasUser}@${NasHost}" "cd ${NasPath} && export HOME=${NasPath} && $gitPath pull origin main"
    $updateStep = 3
} else {
    Write-Host "      Git not available. Uploading files via SCP..." -ForegroundColor Yellow
    Write-Host "[2/5] Uploading application files..." -ForegroundColor Yellow
    
    # Upload key files
    $filesToUpload = @(
        "app.py",
        "models.py",
        "requirements.txt",
        "app_production.py",
        "Dockerfile",
        "docker-compose.yml"
    )
    
    foreach ($file in $filesToUpload) {
        if (Test-Path $file) {
            Write-Host "      Uploading $file..." -ForegroundColor Gray
            scp -o StrictHostKeyChecking=no $file "${NasUser}@${NasHost}:${NasPath}/"
        }
    }
    
    # Upload directories
    $dirsToUpload = @("utils", "templates", "static")
    foreach ($dir in $dirsToUpload) {
        if (Test-Path $dir) {
            Write-Host "      Uploading $dir/..." -ForegroundColor Gray
            scp -r -o StrictHostKeyChecking=no $dir "${NasUser}@${NasHost}:${NasPath}/"
        }
    }
    
    $updateStep = 3
}

# Detect docker-compose command (Synology uses docker compose v2)
Write-Host "[$updateStep/5] Detecting Docker Compose..." -ForegroundColor Yellow
$dockerComposeCmd = ssh "${NasUser}@${NasHost}" "if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then echo 'docker compose'; elif command -v docker-compose >/dev/null 2>&1; then echo 'docker-compose'; elif [ -f /usr/local/bin/docker-compose ]; then echo '/usr/local/bin/docker-compose'; elif [ -f /usr/bin/docker-compose ]; then echo '/usr/bin/docker-compose'; else echo 'docker compose'; fi"

Write-Host "[$updateStep/5] Stopping container..." -ForegroundColor Yellow
ssh "${NasUser}@${NasHost}" "cd ${NasPath} && export HOME=${NasPath} && $dockerComposeCmd down"

Write-Host "[$($updateStep+1)/5] Rebuilding and starting container..." -ForegroundColor Yellow
ssh "${NasUser}@${NasHost}" "cd ${NasPath} && export HOME=${NasPath} && $dockerComposeCmd up -d --build"

Write-Host "[$($updateStep+2)/5] Checking status..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
ssh "${NasUser}@${NasHost}" "cd ${NasPath} && export HOME=${NasPath} && $dockerComposeCmd ps"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Update Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Application should be available at: http://${NasHost}:5005" -ForegroundColor Yellow
Write-Host ""
Write-Host "View logs: ssh ${NasUser}@${NasHost} 'cd ${NasPath} && $dockerComposeCmd logs -f'" -ForegroundColor Cyan

