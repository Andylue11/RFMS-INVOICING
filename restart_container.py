#!/usr/bin/env python3
"""Restart the container on NAS"""

import paramiko
import sys

NAS_HOST_IP = "192.168.0.201"
NAS_USER = "atoz"
NAS_PASSWORD = "SimVek22$$22"
NAS_PATH = "/volume1/docker/rfms-uploader"

def restart_container():
    """Restart the container"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {NAS_USER}@{NAS_HOST_IP}...")
        ssh.connect(NAS_HOST_IP, username=NAS_USER, password=NAS_PASSWORD, timeout=30)
        print("Connected successfully")
        
        print("Restarting container...")
        cmd = f"cd {NAS_PATH} && /usr/local/bin/docker-compose -f docker-compose-nas.yml restart uploader"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        if exit_status == 0:
            print("[OK] Container restarted successfully")
            if output:
                print(output)
            return True
        else:
            print(f"[ERROR] Restart failed: {errors}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False
    finally:
        ssh.close()

if __name__ == "__main__":
    success = restart_container()
    sys.exit(0 if success else 1)




