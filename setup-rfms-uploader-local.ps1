# PowerShell script to set up rfms-uploader.local on Windows
# Run this script as Administrator

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setting up rfms-uploader.local" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Path to hosts file
$hostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
$entry = "192.168.0.201    rfms-uploader.local"

Write-Host "Step 1: Checking hosts file..." -ForegroundColor Yellow
Write-Host "Location: $hostsPath" -ForegroundColor Gray

# Check if entry already exists
$hostsContent = Get-Content $hostsPath -ErrorAction SilentlyContinue
if ($hostsContent -match "rfms-uploader\.local") {
    Write-Host "✓ Entry already exists in hosts file" -ForegroundColor Green
    Write-Host "  Current entry: $($hostsContent | Select-String 'rfms-uploader')" -ForegroundColor Gray
    
    $response = Read-Host "Do you want to update it? (y/n)"
    if ($response -ne 'y') {
        Write-Host "Skipping hosts file update" -ForegroundColor Yellow
    } else {
        # Remove old entry
        $hostsContent = $hostsContent | Where-Object { $_ -notmatch "rfms-uploader\.local" }
        # Add new entry
        $hostsContent += $entry
        # Backup old file
        Copy-Item $hostsPath "$hostsPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        # Write new content
        $hostsContent | Set-Content $hostsPath
        Write-Host "✓ Hosts file updated" -ForegroundColor Green
    }
} else {
    Write-Host "Adding entry to hosts file..." -ForegroundColor Yellow
    # Backup old file
    Copy-Item $hostsPath "$hostsPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')" -ErrorAction SilentlyContinue
    # Add new entry
    Add-Content -Path $hostsPath -Value "`n$entry" -Force
    Write-Host "✓ Entry added to hosts file" -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 2: Flushing DNS cache..." -ForegroundColor Yellow
ipconfig /flushdns | Out-Null
Write-Host "✓ DNS cache flushed" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Testing connection..." -ForegroundColor Yellow

# Test ping
Write-Host "Testing ping to rfms-uploader.local..." -ForegroundColor Gray
$pingResult = Test-Connection -ComputerName rfms-uploader.local -Count 1 -Quiet -ErrorAction SilentlyContinue

if ($pingResult) {
    Write-Host "✓ Ping successful!" -ForegroundColor Green
} else {
    Write-Host "⚠ Ping failed (this might be normal if ICMP is disabled)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Configure Synology Reverse Proxy (see SETUP-RFMS-UPLOADER-LOCAL.md)" -ForegroundColor White
Write-Host "2. Open browser and go to: http://rfms-uploader.local" -ForegroundColor White
Write-Host ""
Write-Host "If you're NOT using reverse proxy, use: http://rfms-uploader.local:5005" -ForegroundColor Cyan
Write-Host ""

# Test web connection
Write-Host "Testing web connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://rfms-uploader.local:5005" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "✓ Web server is accessible!" -ForegroundColor Green
    Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Gray
} catch {
    Write-Host "⚠ Could not connect to http://rfms-uploader.local:5005" -ForegroundColor Yellow
    Write-Host "  Make sure:" -ForegroundColor Gray
    Write-Host "    - Docker container is running" -ForegroundColor Gray
    Write-Host "    - Synology reverse proxy is configured (if using Method 1)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Done! You can now access the app at:" -ForegroundColor Green
Write-Host "  http://rfms-uploader.local" -ForegroundColor Cyan
Write-Host "  (or http://rfms-uploader.local:5005 if not using reverse proxy)" -ForegroundColor Cyan

