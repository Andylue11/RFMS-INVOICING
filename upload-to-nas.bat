@echo off
REM PDF Extractor Upload Script for Synology NAS (Windows)
REM This script uploads all files to the Synology NAS

echo ==========================================
echo PDF Extractor NAS Upload
echo ==========================================

REM Configuration
set NAS_USER=atoz
set NAS_IP=192.168.0.201
set NAS_PATH=/volume1/docker/pdf-extractor

echo Uploading to: %NAS_USER%@%NAS_IP%
echo Target path: %NAS_PATH%

REM Check if SCP is available
where scp >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: SCP is not available. Please install OpenSSH client or use PuTTY.
    echo Download from: https://www.putty.org/
    pause
    exit /b 1
)

REM Test connection to NAS
echo.
echo Testing connection to NAS...
ssh -o ConnectTimeout=10 -o BatchMode=yes %NAS_USER%@%NAS_IP% "echo Connection successful" >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Cannot connect to NAS
    echo Please ensure:
    echo 1. SSH is enabled on your Synology NAS
    echo 2. The IP address is correct: %NAS_IP%
    echo 3. The username is correct: %NAS_USER%
    echo 4. You have SSH key authentication set up or will enter password
    pause
    exit /b 1
)
echo Connection to NAS successful

REM Create directory on NAS
echo.
echo Creating directory on NAS...
ssh %NAS_USER%@%NAS_IP% "sudo mkdir -p %NAS_PATH% && sudo chown -R %NAS_USER%:users %NAS_PATH%"

REM Upload application files
echo.
echo Uploading application files...

REM Upload main application files
echo   Uploading main application files...
scp app.py %NAS_USER%@%NAS_IP%:%NAS_PATH%/
scp models.py %NAS_USER%@%NAS_IP%:%NAS_PATH%/
scp requirements.txt %NAS_USER%@%NAS_IP%:%NAS_PATH%/

REM Upload utils directory
if exist utils (
    echo   Uploading utils directory...
    scp -r utils %NAS_USER%@%NAS_IP%:%NAS_PATH%/
)

REM Upload templates directory
if exist templates (
    echo   Uploading templates directory...
    scp -r templates %NAS_USER%@%NAS_IP%:%NAS_PATH%/
)

REM Upload static directory
if exist static (
    echo   Uploading static directory...
    scp -r static %NAS_USER%@%NAS_IP%:%NAS_PATH%/
)

REM Upload all Synology scripts
echo   Uploading Synology management scripts...
for %%f in (*-synology.sh) do (
    if exist "%%f" (
        echo     Uploading %%f...
        scp "%%f" %NAS_USER%@%NAS_IP%:%NAS_PATH%/
    )
)

REM Upload Docker files
echo   Uploading Docker configuration files...
for %%f in (Dockerfile* docker-compose*.yml) do (
    if exist "%%f" (
        echo     Uploading %%f...
        scp "%%f" %NAS_USER%@%NAS_IP%:%NAS_PATH%/
    )
)

REM Upload any other Python files
echo   Uploading Python files...
for %%f in (*.py) do (
    if exist "%%f" (
        echo     Uploading %%f...
        scp "%%f" %NAS_USER%@%NAS_IP%:%NAS_PATH%/
    )
)

REM Upload any configuration files
echo   Uploading configuration files...
for %%f in (*.conf *.env*) do (
    if exist "%%f" (
        echo     Uploading %%f...
        scp "%%f" %NAS_USER%@%NAS_IP%:%NAS_PATH%/
    )
)

REM Upload documentation
echo   Uploading documentation...
for %%f in (*.md README*) do (
    if exist "%%f" (
        echo     Uploading %%f...
        scp "%%f" %NAS_USER%@%NAS_IP%:%NAS_PATH%/
    )
)

REM Set proper permissions on NAS
echo.
echo Setting permissions on NAS...
ssh %NAS_USER%@%NAS_IP% "cd %NAS_PATH% && sudo chown -R %NAS_USER%:users . && sudo chmod -R 755 . && sudo chmod +x *.sh"

REM Create necessary directories on NAS
echo.
echo Creating necessary directories on NAS...
ssh %NAS_USER%@%NAS_IP% "cd %NAS_PATH% && sudo mkdir -p instance uploads logs static && sudo chown -R %NAS_USER%:users instance uploads logs static && sudo chmod -R 755 instance uploads logs static"

REM Verify upload
echo.
echo Verifying upload...
ssh %NAS_USER%@%NAS_IP% "cd %NAS_PATH% && echo 'Files uploaded:' && ls -la"

echo.
echo Upload completed successfully!
echo.
echo Next Steps:
echo 1. SSH into your NAS: ssh %NAS_USER%@%NAS_IP%
echo 2. Navigate to: cd %NAS_PATH%
echo 3. Run quick setup: ./quick-setup-synology.sh
echo 4. Or run master control: ./master-control-synology.sh
echo.
echo Your application will be available at:
echo    http://%NAS_IP%:5000
echo.
echo Management commands:
echo    View logs: docker-compose logs -f
echo    Restart: docker-compose restart
echo    Stop: docker-compose down
echo    Start: docker-compose up -d
echo.
echo ==========================================
echo Upload Complete!
echo ==========================================
pause

