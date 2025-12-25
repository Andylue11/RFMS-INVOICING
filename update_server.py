#!/usr/bin/env python3
"""Update the server by pulling latest code and rebuilding container"""

import paramiko
import sys

NAS_HOST_IP = "192.168.0.201"
NAS_USER = "atoz"
NAS_PASSWORD = "SimVek22$$22"
NAS_PATH = "/volume1/docker/rfms-uploader"

def run_command(ssh, command, description=""):
    """Run a command via SSH and return output"""
    if description:
        print(f"{description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    errors = stderr.read().decode().strip()
    
    if output:
        print(output)
    if errors and exit_status != 0:
        print(f"[WARNING] {errors}")
    
    return output, exit_status

def update_server():
    """Update server by pulling code and rebuilding container"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("="*70)
        print("RFMS Uploader - Server Update")
        print("="*70)
        print(f"Connecting to {NAS_USER}@{NAS_HOST_IP}...")
        ssh.connect(NAS_HOST_IP, username=NAS_USER, password=NAS_PASSWORD, timeout=30)
        print("[OK] Connected successfully\n")
        
        # Step 1: Pull latest code from git
        print("[1/4] Pulling latest code from Git...")
        git_cmd = f"cd {NAS_PATH} && export HOME={NAS_PATH} && /bin/git pull origin main 2>&1 || echo 'Git pull completed'"
        output, status = run_command(ssh, git_cmd)
        if "Already up to date" in output or "up to date" in output:
            print("[OK] Code is already up to date")
        elif status == 0:
            print("[OK] Code updated successfully")
        else:
            print("[WARNING] Git pull had issues, but continuing...")
        print()
        
        # Step 2: Stop existing container
        print("[2/4] Stopping existing container...")
        stop_cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml down"
        run_command(ssh, stop_cmd)
        print("[OK] Container stopped\n")
        
        # Step 3: Rebuild the image
        print("[3/4] Rebuilding Docker image...")
        build_cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml build --no-cache"
        stdin, stdout, stderr = ssh.exec_command(build_cmd)
        
        # Stream build output
        print("Build output:")
        while True:
            line = stdout.readline()
            if not line:
                break
            try:
                print(line.rstrip())
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
        
        exit_status = stdout.channel.recv_exit_status()
        errors = stderr.read().decode()
        
        if exit_status != 0:
            print(f"\n[ERROR] Build failed with status {exit_status}")
            if errors:
                print(f"Errors: {errors}")
            return False
        
        print("\n[OK] Image rebuilt successfully\n")
        
        # Step 4: Start the container
        print("[4/4] Starting container...")
        start_cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml up -d"
        output, status = run_command(ssh, start_cmd)
        
        if status == 0:
            print("[OK] Container started successfully\n")
            
            # Wait a moment and check status
            import time
            time.sleep(3)
            
            print("Container status:")
            status_cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml ps"
            run_command(ssh, status_cmd)
            print()
            
            print("="*70)
            print("✅ Update Complete!")
            print("="*70)
            print(f"Application should be available at: http://{NAS_HOST_IP}:5007")
            return True
        else:
            print(f"[ERROR] Failed to start container")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        ssh.close()

if __name__ == "__main__":
    success = update_server()
    sys.exit(0 if success else 1)


