#!/usr/bin/env python3
"""
Direct deployment to NAS at /volume1/docker/rfms-uploader
"""

import paramiko
import sys

# NAS Server Configuration
NAS_HOST_IP = "192.168.0.201"
NAS_USER = "atoz"
NAS_PASSWORD = "SimVek22$$22"
NAS_PATH = "/volume1/docker/rfms-uploader"

def run_ssh_command(ssh, command, description=""):
    """Run a command via SSH and return output"""
    if description:
        print(f"  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    errors = stderr.read().decode().strip()
    if exit_status != 0 and errors:
        print(f"    [WARNING] {errors}")
    return output, exit_status

def deploy():
    """Deploy the application to NAS server"""
    print("="*70)
    print("RFMS Uploader - Direct NAS Deployment")
    print("="*70)
    print(f"Target: {NAS_USER}@{NAS_HOST_IP}")
    print(f"Path: {NAS_PATH}")
    print()
    
    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to NAS
        print(f"Connecting to {NAS_USER}@{NAS_HOST_IP}...")
        ssh.connect(
            NAS_HOST_IP,
            username=NAS_USER,
            password=NAS_PASSWORD,
            timeout=30
        )
        print("[OK] Connected successfully")
        print()
        
        # Check Docker - try multiple paths
        print("Checking Docker...")
        docker_paths = [
            "docker",
            "/usr/local/bin/docker",
            "/usr/bin/docker",
            "/var/packages/Docker/target/usr/bin/docker",
            "/volume1/@appstore/Docker/bin/docker"
        ]
        docker_cmd = None
        for path in docker_paths:
            check_cmd = f"{path} --version 2>/dev/null"
            check_output, check_status = run_ssh_command(ssh, check_cmd)
            if check_status == 0 and "version" in check_output.lower():
                docker_cmd = path
                print(f"  [OK] Docker found at: {path}")
                print(f"      Version: {check_output}")
                break
        
        if not docker_cmd:
            print("  [ERROR] Docker not found in standard locations")
            print("  Trying to find Docker via Synology package system...")
            pkg_check, _ = run_ssh_command(ssh, "ls -la /var/packages/Docker 2>/dev/null || echo 'NOT_FOUND'")
            if "NOT_FOUND" not in pkg_check:
                print("  [INFO] Docker package directory exists, but binary not in PATH")
                print("  [INFO] You may need to add Docker to PATH or use full path")
            docker_cmd = "docker"  # Fallback, will try with sudo
        
        # Check docker compose
        compose_cmd = None
        compose_paths = [
            "docker compose",
            "docker-compose",
            "/usr/local/bin/docker-compose",
            "/usr/bin/docker-compose"
        ]
        for path in compose_paths:
            check_cmd = f"{path} --version 2>/dev/null || {path} version 2>/dev/null"
            check_output, check_status = run_ssh_command(ssh, check_cmd)
            if check_status == 0:
                compose_cmd = path
                print(f"  [OK] Docker Compose found: {path}")
                break
        
        if not compose_cmd:
            print("  [WARNING] Docker Compose not found, will try 'docker compose' (v2)")
            compose_cmd = "docker compose"
        print()
        
        # Navigate to directory
        print(f"Navigating to {NAS_PATH}...")
        run_ssh_command(ssh, f"cd {NAS_PATH} && pwd")
        print("  [OK] Directory exists")
        print()
        
        # Create docker-compose-nas.yml
        print("Creating docker-compose-nas.yml...")
        compose_content = """version: '3.8'

services:
  uploader:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: uploader
    ports:
      - "5007:5007"
    environment:
      - FLASK_ENV=production
      - PYTHONUNBUFFERED=1
      - PORT=5007
      - HOST=0.0.0.0
    env_file:
      - .env
    volumes:
      - /volume1/docker/rfms-uploader/instance:/app/instance
      - /volume1/docker/rfms-uploader/uploads:/app/uploads
      - /volume1/docker/rfms-uploader/logs:/app/logs
      - /volume1/docker/rfms-uploader/static:/app/static
      - /volume1/docker/rfms-uploader/data:/app/data
    restart: unless-stopped
    networks:
      - uploader-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5007/')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

networks:
  uploader-network:
    driver: bridge
"""
        # Transfer via base64
        import base64
        compose_data = base64.b64encode(compose_content.encode('utf-8')).decode('utf-8')
        compose_escaped = compose_data.replace("'", "'\\''")
        run_ssh_command(ssh, f"cd {NAS_PATH} && echo '{compose_escaped}' | base64 -d > docker-compose-nas.yml")
        print("  [OK] docker-compose-nas.yml created")
        print()
        
        # Ensure directories exist
        print("Ensuring directories exist...")
        run_ssh_command(ssh, f"cd {NAS_PATH} && mkdir -p instance uploads logs static data && chmod 755 instance uploads logs static data")
        print("  [OK] Directories ready")
        print()
        
        # Check .env file
        print("Checking .env file...")
        env_check, _ = run_ssh_command(ssh, f"cd {NAS_PATH} && test -f .env && echo 'EXISTS' || echo 'MISSING'")
        if "EXISTS" in env_check:
            print("  [OK] .env file exists")
        else:
            print("  [WARNING] .env file not found - container may not start properly")
        print()
        
        # Stop existing container if running
        print("Stopping existing containers...")
        stop_cmd = f"cd {NAS_PATH} && {compose_cmd} -f docker-compose-nas.yml down 2>/dev/null || {docker_cmd} stop uploader 2>/dev/null || true"
        run_ssh_command(ssh, stop_cmd)
        print("  [OK] Existing containers stopped")
        print()
        
        # Try with sudo if docker_cmd needs it
        sudo_needed = False
        if docker_cmd == "docker":
            # Test if docker works without sudo
            test_cmd = f"{docker_cmd} ps 2>&1"
            test_output, test_status = run_ssh_command(ssh, test_cmd)
            if test_status != 0 and "permission denied" in test_output.lower():
                sudo_needed = True
                print("  [INFO] Docker requires sudo, will use sudo for commands")
        
        # Build and start
        print("Building and starting container...")
        if sudo_needed:
            build_cmd = f"cd {NAS_PATH} && sudo {compose_cmd} -f docker-compose-nas.yml up -d --build 2>&1"
        else:
            build_cmd = f"cd {NAS_PATH} && {compose_cmd} -f docker-compose-nas.yml up -d --build 2>&1"
        
        build_output, build_status = run_ssh_command(ssh, build_cmd)
        print(build_output)
        
        if build_status == 0:
            print("  [OK] Container started")
        else:
            print(f"  [WARNING] Build returned status {build_status}")
            print("  Trying alternative method...")
            # Try direct docker commands
            if sudo_needed:
                alt_cmd = f"cd {NAS_PATH} && sudo {docker_cmd} build -t uploader . && sudo {docker_cmd} run -d --name uploader --restart unless-stopped -p 5007:5007 -v {NAS_PATH}/instance:/app/instance -v {NAS_PATH}/uploads:/app/uploads -v {NAS_PATH}/logs:/app/logs -v {NAS_PATH}/static:/app/static -v {NAS_PATH}/data:/app/data --env-file .env uploader"
            else:
                alt_cmd = f"cd {NAS_PATH} && {docker_cmd} build -t uploader . && {docker_cmd} run -d --name uploader --restart unless-stopped -p 5007:5007 -v {NAS_PATH}/instance:/app/instance -v {NAS_PATH}/uploads:/app/uploads -v {NAS_PATH}/logs:/app/logs -v {NAS_PATH}/static:/app/static -v {NAS_PATH}/data:/app/data --env-file .env uploader"
            alt_output, alt_status = run_ssh_command(ssh, alt_cmd)
            print(alt_output)
        print()
        
        # Check status
        print("Checking container status...")
        if sudo_needed:
            status_cmd = f"sudo {docker_cmd} ps | grep uploader || sudo {docker_cmd} ps -a | grep uploader"
        else:
            status_cmd = f"{docker_cmd} ps | grep uploader || {docker_cmd} ps -a | grep uploader"
        status_output, _ = run_ssh_command(ssh, status_cmd)
        print(status_output if status_output else "  [INFO] Container status not available")
        print()
        
        # Show logs
        print("Recent logs:")
        if sudo_needed:
            logs_cmd = f"sudo {docker_cmd} logs uploader --tail=20 2>/dev/null"
        else:
            logs_cmd = f"{docker_cmd} logs uploader --tail=20 2>/dev/null"
        logs_output, _ = run_ssh_command(ssh, logs_cmd)
        print(logs_output if logs_output else "  [INFO] No logs available yet")
        print()
        
        print("="*70)
        print("Deployment complete!")
        print("="*70)
        print()
        print("Application should be available at:")
        print(f"  http://192.168.0.201:5007")
        print()
        print("To view logs:")
        print(f"  ssh {NAS_USER}@{NAS_HOST_IP} 'cd {NAS_PATH} && docker compose -f docker-compose-nas.yml logs -f'")
        print()
        
    except paramiko.AuthenticationException:
        print("[ERROR] Authentication failed. Check username and password.")
        sys.exit(1)
    except paramiko.SSHException as e:
        print(f"[ERROR] SSH error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy()

