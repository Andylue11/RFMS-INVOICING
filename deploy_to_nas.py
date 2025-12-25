#!/usr/bin/env python3
"""
Deploy RFMS-Uploader App to NAS Server with Docker
Deploys to atoz@AtozServer.local (or 192.168.0.201) and sets up uploader.atozflooringsolutions.com.au domain
"""

import os
import sys
import paramiko
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# NAS Server Configuration
NAS_HOST = "AtozServer.local"  # Can also use 192.168.0.201
NAS_HOST_IP = "192.168.0.201"  # Fallback IP
NAS_USER = "atoz"
NAS_PASSWORD = "SimVek22$$22"
DOMAIN = "uploader.atozflooringsolutions.com.au"
APP_PORT = 5007
# Use home directory - will be determined dynamically
REMOTE_DIR_BASE = "rfms-uploader"
REPO_DIR = Path(__file__).parent

def run_ssh_command(ssh, command, description=""):
    """Run a command via SSH and return output"""
    if description:
        print(f"  {description}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    errors = stderr.read().decode().strip()
    if exit_status != 0 and errors:
        print(f"    [WARNING] Warning: {errors}")
    return output, exit_status

def deploy():
    """Deploy the application to NAS server"""
    print("="*70)
    print("RFMS-Uploader - NAS Deployment")
    print("="*70)
    print(f"Target: {NAS_USER}@{NAS_HOST} (or {NAS_HOST_IP})")
    print(f"Domain: {DOMAIN}")
    print(f"Port: {APP_PORT}")
    print()
    
    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Try connecting to NAS (try hostname first, then IP)
        print(f"Connecting to {NAS_USER}@{NAS_HOST}...")
        try:
            ssh.connect(
                NAS_HOST,
                username=NAS_USER,
                password=NAS_PASSWORD,
                timeout=30
            )
        except Exception as e:
            print(f"  Failed to connect via hostname: {e}")
            print(f"  Trying IP address {NAS_HOST_IP}...")
            ssh.connect(
                NAS_HOST_IP,
                username=NAS_USER,
                password=NAS_PASSWORD,
                timeout=30
            )
            print(f"  [OK] Connected via IP address")
        print("[OK] Connected successfully")
        print()
        
        # Check if Docker is installed
        print("Checking Docker installation...")
        docker_check, _ = run_ssh_command(ssh, "which docker || command -v docker")
        docker_compose_check, _ = run_ssh_command(ssh, "which docker-compose || which docker || command -v docker-compose")
        
        if not docker_check:
            print("  [WARNING] Docker not found.")
            print("  This appears to be a Synology NAS.")
            print("  Please install Docker via Synology Package Center:")
            print("    1. Open Synology DSM (web interface)")
            print("    2. Go to Package Center")
            print("    3. Search for 'Docker' and install it")
            print("  DO NOT use the standard Docker install script - it doesn't work on Synology.")
        else:
            print("  [OK] Docker is installed")
        
        if not docker_compose_check:
            print("  [WARNING] Docker Compose not found.")
            print("  If Docker was installed via Package Center, Docker Compose may be included.")
            print("  Try: docker compose version")
            print("  If not available, install manually:")
            print("    sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose")
            print("    sudo chmod +x /usr/local/bin/docker-compose")
        else:
            print("  [OK] Docker Compose is installed")
        print()
        
        # Get home directory
        print("Determining home directory...")
        stdin, stdout, stderr = ssh.exec_command("echo $HOME")
        home_dir = stdout.read().decode().strip()
        if not home_dir:
            # Fallback to ~
            stdin, stdout, stderr = ssh.exec_command("cd ~ && pwd")
            home_dir = stdout.read().decode().strip()
        remote_dir = f"{home_dir}/{REMOTE_DIR_BASE}"
        print(f"  Home directory: {home_dir}")
        print(f"  App directory: {remote_dir}")
        
        # Create remote directory
        print(f"\nSetting up directory {remote_dir}...")
        run_ssh_command(ssh, f"mkdir -p {remote_dir}")
        # Verify directory exists and is writable
        verify_cmd = f"test -d {remote_dir} && test -w {remote_dir} && echo 'OK' || echo 'FAIL'"
        verify_output, _ = run_ssh_command(ssh, verify_cmd)
        if verify_output != "OK":
            print(f"  [ERROR] Directory {remote_dir} does not exist or is not writable")
            sys.exit(1)
        print("  [OK] Directory created and verified")
        print()
        
        # Use tar archive for reliable file transfer
        print("Creating deployment archive...")
        import tempfile
        import tarfile
        
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            tar_path = tmp_file.name
        
        # Create tar archive
        files_to_include = [
            "app.py",
            "models.py",
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            "templates",
            "static",
            "utils",
            "data",
        ]
        
        with tarfile.open(tar_path, "w:gz") as tar:
            for item in files_to_include:
                local_path = REPO_DIR / item
                if local_path.exists():
                    tar.add(str(local_path), arcname=item, recursive=local_path.is_dir())
                    print(f"  Added {item} to archive")
        
        print(f"  [OK] Archive created: {tar_path}")
        print()
        
        # Transfer archive via SFTP - try multiple paths
        print("Transferring archive to server...")
        sftp = ssh.open_sftp()
        
        # Try different paths that SFTP might be able to access
        remote_paths_to_try = [
            f"~/rfms-uploader/deploy.tar.gz",  # Relative to home
            f"rfms-uploader/deploy.tar.gz",     # Relative path
            f"deploy.tar.gz",                    # Current directory
            f"{home_dir}/rfms-uploader/deploy.tar.gz",  # Full path
        ]
        
        transferred = False
        remote_tar = None
        for remote_path in remote_paths_to_try:
            try:
                print(f"  Trying path: {remote_path}")
                sftp.put(tar_path, remote_path)
                remote_tar = remote_path
                print(f"  [OK] Archive transferred to {remote_path}")
                transferred = True
                break
            except Exception as e:
                print(f"    Failed: {e}")
                continue
        
        if not transferred:
            # Last resort: use base64 encoding to transfer via SSH command
            print("  Trying base64 transfer method...")
            import base64
            with open(tar_path, 'rb') as f:
                tar_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Split into chunks and transfer via echo
            chunk_size = 10000
            chunks = [tar_data[i:i+chunk_size] for i in range(0, len(tar_data), chunk_size)]
            remote_tar = f"{remote_dir}/deploy.tar.gz"
            run_ssh_command(ssh, f"rm -f {remote_tar} && touch {remote_tar}")
            
            for i, chunk in enumerate(chunks):
                # Escape special characters
                chunk_escaped = chunk.replace("'", "'\\''")
                run_ssh_command(ssh, f"echo '{chunk_escaped}' | base64 -d >> {remote_tar}")
            
            print("  [OK] Archive transferred via base64")
            transferred = True
        
        sftp.close()
        
        if not transferred:
            print("  [ERROR] Could not transfer archive")
            sys.exit(1)
        
        # Extract archive on server
        print("Extracting archive on server...")
        # Resolve the actual path
        if remote_tar.startswith("~"):
            remote_tar = remote_tar.replace("~", home_dir)
        extract_cmd = f"cd {remote_dir} && tar -xzf {remote_tar} && rm -f {remote_tar} && echo 'OK'"
        extract_output, _ = run_ssh_command(ssh, extract_cmd)
        if "OK" in extract_output:
            print("  [OK] Archive extracted")
        else:
            print(f"  [WARNING] Extraction output: {extract_output}")
        
        # Clean up local archive
        import os
        os.unlink(tar_path)
        print()
        
        # Copy .env file if it exists (using base64 method)
        print("Setting up environment file...")
        local_env = REPO_DIR / ".env"
        if local_env.exists():
            print("  Copying .env file...")
            import base64
            with open(local_env, 'rb') as f:
                env_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Transfer via SSH command
            env_escaped = env_data.replace("'", "'\\''")
            run_ssh_command(ssh, f"echo '{env_escaped}' | base64 -d > {remote_dir}/.env")
            print("  [OK] .env file copied")
        else:
            print("  [WARNING] .env file not found locally")
            print("  You'll need to create it on the server")
        print()
        
        # Create nginx configuration
        print("Creating nginx configuration...")
        nginx_config = f"""server {{
    listen 80;
    server_name {DOMAIN};

    location / {{
        proxy_pass http://localhost:{APP_PORT};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Increase body size for file uploads
        client_max_body_size 20M;
    }}
}}
"""
        nginx_config_path = f"{remote_dir}/nginx-{DOMAIN.replace('.', '-')}.conf"
        # Transfer via base64
        import base64
        nginx_data = base64.b64encode(nginx_config.encode('utf-8')).decode('utf-8')
        nginx_escaped = nginx_data.replace("'", "'\\''")
        run_ssh_command(ssh, f"echo '{nginx_escaped}' | base64 -d > {nginx_config_path}")
        print(f"  [OK] Nginx config created at {nginx_config_path}")
        print()
        
        # Create deployment script on server
        print("Creating deployment script on server...")
        deploy_script = f"""#!/bin/bash
set -e

cd {remote_dir}

# Use docker compose (v2) if available, fallback to docker-compose (v1)
DOCKER_COMPOSE="docker compose"
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not found. Please install Docker via Synology Package Center."
    exit 1
fi

# Check if docker compose works, otherwise try docker-compose
if ! $DOCKER_COMPOSE version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    if ! command -v docker-compose &> /dev/null; then
        echo "ERROR: Docker Compose not found. Trying to use docker compose..."
        DOCKER_COMPOSE="docker compose"
    fi
fi

echo "Using: $DOCKER_COMPOSE"
$DOCKER_COMPOSE version || echo "Warning: Could not verify docker compose version"

echo "Building Docker image..."
$DOCKER_COMPOSE build

echo "Stopping existing containers..."
$DOCKER_COMPOSE down || true

echo "Starting containers..."
$DOCKER_COMPOSE up -d

echo "Waiting for container to be healthy..."
sleep 5

echo "Checking container status..."
$DOCKER_COMPOSE ps

echo "Checking logs..."
$DOCKER_COMPOSE logs --tail=20

echo ""
echo "Deployment complete!"
echo "App should be available at: http://{DOMAIN} or http://{NAS_HOST}:{APP_PORT}"
"""
        deploy_script_path = f"{remote_dir}/deploy.sh"
        # Transfer via base64
        script_data = base64.b64encode(deploy_script.encode('utf-8')).decode('utf-8')
        script_escaped = script_data.replace("'", "'\\''")
        run_ssh_command(ssh, f"echo '{script_escaped}' | base64 -d > {deploy_script_path}")
        run_ssh_command(ssh, f"chmod +x {deploy_script_path}")
        print(f"  [OK] Deployment script created")
        print()
        
        # Instructions for nginx setup
        print("="*70)
        print("Deployment files copied successfully!")
        print("="*70)
        print()
        print("Next steps:")
        print()
        print("1. SSH into the server:")
        print(f"   ssh {NAS_USER}@{NAS_HOST}")
        print()
        print("2. Navigate to the app directory:")
        print(f"   cd {remote_dir}")
        print()
        print("3. Ensure .env file is configured with your credentials")
        print("   Make sure PORT=5007 is set in .env")
        print("   See DEPLOYMENT_SUMMARY.md for required environment variables")
        print()
        print("4. Install Docker via Synology Package Center (if not already installed):")
        print("   - Open Synology DSM web interface")
        print("   - Go to Package Center")
        print("   - Search for 'Docker' and install")
        print("   - DO NOT use the standard Docker install script")
        print()
        print("5. Run the deployment script:")
        print(f"   cd {remote_dir}")
        print(f"   sudo ./deploy.sh")
        print("   (Use sudo if you get permission errors)")
        print()
        print("6. Set up reverse proxy (choose one method):")
        print()
        print("   Option A - Synology Reverse Proxy (Recommended):")
        print("   - Open Synology DSM > Control Panel > Application Portal > Reverse Proxy")
        print("   - Create new rule:")
        print("     Source: HTTP, Hostname: {DOMAIN}, Port: 80")
        print("     Destination: HTTP, Hostname: localhost, Port: {APP_PORT}")
        print()
        print("   Option B - Manual Nginx:")
        print(f"   sudo cp {nginx_config_path} /etc/nginx/sites-available/{DOMAIN.replace('.', '-')}")
        print(f"   sudo ln -s /etc/nginx/sites-available/{DOMAIN.replace('.', '-')} /etc/nginx/sites-enabled/")
        print("   sudo nginx -t  # Test configuration")
        print("   sudo systemctl reload nginx")
        print()
        print("7. Configure DNS:")
        print(f"   Add A record: {DOMAIN} -> Your NAS public IP")
        print("   Or configure your router's DNS to point the subdomain to the NAS")
        print()
        print("8. Access the app at:")
        print(f"   http://{DOMAIN}")
        print(f"   http://{NAS_HOST} or http://{NAS_HOST_IP}:{APP_PORT}")
        print()
        print("For detailed Synology-specific instructions, see SYNOLOGY_DEPLOYMENT.md")
        print()
        print("="*70)
        
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
