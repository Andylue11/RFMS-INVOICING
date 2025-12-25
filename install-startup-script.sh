#!/bin/bash
#
# Install startup script on Synology NAS
# Run this script on the NAS to set up auto-start on boot
#

echo "=========================================="
echo "Installing RFMS Uploader Startup Script"
echo "=========================================="
echo ""

# Configuration
APP_DIR="/volume1/docker/rfms-uploader"
STARTUP_SCRIPT="/usr/local/etc/rc.d/S99rfms-uploader.sh"
SCRIPT_SOURCE="$APP_DIR/synology-startup.sh"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Check if source script exists
if [ ! -f "$SCRIPT_SOURCE" ]; then
    echo "ERROR: Source script not found: $SCRIPT_SOURCE"
    echo "Please ensure synology-startup.sh is in $APP_DIR"
    exit 1
fi

# Create rc.d directory if it doesn't exist
if [ ! -d "/usr/local/etc/rc.d" ]; then
    echo "Creating /usr/local/etc/rc.d directory..."
    mkdir -p /usr/local/etc/rc.d
fi

# Copy script to startup location
echo "Copying startup script..."
cp "$SCRIPT_SOURCE" "$STARTUP_SCRIPT"

# Make it executable
chmod +x "$STARTUP_SCRIPT"

echo ""
echo "Startup script installed successfully!"
echo ""
echo "Location: $STARTUP_SCRIPT"
echo ""
echo "The script will automatically run on system boot."
echo ""
echo "To test the script manually, run:"
echo "  sudo $STARTUP_SCRIPT"
echo ""
echo "To view logs:"
echo "  tail -f $APP_DIR/logs/startup.log"
echo ""
echo "To remove the startup script:"
echo "  sudo rm $STARTUP_SCRIPT"
echo ""




