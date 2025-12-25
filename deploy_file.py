#!/usr/bin/env python3
"""Deploy a single file to NAS"""

import paramiko
import base64
import sys
import os

NAS_HOST_IP = "192.168.0.201"
NAS_USER = "atoz"
NAS_PASSWORD = "SimVek22$$22"
NAS_PATH = "/volume1/docker/rfms-uploader"

def deploy_file(local_file, remote_path):
    """Deploy a file to NAS"""
    if not os.path.exists(local_file):
        print(f"Error: File {local_file} not found")
        return False
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {NAS_USER}@{NAS_HOST_IP}...")
        ssh.connect(NAS_HOST_IP, username=NAS_USER, password=NAS_PASSWORD, timeout=30)
        print("Connected successfully")
        
        # Read file content
        print(f"Reading {local_file}...")
        with open(local_file, 'rb') as f:
            content = f.read()
        
        # Encode to base64
        data = base64.b64encode(content).decode('utf-8')
        escaped = data.replace("'", "'\\''")
        
        # Create remote directory if needed
        remote_dir = os.path.dirname(remote_path)
        if remote_dir:
            ssh.exec_command(f"mkdir -p {NAS_PATH}/{remote_dir}")
        
        # Upload file
        print(f"Uploading to {NAS_PATH}/{remote_path}...")
        cmd = f"cd {NAS_PATH} && echo '{escaped}' | base64 -d > {remote_path}"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("[OK] File uploaded successfully")
            return True
        else:
            error = stderr.read().decode()
            print(f"[ERROR] Upload failed: {error}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False
    finally:
        ssh.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python deploy_file.py <local_file> [remote_path]")
        sys.exit(1)
    
    local_file = sys.argv[1]
    remote_path = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(local_file)
    
    success = deploy_file(local_file, remote_path)
    sys.exit(0 if success else 1)

