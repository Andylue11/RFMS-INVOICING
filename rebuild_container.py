#!/usr/bin/env python3
"""Rebuild and restart the container on NAS"""

import paramiko
import sys

NAS_HOST_IP = "192.168.0.201"
NAS_USER = "atoz"
NAS_PASSWORD = "SimVek22$$22"
NAS_PATH = "/volume1/docker/rfms-uploader"

def rebuild_container():
    """Rebuild and restart the container"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {NAS_USER}@{NAS_HOST_IP}...")
        ssh.connect(NAS_HOST_IP, username=NAS_USER, password=NAS_PASSWORD, timeout=30)
        print("Connected successfully")
        
        # Stop and remove existing container
        print("Stopping existing container...")
        cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml down"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        if output:
            print(output)
        
        # Rebuild the image
        print("Rebuilding Docker image...")
        cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml build --no-cache"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        
        # Stream output
        import sys
        import io
        while True:
            line = stdout.readline()
            if not line:
                break
            try:
                print(line.strip())
            except UnicodeEncodeError:
                # Skip lines with encoding issues
                pass
        
        errors = stderr.read().decode()
        if errors:
            print("Errors:", errors)
        
        if exit_status != 0:
            print(f"[ERROR] Build failed with status {exit_status}")
            return False
        
        print("[OK] Image rebuilt successfully")
        
        # Start the container
        print("Starting container...")
        cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml up -d"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        if exit_status == 0:
            print("[OK] Container started successfully")
            if output:
                print(output)
            return True
        else:
            print(f"[ERROR] Start failed: {errors}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        ssh.close()

if __name__ == "__main__":
    success = rebuild_container()
    sys.exit(0 if success else 1)

