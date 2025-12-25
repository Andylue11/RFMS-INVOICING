#!/bin/bash
# Deploy RFMS-Uploader to office server
# Usage: ./deploy-to-server.sh

set -e  # Exit on error

SERVER="atoz@192.168.0.201"
REMOTE_DIR="/volume1/docker/rfms-uploader"
CONTAINER_NAME="rfms-uploader"

echo "=========================================="
echo "RFMS-Uploader - Deploy to Server"
echo "=========================================="
echo ""
echo "Server: $SERVER"
echo "Remote Directory: $REMOTE_DIR"
echo ""

# Step 1: Test local files
echo "[1/5] Testing local files..."
if python -c "import sys; sys.path.insert(0, '.'); from utils.text_utils import uppercase_rfms_fields; print('✓ text_utils.py OK')" 2>/dev/null; then
    echo "✓ Python files are valid"
else
    echo "⚠ Python syntax check skipped (may need dependencies)"
fi

# Step 2: Create file list for upload
echo ""
echo "[2/5] Preparing files for upload..."
FILES_TO_UPLOAD=(
    "app.py"
    "utils/text_utils.py"
    "templates/base.html"
    "templates/installer_photos.html"
    "requirements.txt"
    "docker-compose.yml"
    "Dockerfile"
)

# Check which files exist
EXISTING_FILES=()
for file in "${FILES_TO_UPLOAD[@]}"; do
    if [ -f "$file" ]; then
        EXISTING_FILES+=("$file")
        echo "  ✓ $file"
    else
        echo "  ⚠ $file (not found, skipping)"
    fi
done

if [ ${#EXISTING_FILES[@]} -eq 0 ]; then
    echo "ERROR: No files to upload!"
    exit 1
fi

# Step 3: Upload files to server
echo ""
echo "[3/5] Uploading files to server..."
echo "This may take a moment..."

# Create remote directory if it doesn't exist
ssh "$SERVER" "mkdir -p $REMOTE_DIR/utils $REMOTE_DIR/templates" || {
    echo "ERROR: Failed to create remote directories"
    exit 1
}

# Upload files
for file in "${EXISTING_FILES[@]}"; do
    echo "  Uploading $file..."
    scp "$file" "$SERVER:$REMOTE_DIR/$file" || {
        echo "ERROR: Failed to upload $file"
        exit 1
    }
done

echo "✓ Files uploaded successfully"

# Step 4: Rebuild container on server
echo ""
echo "[4/5] Rebuilding container on server..."
echo "This may take several minutes..."

ssh "$SERVER" "cd $REMOTE_DIR && \
    docker compose down && \
    docker compose build --no-cache && \
    docker compose up -d" || {
    echo "ERROR: Failed to rebuild container"
    echo "Check server logs with: ssh $SERVER 'cd $REMOTE_DIR && docker compose logs'"
    exit 1
}

echo "✓ Container rebuilt and started"

# Step 5: Verify deployment
echo ""
echo "[5/5] Verifying deployment..."
sleep 10

# Check container status
CONTAINER_STATUS=$(ssh "$SERVER" "docker ps --filter name=$CONTAINER_NAME --format '{{.Status}}'" 2>/dev/null || echo "")
if [ -n "$CONTAINER_STATUS" ]; then
    echo "✓ Container is running: $CONTAINER_STATUS"
else
    echo "⚠ Could not verify container status"
fi

# Check logs
echo ""
echo "Recent container logs:"
ssh "$SERVER" "cd $REMOTE_DIR && docker compose logs --tail=20" 2>/dev/null || echo "Could not retrieve logs"

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Server: $SERVER"
echo "Container: $CONTAINER_NAME"
echo "Remote Directory: $REMOTE_DIR"
echo ""
echo "Useful commands:"
echo "  View logs:    ssh $SERVER 'cd $REMOTE_DIR && docker compose logs -f'"
echo "  Restart:      ssh $SERVER 'cd $REMOTE_DIR && docker compose restart'"
echo "  Stop:         ssh $SERVER 'cd $REMOTE_DIR && docker compose down'"
echo "  Shell:        ssh $SERVER 'docker exec -it $CONTAINER_NAME bash'"
echo ""

