#!/usr/bin/env python3
"""Rebuild and restart the container (assumes files are already on server)"""

import paramiko
import sys
import time

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

def rebuild_server():
    """Rebuild and restart container"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("="*70)
        print("RFMS Uploader - Rebuild Container")
        print("="*70)
        print(f"Connecting to {NAS_USER}@{NAS_HOST_IP}...")
        ssh.connect(NAS_HOST_IP, username=NAS_USER, password=NAS_PASSWORD, timeout=30)
        print("[OK] Connected successfully\n")
        
        # Step 1: Stop existing container
        print("[1/4] Stopping existing container...")
        stop_cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml down"
        run_command(ssh, stop_cmd)
        print("[OK] Container stopped\n")
        
        # Step 2: Rebuild the image
        print("[2/4] Rebuilding Docker image...")
        print("(This may take a few minutes...)")
        build_cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml build --no-cache"
        stdin, stdout, stderr = ssh.exec_command(build_cmd)
        
        # Stream build output (show progress)
        print("Build progress:")
        line_count = 0
        while True:
            line = stdout.readline()
            if not line:
                break
            try:
                line_str = line.rstrip()
                # Show every 10th line and important lines
                if line_count % 10 == 0 or "Step" in line_str or "DONE" in line_str or "ERROR" in line_str or "Successfully" in line_str:
                    print(f"  {line_str[:100]}")
                line_count += 1
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
        
        # Step 3: Start the container
        print("[3/4] Starting container...")
        start_cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml up -d"
        output, status = run_command(ssh, start_cmd)
        
        if status == 0:
            print("[OK] Container started successfully\n")
            
            # Wait a moment and check status
            print("[4/4] Checking container status...")
            time.sleep(3)
            
            status_cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml ps"
            run_command(ssh, status_cmd)
            print()
            
            print("="*70)
            print("Rebuild Complete!")
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
    success = rebuild_server()
    sys.exit(0 if success else 1)

