# Synology NAS Auto Power-On After Power Loss

## Overview

Most Synology NAS devices can automatically turn themselves back on when AC power is restored. This is a **hardware/BIOS setting** that must be configured on the NAS itself.

## How to Configure Auto Power-On

### Method 1: Synology Control Panel (Recommended)

1. **Open Synology DSM** (web interface)
2. Go to **Control Panel** → **Hardware & Power**
3. Look for **"Power Recovery"** or **"Auto Power-On"** section
4. Enable **"Automatically power on the system after a power failure"**
5. Click **Apply**

### Method 2: Check BIOS/UEFI Settings (Advanced)

Some Synology models allow BIOS access:

1. **Access BIOS/UEFI:**
   - Connect a monitor and keyboard directly to the NAS
   - Boot the NAS and press the appropriate key (usually F2, Del, or F12) during startup
   - Look for **"AC Recovery"**, **"Power On After AC Loss"**, or **"Restore AC Power Loss"**
   - Set it to **"Power On"** or **"Always On"**
   - Save and exit

### Method 3: Check Model-Specific Settings

Different Synology models have different locations for this setting:

- **DSM 7.x**: Control Panel → Hardware & Power → Power Recovery
- **DSM 6.x**: Control Panel → Hardware & Power → Power
- **Some models**: May be in Control Panel → System → Power

## Verify Current Setting

To check if auto power-on is enabled:

1. **Via DSM:**
   - Control Panel → Hardware & Power → Power Recovery
   - Should show "Automatically power on after a power failure" as enabled

2. **Via SSH (if available):**
   ```bash
   # Check power settings
   synosystemctl --get-power-recovery
   ```

## Testing Auto Power-On

**⚠️ WARNING: Only test if you're comfortable with power cycling your NAS**

1. Ensure auto power-on is enabled in Control Panel
2. Safely shut down the NAS: Control Panel → Hardware & Power → Shut Down
3. Unplug the power cord
4. Wait 30 seconds
5. Plug the power cord back in
6. The NAS should automatically power on within a few seconds

## What Happens After Power Restoration

With auto power-on enabled:

1. **Power restored** → NAS automatically powers on
2. **NAS boots** → Synology DSM starts
3. **Docker service starts** → (if enabled in Package Center)
4. **Startup script runs** → `/usr/local/etc/rc.d/S99rfms-uploader.sh`
5. **Containers start** → Application becomes accessible

## Limitations

- **Not all models support this**: Some older Synology models may not have this feature
- **UPS recommended**: For critical systems, use a UPS (Uninterruptible Power Supply) to prevent power loss
- **Hardware dependent**: This is a BIOS/firmware feature, not software-controlled

## UPS Integration (Recommended)

For maximum reliability, use a UPS:

1. **Connect UPS to NAS** via USB
2. **Configure in DSM**: Control Panel → Hardware & Power → UPS
3. **Set shutdown time**: How long to wait on battery before shutting down
4. **Auto restart**: NAS will automatically power on when UPS power is restored

## Troubleshooting

### NAS Doesn't Auto Power-On

1. **Check Control Panel settings** - Ensure "Power Recovery" is enabled
2. **Check model compatibility** - Some older models don't support this
3. **Check BIOS settings** - If accessible, verify AC Recovery is enabled
4. **Contact Synology support** - They can confirm if your model supports this

### NAS Powers On But Containers Don't Start

This is handled by the startup script we installed:
- Check logs: `tail -f /volume1/docker/rfms-uploader/logs/startup.log`
- Manually start: `cd /volume1/docker/rfms-uploader && docker-compose -f docker-compose-nas.yml up -d`

## Summary

- ✅ **Auto power-on after AC loss**: Configure in Control Panel → Hardware & Power → Power Recovery
- ✅ **Auto-start containers**: Handled by startup script (`/usr/local/etc/rc.d/S99rfms-uploader.sh`)
- ✅ **Auto-restart containers**: Handled by Docker restart policy (`restart: unless-stopped`)

The combination of these three ensures your application is accessible as quickly as possible after power restoration.




