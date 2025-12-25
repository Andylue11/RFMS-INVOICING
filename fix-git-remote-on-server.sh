#!/bin/bash
# Fix git remote URL on server to use SSH instead of HTTPS
# This avoids authentication issues when pulling

echo "=========================================="
echo "Fixing Git Remote URL on Server"
echo "=========================================="
echo ""

ssh atoz@AtozServer << 'ENDSSH'
cd /volume1/docker/rfms-uploader

echo "Current remote URL:"
git remote -v

echo ""
echo "Updating remote to use SSH..."
git remote set-url origin git@github.com:Andylue11/RFMS-UPLOADER.git

echo ""
echo "New remote URL:"
git remote -v

echo ""
echo "Testing connection..."
git fetch origin

echo ""
echo "✅ Git remote updated successfully!"
ENDSSH

