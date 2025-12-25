# Simple step-by-step update - Run each command separately if needed

$server = "atoz@AtozServer"
$path = "/volume1/docker/rfms-uploader"

Write-Host "Updating RFMS-Uploader..." -ForegroundColor Cyan
Write-Host ""

# Use semicolons to chain commands (avoids line ending issues)
$commands = @(
    "mkdir -p ~/.ssh; chmod 700 ~/.ssh; ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null; chmod 600 ~/.ssh/known_hosts",
    "cd $path; git remote set-url origin git@github.com:Andylue11/RFMS-UPLOADER.git",
    "cd $path; git fetch origin; git checkout main; git pull origin main",
    "cd $path; docker-compose down",
    "cd $path; docker-compose build --no-cache",
    "cd $path; docker-compose up -d",
    "cd $path; sleep 5; docker-compose ps; docker-compose logs --tail=20"
)

$step = 1
foreach ($cmd in $commands) {
    Write-Host "[$step/$($commands.Count)] Running command..." -ForegroundColor Yellow
    ssh $server $cmd
    if ($LASTEXITCODE -ne 0 -and $step -lt 3) {
        Write-Host "Warning: Command returned error code $LASTEXITCODE" -ForegroundColor Yellow
    }
    $step++
    Write-Host ""
}

Write-Host "Done!" -ForegroundColor Green

