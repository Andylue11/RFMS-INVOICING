# Update Server Using Git

## Quick Update Commands

### Option 1: Single Command (Recommended)
```bash
ssh atoz@192.168.0.201 "cd /volume1/docker/rfms-uploader && git pull && docker compose down && docker compose build --no-cache && docker compose up -d"
```

### Option 2: Step by Step

1. **SSH into the server:**
   ```bash
   ssh atoz@192.168.0.201
   ```

2. **Navigate to the project directory:**
   ```bash
   cd /volume1/docker/rfms-uploader
   ```

3. **Pull latest changes from git:**
   ```bash
   git pull
   ```
   Or if you need to specify branch:
   ```bash
   git pull origin main
   # or
   git pull origin master
   ```

4. **Rebuild and restart the container:**
   ```bash
   docker compose down
   docker compose build --no-cache
   docker compose up -d
   ```

5. **Verify it's running:**
   ```bash
   docker compose ps
   docker compose logs --tail=50
   ```

## If Git Repository Doesn't Exist on Server

If the server doesn't have git initialized, you can set it up:

```bash
ssh atoz@192.168.0.201
cd /volume1/docker/rfms-uploader

# Initialize git (if not already done)
git init

# Add remote (replace with your actual repository URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Or if using SSH:
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git

# Pull the code
git pull origin main
```

## Troubleshooting

### If git pull fails with authentication:
- Make sure SSH keys are set up on the server
- Or use HTTPS with a personal access token

### If you need to commit local changes first:
```bash
cd /volume1/docker/rfms-uploader
git add .
git commit -m "Update from server"
git pull
```

### To see what branch you're on:
```bash
git branch
git status
```

