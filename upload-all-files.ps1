# PDF Extractor Upload Script for Synology NAS (PowerShell)
# This script uploads all files to the Synology NAS

Write-Host "==========================================" -ForegroundColor Green
Write-Host "PDF Extractor NAS Upload" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# Configuration
$NAS_USER = "atoz"
$NAS_IP = "192.168.0.201"
$NAS_PATH = "/volume1/docker/pdf-extractor"

Write-Host "Uploading to: $NAS_USER@$NAS_IP" -ForegroundColor Yellow
Write-Host "Target path: $NAS_PATH" -ForegroundColor Yellow
Write-Host ""
Write-Host "NOTE: You will be prompted for the password for each file upload." -ForegroundColor Cyan
Write-Host "This is normal behavior for SCP." -ForegroundColor Cyan
Write-Host ""

# Function to upload file with error handling
function Upload-File {
    param($LocalFile, $RemotePath)
    
    Write-Host "Uploading: $LocalFile" -ForegroundColor Blue
    $result = scp -o StrictHostKeyChecking=no $LocalFile "${NAS_USER}@${NAS_IP}:${RemotePath}"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully uploaded: $LocalFile" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to upload: $LocalFile" -ForegroundColor Red
    }
}

# Function to upload directory with error handling
function Upload-Directory {
    param($LocalDir, $RemotePath)
    
    Write-Host "Uploading directory: $LocalDir" -ForegroundColor Blue
    $result = scp -r -o StrictHostKeyChecking=no $LocalDir "${NAS_USER}@${NAS_IP}:${RemotePath}"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully uploaded directory: $LocalDir" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to upload directory: $LocalDir" -ForegroundColor Red
    }
}

# Upload main application files
Write-Host "📄 Uploading main application files..." -ForegroundColor Magenta
Upload-File "app.py" $NAS_PATH
Upload-File "models.py" $NAS_PATH
Upload-File "requirements.txt" $NAS_PATH
Upload-File "app_production.py" $NAS_PATH

# Upload directories
Write-Host "📁 Uploading directories..." -ForegroundColor Magenta
Upload-Directory "utils" $NAS_PATH
Upload-Directory "templates" $NAS_PATH
Upload-Directory "static" $NAS_PATH

# Upload Synology scripts
Write-Host "🐧 Uploading Synology management scripts..." -ForegroundColor Magenta
$scripts = @(
    "quick-setup-synology.sh",
    "auto-setup-synology.sh", 
    "manage-synology.sh",
    "configure-synology.sh",
    "troubleshoot-synology.sh",
    "security-harden-synology.sh",
    "optimize-performance-synology.sh",
    "backup-synology.sh",
    "disaster-recovery-synology.sh",
    "monitor-synology.sh",
    "maintenance-synology.sh",
    "migrate-synology.sh",
    "master-control-synology.sh",
    "health-check-synology.sh",
    "update-synology.sh"
)

foreach ($script in $scripts) {
    if (Test-Path $script) {
        Upload-File $script $NAS_PATH
    }
}

# Upload Docker files
Write-Host "🐳 Uploading Docker configuration files..." -ForegroundColor Magenta
Upload-File "Dockerfile" $NAS_PATH
Upload-File "Dockerfile-synology" $NAS_PATH
Upload-File "docker-compose.yml" $NAS_PATH
Upload-File "docker-compose-synology.yml" $NAS_PATH

# Upload other important files
Write-Host "📋 Uploading other important files..." -ForegroundColor Magenta
Upload-File "deploy-synology.sh" $NAS_PATH
Upload-File "SYNOLOGY_DEPLOYMENT_GUIDE.md" $NAS_PATH
Upload-File "README.md" $NAS_PATH

# Set permissions
Write-Host ""
Write-Host "🔐 Setting permissions on NAS..." -ForegroundColor Magenta
ssh -o StrictHostKeyChecking=no "${NAS_USER}@${NAS_IP}" "cd $NAS_PATH && sudo chown -R $NAS_USER:users . && sudo chmod -R 755 . && sudo chmod +x *.sh"

# Create directories
Write-Host "📁 Creating necessary directories on NAS..." -ForegroundColor Magenta
ssh -o StrictHostKeyChecking=no "${NAS_USER}@${NAS_IP}" "cd $NAS_PATH && sudo mkdir -p instance uploads logs static && sudo chown -R $NAS_USER:users instance uploads logs static && sudo chmod -R 755 instance uploads logs static"

# Verify upload
Write-Host ""
Write-Host "🔍 Verifying upload..." -ForegroundColor Magenta
ssh -o StrictHostKeyChecking=no "${NAS_USER}@${NAS_IP}" "cd $NAS_PATH && echo 'Files uploaded:' && ls -la"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Upload completed successfully!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. SSH into your NAS: ssh $NAS_USER@$NAS_IP" -ForegroundColor White
Write-Host "2. Navigate to: cd $NAS_PATH" -ForegroundColor White
Write-Host "3. Run quick setup: ./quick-setup-synology.sh" -ForegroundColor White
Write-Host "4. Or run master control: ./master-control-synology.sh" -ForegroundColor White
Write-Host ""
Write-Host "Your application will be available at:" -ForegroundColor Yellow
Write-Host "   http://$NAS_IP:5000" -ForegroundColor White
Write-Host ""
Write-Host "Management commands:" -ForegroundColor Yellow
Write-Host "   View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   Restart: docker-compose restart" -ForegroundColor White
Write-Host "   Stop: docker-compose down" -ForegroundColor White
Write-Host "   Start: docker-compose up -d" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

