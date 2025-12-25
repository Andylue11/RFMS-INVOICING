#!/usr/bin/env python3
"""Check container status, start it, and verify reverse proxy configuration"""

import paramiko
import sys

NAS_HOST_IP = "192.168.0.201"
NAS_USER = "atoz"
NAS_PASSWORD = "SimVek22$$22"
NAS_PATH = "/volume1/docker/rfms-uploader"
DOMAIN = "uploader.atozflooringsolutions.com.au"
PORT = 5007

def run_ssh_command(ssh, command, description=""):
    """Run a command via SSH and return output"""
    if description:
        print(f"  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    errors = stderr.read().decode('utf-8', errors='ignore')
    if exit_status != 0 and errors:
        print(f"    [WARNING] {errors}")
    return output, exit_status

def main():
    """Main function to check and fix everything"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("="*70)
        print("RFMS Uploader - Container Check and Start")
        print("="*70)
        print(f"Connecting to {NAS_USER}@{NAS_HOST_IP}...")
        ssh.connect(NAS_HOST_IP, username=NAS_USER, password=NAS_PASSWORD, timeout=30)
        print("[OK] Connected successfully")
        print()
        
        # Check Docker - try multiple paths
        print("Checking Docker...")
        docker_paths = ["/usr/local/bin/docker", "/usr/bin/docker", "docker"]
        docker_cmd = None
        for path in docker_paths:
            check_output, check_status = run_ssh_command(ssh, f"{path} --version 2>/dev/null")
            if check_status == 0:
                docker_cmd = path
                print(f"  [OK] Docker found: {path}")
                break
        
        if not docker_cmd:
            print("  [ERROR] Docker not found!")
            return False
        
        # Check docker-compose
        compose_paths = ["/usr/local/bin/docker-compose", "docker-compose", "docker compose"]
        compose_cmd = None
        for path in compose_paths:
            check_output, check_status = run_ssh_command(ssh, f"{path} --version 2>/dev/null || {path} version 2>/dev/null")
            if check_status == 0:
                compose_cmd = path
                print(f"  [OK] Docker Compose found: {path}")
                break
        
        if not compose_cmd:
            compose_cmd = "docker compose"  # Fallback
            print(f"  [INFO] Using: {compose_cmd}")
        print()
        
        # Check container status
        print("Checking container status...")
        status_cmd = f"cd {NAS_PATH} && {docker_cmd} ps -a | grep uploader || echo 'NOT_FOUND'"
        status_output, _ = run_ssh_command(ssh, status_cmd)
        
        if "NOT_FOUND" in status_output or not status_output.strip():
            print("  [WARNING] Container not found")
            print("  Starting container...")
        else:
            print(f"  Container status:")
            print(f"  {status_output}")
            
            # Check if running
            if "Up" in status_output:
                print("  [OK] Container is running")
            else:
                print("  [WARNING] Container exists but is not running")
        
        print()
        
        # Start/restart container
        print("Starting container...")
        start_cmd = f"cd {NAS_PATH} && {compose_cmd} -f docker-compose-nas.yml up -d 2>&1"
        start_output, start_status = run_ssh_command(ssh, start_cmd)
        print(start_output)
        
        if start_status == 0:
            print("  [OK] Container started")
        else:
            print("  [WARNING] Start command returned non-zero status")
        
        print()
        
        # Wait a moment for container to start
        import time
        print("Waiting for container to initialize...")
        time.sleep(5)
        
        # Check container status again
        print("Verifying container is running...")
        verify_cmd = f"{docker_cmd} ps | grep uploader || echo 'NOT_RUNNING'"
        verify_output, _ = run_ssh_command(ssh, verify_cmd)
        
        if "NOT_RUNNING" in verify_output:
            print("  [ERROR] Container is not running!")
            print("  Checking logs...")
            logs_cmd = f"cd {NAS_PATH} && {docker_cmd} logs uploader --tail=20 2>&1"
            logs_output, _ = run_ssh_command(ssh, logs_cmd)
            print(logs_output)
            return False
        else:
            print("  [OK] Container is running")
            print(f"  {verify_output}")
        
        print()
        
        # Check if port is accessible
        print(f"Testing port {PORT}...")
        port_test = f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{PORT} || echo 'FAILED'"
        port_output, _ = run_ssh_command(ssh, port_test)
        if "200" in port_output or "302" in port_output or "301" in port_output:
            print(f"  [OK] Port {PORT} is responding")
        else:
            print(f"  [WARNING] Port {PORT} test: {port_output}")
        
        print()
        
        # Check reverse proxy configuration
        print("Checking reverse proxy configuration...")
        print(f"  Domain: {DOMAIN}")
        print(f"  Should point to: localhost:{PORT}")
        print()
        print("  [INFO] Please verify in Synology DSM:")
        print("  1. Control Panel > Login Portal > Reverse Proxy")
        print(f"  2. Ensure rule exists for: {DOMAIN}")
        print(f"  3. Destination should be: localhost:{PORT}")
        print("  4. Rule should be enabled (green toggle)")
        print()
        
        # Check if nginx config exists
        nginx_check = f"test -f {NAS_PATH}/nginx-rfms-uploader.conf && echo 'EXISTS' || echo 'NOT_FOUND'"
        nginx_output, _ = run_ssh_command(ssh, nginx_check)
        if "EXISTS" in nginx_output:
            print("  [OK] nginx-rfms-uploader.conf exists")
            print("  [INFO] If using nginx, ensure config is in /etc/nginx/sites-enabled/")
        
        print()
        print("="*70)
        print("Summary")
        print("="*70)
        print(f"Container: {'Running' if 'NOT_RUNNING' not in verify_output else 'Not Running'}")
        print(f"Port {PORT}: {'Accessible' if '200' in port_output or '302' in port_output else 'Check manually'}")
        print(f"Domain: {DOMAIN}")
        print(f"Direct Access: http://{NAS_HOST_IP}:{PORT}")
        print(f"Domain Access: http://{DOMAIN} (requires reverse proxy)")
        print()
        print("To view logs:")
        print(f"  ssh {NAS_USER}@{NAS_HOST_IP} 'cd {NAS_PATH} && docker logs uploader -f'")
        print()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        ssh.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

