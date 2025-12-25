#!/bin/bash
# Run Flask app locally on port 5008 for testing

echo "========================================"
echo "Starting RFMS Uploader - Local Testing"
echo "Port: 5008"
echo "========================================"
echo ""

# Set port environment variable
export PORT=5008

# Run the local script
python3 run_local.py

