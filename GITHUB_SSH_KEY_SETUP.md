# GitHub SSH Key Setup Instructions

## Your SSH Public Key

Copy this entire key (it's one line):

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINzTAsLu0rczuJtW79kQtCukpBpX9OUe0028Ihp1gkEE rfms-uploader-server
```

## Steps to Add Key to GitHub

1. **Go to GitHub Settings:**
   - Visit: https://github.com/settings/keys
   - Or: Click your profile picture → Settings → SSH and GPG keys

2. **Add New SSH Key:**
   - Click "New SSH key" button
   - **Title:** `RFMS-Uploader Server` (or any descriptive name)
   - **Key type:** Authentication Key
   - **Key:** Paste the entire key above (starting with `ssh-ed25519`)

3. **Click "Add SSH key"**

## Copy Key to Server (if needed)

If you need to use this key on the office server, copy it there:

```bash
# Copy the public key to the server
scp ~/.ssh/id_ed25519_rfms_uploader.pub atoz@AtozServer:/tmp/

# Then SSH to server and add it
ssh atoz@AtozServer
mkdir -p ~/.ssh
cat /tmp/id_ed25519_rfms_uploader.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

## Update Git Remote on Server

After adding the key to GitHub, update the git remote on the server:

```bash
ssh atoz@AtozServer 'cd /volume1/docker/rfms-uploader && git remote set-url origin git@github.com:Andylue11/RFMS-UPLOADER.git'
```

## Test Connection

Test if the key works:

```bash
ssh -T git@github.com
```

You should see: "Hi Andylue11! You've successfully authenticated..."

## Alternative: Use Existing Key

If you already have an SSH key set up on the server, you can use that instead. Check for existing keys:

```bash
ssh atoz@AtozServer 'ls -la ~/.ssh/*.pub'
```

Then add that key to GitHub instead.

