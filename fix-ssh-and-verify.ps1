# Fix SSH key issue and verify update

$server = "atoz@AtozServer"
$path = "/volume1/docker/rfms-uploader"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Fixing SSH and Verifying Update" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Fix SSH known_hosts
Write-Host "Fixing GitHub SSH known_hosts..." -ForegroundColor Yellow
ssh $server "mkdir -p ~/.ssh; chmod 700 ~/.ssh; ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null; chmod 600 ~/.ssh/known_hosts"

# Check git status
Write-Host ""
Write-Host "Checking git status..." -ForegroundColor Yellow
ssh $server "cd $path; git status; echo ''; echo 'Last commit:'; git log -1 --oneline"

# Check if container needs to be updated
Write-Host ""
Write-Host "Checking container status..." -ForegroundColor Yellow
ssh $server "cd $path; docker compose ps"

Write-Host ""
Write-Host "If container is running but code is updated, rebuild:" -ForegroundColor Yellow
Write-Host "  ssh $server 'cd $path; docker compose down; docker compose build --no-cache; docker compose up -d'" -ForegroundColor Cyan

