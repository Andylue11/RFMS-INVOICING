# Deploy RFMS-Uploader to office server
# Usage: .\deploy-to-server.ps1

$ErrorActionPreference = "Stop"

$server = "atoz@192.168.0.201"
$remoteDir = "/volume1/docker/rfms-uploader"
$containerName = "rfms-uploader"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "RFMS-Uploader - Deploy to Server" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server: $server"
Write-Host "Remote Directory: $remoteDir"
Write-Host ""

# Step 1: Test local files
Write-Host "[1/5] Testing local files..." -ForegroundColor Yellow
$filesToCheck = @(
    "app.py",
    "utils\text_utils.py",
    "templates\base.html",
    "templates\installer_photos.html",
    "requirements.txt",
    "docker-compose.yml",
    "Dockerfile"
)

$existingFiles = @()
foreach ($file in $filesToCheck) {
    if (Test-Path $file) {
        $existingFiles += $file
        Write-Host "  [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] $file (not found)" -ForegroundColor Yellow
    }
}

if ($existingFiles.Count -eq 0) {
    Write-Host "ERROR: No files to upload!" -ForegroundColor Red
    exit 1
}

# Step 2: Upload files to server
Write-Host ""
Write-Host "[2/5] Uploading files to server..." -ForegroundColor Yellow
Write-Host "This may take a moment..."

# Create remote directories
Write-Host "  Creating remote directories..." -ForegroundColor Gray
ssh -o LogLevel=ERROR $server "mkdir -p $remoteDir/utils $remoteDir/templates" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] Directory creation may have failed (continuing...)" -ForegroundColor Yellow
}

# Upload files (convert Windows paths to Unix paths)
foreach ($file in $existingFiles) {
    $unixPath = $file -replace '\\', '/'
    Write-Host "  Uploading $file..." -ForegroundColor Gray
    scp -o LogLevel=ERROR $file "${server}:${remoteDir}/${unixPath}" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to upload $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host "  [OK] Files uploaded successfully" -ForegroundColor Green

# Step 3: Rebuild container on server
Write-Host ""
Write-Host "[3/5] Rebuilding container on server..." -ForegroundColor Yellow
Write-Host "This may take several minutes..."

$rebuildCommand = @"
cd $remoteDir && \
docker compose down && \
docker compose build --no-cache && \
docker compose up -d
"@

Write-Host "  Executing rebuild commands..." -ForegroundColor Gray
ssh -o LogLevel=ERROR $server $rebuildCommand
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to rebuild container" -ForegroundColor Red
    Write-Host "Check server logs with: ssh $server 'cd $remoteDir && docker compose logs'" -ForegroundColor Yellow
    exit 1
}

Write-Host "  [OK] Container rebuilt and started" -ForegroundColor Green

# Step 4: Wait for container to start
Write-Host ""
Write-Host "[4/5] Waiting for container to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Step 5: Verify deployment
Write-Host ""
Write-Host "[5/5] Verifying deployment..." -ForegroundColor Yellow

# Check container status
$containerStatus = ssh $server "docker ps --filter name=$containerName --format '{{.Status}}'" 2>&1
if ($containerStatus -and $containerStatus -notmatch "error|Error") {
    Write-Host "  [OK] Container is running: $containerStatus" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Could not verify container status" -ForegroundColor Yellow
}

# Show recent logs
Write-Host ""
Write-Host "Recent container logs:" -ForegroundColor Cyan
ssh $server "cd $remoteDir && docker compose logs --tail=20" 2>&1

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server: $server"
Write-Host "Container: $containerName"
Write-Host "Remote Directory: $remoteDir"
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  View logs:    ssh $server 'cd $remoteDir && docker compose logs -f'"
Write-Host "  Restart:      ssh $server 'cd $remoteDir && docker compose restart'"
Write-Host "  Stop:         ssh $server 'cd $remoteDir && docker compose down'"
Write-Host "  Shell:        ssh $server 'docker exec -it $containerName bash'"
Write-Host ""

