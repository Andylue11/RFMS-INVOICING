# Find Docker path on Synology server

$server = "atoz@AtozServer"

Write-Host "Finding Docker installation..." -ForegroundColor Cyan
Write-Host ""

$dockerPath = ssh $server "which docker || find /usr -name docker 2>/dev/null | head -1 || echo '/usr/local/bin/docker'"
$dockerComposePath = ssh $server "which docker-compose || which 'docker compose' || find /usr -name docker-compose 2>/dev/null | head -1 || echo 'docker compose'"

Write-Host "Docker path: $dockerPath" -ForegroundColor Yellow
Write-Host "Docker Compose: $dockerComposePath" -ForegroundColor Yellow
Write-Host ""

# Test if docker works
Write-Host "Testing Docker access..." -ForegroundColor Cyan
ssh $server "$dockerPath --version"
ssh $server "$dockerComposePath version"

