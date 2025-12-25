@echo off
echo ==========================================
echo RFMS Uploader Status Check
echo ==========================================
echo.
echo Testing connection to NAS at 192.168.0.201:5005...
echo.

ping -n 1 192.168.0.201 >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ NAS is reachable
) else (
    echo ❌ NAS is not reachable
    exit /b 1
)

echo.
echo Attempting to connect to application...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://192.168.0.201:5005' -TimeoutSec 5; Write-Host '✅ Application is RUNNING! Status Code:' $response.StatusCode } catch { Write-Host '❌ Application is NOT responding' }"

echo.
echo ==========================================
echo.
echo If the application is not running, SSH into the NAS and run:
echo   cd /volume1/docker/pdf-extractor
echo   sudo docker ps
echo   sudo docker-compose up -d
echo.
pause


