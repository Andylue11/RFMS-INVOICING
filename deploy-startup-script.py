#!/usr/bin/env python3
"""Deploy startup script to NAS and install it"""

import paramiko
import base64
import sys
import os

NAS_HOST_IP = "192.168.0.201"
NAS_USER = "atoz"
NAS_PASSWORD = "SimVek22$$22"
NAS_PATH = "/volume1/docker/rfms-uploader"
STARTUP_SCRIPT = "/usr/local/etc/rc.d/S99rfms-uploader.sh"

def deploy_and_install():
    """Deploy startup script and install it"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {NAS_USER}@{NAS_HOST_IP}...")
        ssh.connect(NAS_HOST_IP, username=NAS_USER, password=NAS_PASSWORD, timeout=30)
        print("Connected successfully")
        
        # Read and deploy synology-startup.sh
        print("Deploying synology-startup.sh...")
        with open('synology-startup.sh', 'rb') as f:
            content = f.read()
        data = base64.b64encode(content).decode('utf-8')
        escaped = data.replace("'", "'\\''")
        cmd = f"cd {NAS_PATH} && echo '{escaped}' | base64 -d > synology-startup.sh && chmod +x synology-startup.sh"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("[OK] synology-startup.sh deployed")
        else:
            error = stderr.read().decode()
            print(f"[ERROR] Failed to deploy: {error}")
            return False
        
        # Create logs directory if it doesn't exist
        print("Ensuring logs directory exists...")
        cmd = f"mkdir -p {NAS_PATH}/logs"
        ssh.exec_command(cmd)
        
        # Install the startup script (requires sudo)
        print("Installing startup script (requires root access)...")
        print("Note: You may need to run the installation manually via SSH")
        
        # Try to install via sudo
        install_cmd = f"""
        if [ ! -d /usr/local/etc/rc.d ]; then
            sudo mkdir -p /usr/local/etc/rc.d
        fi
        sudo cp {NAS_PATH}/synology-startup.sh {STARTUP_SCRIPT}
        sudo chmod +x {STARTUP_SCRIPT}
        echo "INSTALLED"
        """
        
        stdin, stdout, stderr = ssh.exec_command(install_cmd)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        if "INSTALLED" in output:
            print("[OK] Startup script installed successfully")
            print(f"Location: {STARTUP_SCRIPT}")
        else:
            print("[WARNING] Installation may require manual steps")
            print("Please SSH into the NAS and run:")
            print(f"  sudo bash {NAS_PATH}/install-startup-script.sh")
            print("Or manually:")
            print(f"  sudo cp {NAS_PATH}/synology-startup.sh {STARTUP_SCRIPT}")
            print(f"  sudo chmod +x {STARTUP_SCRIPT}")
        
        # Also deploy install script
        print("Deploying install-startup-script.sh...")
        with open('install-startup-script.sh', 'rb') as f:
            content = f.read()
        data = base64.b64encode(content).decode('utf-8')
        escaped = data.replace("'", "'\\''")
        cmd = f"cd {NAS_PATH} && echo '{escaped}' | base64 -d > install-startup-script.sh && chmod +x install-startup-script.sh"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("[OK] install-startup-script.sh deployed")
        
        print("")
        print("==========================================")
        print("Deployment Complete!")
        print("==========================================")
        print("")
        print("Next steps:")
        print("1. SSH into the NAS: ssh atoz@192.168.0.201")
        print(f"2. Run: sudo bash {NAS_PATH}/install-startup-script.sh")
        print("3. Test: sudo /usr/local/etc/rc.d/S99rfms-uploader.sh")
        print("")
        print("The script will automatically start containers on boot.")
        print("")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        ssh.close()

if __name__ == "__main__":
    success = deploy_and_install()
    sys.exit(0 if success else 1)




