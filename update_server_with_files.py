#!/usr/bin/env python3
"""Update the server by uploading latest files and rebuilding container"""

import paramiko
import sys
import os
from pathlib import Path

NAS_HOST_IP = "192.168.0.201"
NAS_USER = "atoz"
NAS_PASSWORD = "SimVek22$$22"
NAS_PATH = "/volume1/docker/rfms-uploader"

# Files and directories to upload
FILES_TO_UPLOAD = [
    "app.py",
    "models.py",
    "requirements.txt",
    "app_production.py",
    "Dockerfile",
    "docker-compose-nas.yml",
]

DIRS_TO_UPLOAD = [
    "utils",
    "templates",
    "static",
]

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

def upload_file(sftp, local_path, remote_path):
    """Upload a single file"""
    try:
        sftp.put(local_path, remote_path)
        print(f"  [OK] Uploaded: {os.path.basename(local_path)}")
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to upload {os.path.basename(local_path)}: {e}")
        return False

def upload_directory(sftp, local_dir, remote_dir):
    """Upload a directory recursively"""
    try:
        # Create remote directory
        try:
            sftp.mkdir(remote_dir)
        except:
            pass  # Directory might already exist
        
        # Upload files in directory
        local_path = Path(local_dir)
        for item in local_path.iterdir():
            remote_path = f"{remote_dir}/{item.name}"
            if item.is_file():
                sftp.put(str(item), remote_path)
                print(f"    [OK] {item.name}")
            elif item.is_dir():
                upload_directory(sftp, str(item), remote_path)
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to upload directory {local_dir}: {e}")
        return False

def update_server():
    """Update server by uploading files and rebuilding container"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("="*70)
        print("RFMS Uploader - Server Update (with File Upload)")
        print("="*70)
        print(f"Connecting to {NAS_USER}@{NAS_HOST_IP}...")
        ssh.connect(NAS_HOST_IP, username=NAS_USER, password=NAS_PASSWORD, timeout=30)
        print("[OK] Connected successfully\n")
        
        # Step 1: Upload files
        print("[1/5] Uploading latest files...")
        sftp = ssh.open_sftp()
        
        # Upload individual files
        uploaded_count = 0
        for filename in FILES_TO_UPLOAD:
            if os.path.exists(filename):
                remote_path = f"{NAS_PATH}/{filename}"
                if upload_file(sftp, filename, remote_path):
                    uploaded_count += 1
            else:
                print(f"  [SKIP] File not found: {filename}")
        
        # Upload directories
        for dirname in DIRS_TO_UPLOAD:
            if os.path.exists(dirname) and os.path.isdir(dirname):
                remote_path = f"{NAS_PATH}/{dirname}"
                print(f"  Uploading directory: {dirname}/")
                if upload_directory(sftp, dirname, remote_path):
                    uploaded_count += 1
            else:
                print(f"  [SKIP] Directory not found: {dirname}")
        
        sftp.close()
        print(f"[OK] Uploaded {uploaded_count} items successfully\n")
        
        # Step 2: Stop existing container
        print("[2/5] Stopping existing container...")
        stop_cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml down"
        run_command(ssh, stop_cmd)
        print("[OK] Container stopped\n")
        
        # Step 3: Rebuild the image
        print("[3/5] Rebuilding Docker image...")
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
                # Show every 5th line and important lines
                if line_count % 5 == 0 or "Step" in line_str or "DONE" in line_str or "ERROR" in line_str:
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
        
        # Step 4: Start the container
        print("[4/5] Starting container...")
        start_cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml up -d"
        output, status = run_command(ssh, start_cmd)
        
        if status == 0:
            print("[OK] Container started successfully\n")
            
            # Wait a moment and check status
            import time
            time.sleep(3)
            
            print("[5/5] Container status:")
            status_cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml ps"
            run_command(ssh, status_cmd)
            print()
            
            print("="*70)
            print("Update Complete!")
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

