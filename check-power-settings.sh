#!/bin/bash
#
# Check Synology NAS Power Recovery Settings
# This script checks if auto power-on is configured
#

echo "=========================================="
echo "Synology NAS Power Recovery Check"
echo "=========================================="
echo ""

# Check if running on Synology
if [ ! -f /etc/synoinfo.conf ]; then
    echo "WARNING: This doesn't appear to be a Synology NAS"
    echo ""
fi

# Try to check power recovery setting
echo "Checking power recovery settings..."
echo ""

# Method 1: Check via synosystemctl (if available)
if command -v synosystemctl > /dev/null 2>&1; then
    echo "Power Recovery Status:"
    synosystemctl --get-power-recovery 2>/dev/null || echo "  (Command not available or requires root)"
    echo ""
fi

# Method 2: Check configuration file
if [ -f /etc/synoinfo.conf ]; then
    echo "Synology Info:"
    grep -i "power" /etc/synoinfo.conf | head -5 || echo "  (No power settings found in config)"
    echo ""
fi

echo "=========================================="
echo "Manual Check Required"
echo "=========================================="
echo ""
echo "To enable auto power-on after power loss:"
echo ""
echo "1. Open Synology DSM web interface"
echo "2. Go to: Control Panel → Hardware & Power"
echo "3. Look for: 'Power Recovery' or 'Auto Power-On'"
echo "4. Enable: 'Automatically power on after a power failure'"
echo "5. Click Apply"
echo ""
echo "Note: Not all Synology models support this feature."
echo "If you don't see this option, your model may not support it."
echo ""
echo "For models that support it, the setting is usually in:"
echo "  Control Panel → Hardware & Power → Power Recovery"
echo ""




