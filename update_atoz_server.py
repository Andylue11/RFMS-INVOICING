#!/usr/bin/env python3
"""
Update atoz server using SSH with password authentication
"""
import sys
import paramiko
import time

# Server configuration
SERVER = "AtozServer"
USERNAME = "atoz"
PASSWORD = "SimVek22$$22"
REMOTE_DIR = "/volume1/docker/rfms-uploader"

def update_server():
    print("=" * 50)
    print("Updating RFMS-Uploader on Atoz Server")
    print("=" * 50)
    print()
    
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"[Connecting] Connecting to {USERNAME}@{SERVER}...")
        ssh.connect(SERVER, username=USERNAME, password=PASSWORD, timeout=10)
        print("[Connected] Successfully connected!")
        print()
        
        # First, detect which docker compose command works
        print("[Detecting] Checking docker compose command...")
        docker_compose_cmd = None
        
        # Try docker compose (newer version) first
        stdin, stdout, stderr = ssh.exec_command("docker compose version 2>&1")
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            docker_compose_cmd = "docker compose"
            print(f"[Detected] Using 'docker compose' (newer version)")
        else:
            # Try docker-compose (older version)
            stdin2, stdout2, stderr2 = ssh.exec_command("which docker-compose 2>&1")
            docker_compose_path = stdout2.read().decode().strip()
            if docker_compose_path and "not found" not in docker_compose_path:
                docker_compose_cmd = "docker-compose"
                print(f"[Detected] Using 'docker-compose' at {docker_compose_path}")
            else:
                # Try common installation paths
                for path in ["/usr/local/bin/docker-compose", "/usr/bin/docker-compose", "/opt/bin/docker-compose"]:
                    stdin3, stdout3, stderr3 = ssh.exec_command(f"test -f {path} && echo {path}")
                    if stdout3.read().decode().strip():
                        docker_compose_cmd = path
                        print(f"[Detected] Using '{docker_compose_cmd}'")
                        break
        
        if not docker_compose_cmd:
            print("[Error] Could not find docker-compose or docker compose command")
            ssh.close()
            return False
        print()
        
        # Commands to run
        commands = [
            f"cd {REMOTE_DIR}",
            "echo '[1/4] Pulling latest code from main...'",
            "git pull origin main",
            "echo ''",
            "echo '[2/4] Stopping container...'",
            f"{docker_compose_cmd} down",
            "echo ''",
            "echo '[3/4] Rebuilding container (this may take a few minutes)...'",
            f"{docker_compose_cmd} build --no-cache",
            "echo ''",
            "echo '[4/4] Starting container...'",
            f"{docker_compose_cmd} up -d",
            "echo ''",
            "echo 'Checking status...'",
            "sleep 5",
            f"{docker_compose_cmd} ps",
            "echo ''",
            "echo 'Recent logs:'",
            f"{docker_compose_cmd} logs --tail=30"
        ]
        
        # Execute commands
        full_command = " && ".join(commands)
        print("[Executing] Running update commands...")
        print()
        
        stdin, stdout, stderr = ssh.exec_command(full_command)
        
        # Print output in real-time
        for line in iter(stdout.readline, ""):
            if line:
                try:
                    # Try to decode and print, handling encoding issues
                    decoded_line = line.decode('utf-8', errors='replace').rstrip()
                    print(decoded_line)
                except:
                    # If decoding fails, try to print as-is or skip
                    try:
                        print(str(line).rstrip())
                    except:
                        pass
        
        # Check for errors
        try:
            error_output = stderr.read().decode('utf-8', errors='replace')
            if error_output:
                print("\n[Errors]", file=sys.stderr)
                print(error_output, file=sys.stderr)
        except:
            pass
        
        exit_status = stdout.channel.recv_exit_status()
        
        print()
        print("=" * 50)
        if exit_status == 0:
            print("Update Complete!")
        else:
            print(f"Update completed with exit status: {exit_status}")
        print("=" * 50)
        
        ssh.close()
        return exit_status == 0
        
    except paramiko.AuthenticationException:
        print(f"[Error] Authentication failed for {USERNAME}@{SERVER}")
        return False
    except paramiko.SSHException as e:
        print(f"[Error] SSH connection error: {e}")
        return False
    except Exception as e:
        print(f"[Error] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = update_server()
    sys.exit(0 if success else 1)

