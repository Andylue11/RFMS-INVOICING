@echo off
REM Run Flask app locally on port 5008 for testing
echo ========================================
echo Starting RFMS Uploader - Local Testing
echo Port: 5008
echo ========================================
echo.

REM Set port environment variable
set PORT=5008

REM Run the local script
python run_local.py

pause

