@echo off
REM Automated Setup Script for Synology NAS
REM This script copies files and runs setup automatically

echo ==========================================
echo Automated PDF Extractor Setup
echo ==========================================

set NAS_USER=atoz
set NAS_IP=192.168.0.201
set NAS_PASSWORD=SimVek22$$22
set NAS_PATH=/volume1/docker/pdf-extractor

echo Copying setup files to NAS...
echo SimVek22$$22 | plink -pw "SimVek22$$22" -batch %NAS_USER%@%NAS_IP% "mkdir -p %NAS_PATH%"
echo SimVek22$$22 | pscp -pw "SimVek22$$22" setup-now.sh %NAS_USER%@%NAS_IP%:%NAS_PATH%/
echo SimVek22$$22 | pscp -pw "SimVek22$$22" SETUP-GUIDE.md %NAS_USER%@%NAS_IP%:%NAS_PATH%/

echo.
echo Running setup on NAS...
echo SimVek22$$22 | plink -pw "SimVek22$$22" %NAS_USER%@%NAS_IP% "cd %NAS_PATH% && chmod +x setup-now.sh && bash setup-now.sh"

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo Your application should be available at:
echo http://%NAS_IP%:5000
echo.
pause
