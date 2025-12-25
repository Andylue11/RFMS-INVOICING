# Reverse Proxy Setup for uploader.atozflooringsolutions.com.au

## Current Configuration

- **Domain**: uploader.atozflooringsolutions.com.au
- **Container Port**: 5007
- **Direct Access**: http://192.168.0.201:5007
- **Domain Access**: http://uploader.atozflooringsolutions.com.au (requires reverse proxy)

## Synology Reverse Proxy Configuration

### Step 1: Access Synology DSM

1. Open web browser: http://192.168.0.201:5000
2. Log in with admin credentials

### Step 2: Configure Reverse Proxy

1. Go to **Control Panel** → **Login Portal** (or **Application Portal**)
2. Click the **Advanced** tab
3. Click **Reverse Proxy**

### Step 3: Create/Edit Reverse Proxy Rule

**If rule doesn't exist, click "Create"**
**If rule exists, select it and click "Edit"**

Configure as follows:

#### General Settings:
- **Reverse Proxy Name**: `uploader-atoz`
- **Description**: `RFMS Uploader Application`

#### Source (HTTP):
- **Protocol**: `HTTP`
- **Hostname**: `uploader.atozflooringsolutions.com.au`
- **Port**: `80`
- **Enable HSTS**: (unchecked for HTTP, checked if using HTTPS)

#### Destination:
- **Protocol**: `HTTP`
- **Hostname**: `localhost`
- **Port**: `5007`

#### Additional Settings (Advanced):
- **Enable WebSocket**: ✓ (if available)
- **Enable HTTP/2**: (optional)

### Step 4: Save and Enable

1. Click **Save**
2. Ensure the rule is **enabled** (green toggle should be ON)
3. Click **Apply**

## Verify Configuration

### Test Direct Access (Should Work):
```
http://192.168.0.201:5007
```

### Test Domain Access (Requires DNS):
```
http://uploader.atozflooringsolutions.com.au
```

## DNS Configuration

For the domain to work, you need DNS configuration:

### Option 1: Public DNS (If domain is public)
- Add A record: `uploader.atozflooringsolutions.com.au` → Your NAS public IP
- Or use CNAME if you have a dynamic IP

### Option 2: Local DNS / Hosts File (For local network only)

**On each computer that needs access:**

**Windows:**
1. Edit: `C:\Windows\System32\drivers\etc\hosts`
2. Add line: `192.168.0.201    uploader.atozflooringsolutions.com.au`
3. Save (may require admin rights)

**Mac/Linux:**
1. Edit: `/etc/hosts`
2. Add line: `192.168.0.201    uploader.atozflooringsolutions.com.au`
3. Save (may require sudo)

### Option 3: Router DNS (For entire network)

If your router supports custom DNS entries:
- Add DNS entry: `uploader.atozflooringsolutions.com.au` → `192.168.0.201`

## Troubleshooting

### Domain Not Resolving

1. **Check DNS/hosts file** - Ensure domain points to `192.168.0.201`
2. **Test with IP**: `http://192.168.0.201:5007` (should work)
3. **Check reverse proxy rule** - Ensure it's enabled

### 502 Bad Gateway

1. **Check container is running**:
   ```bash
   ssh atoz@192.168.0.201
   docker ps | grep uploader
   ```

2. **Check port is accessible**:
   ```bash
   curl http://localhost:5007
   ```

3. **Check reverse proxy destination** - Should be `localhost:5007`

### Container Not Running

Start the container:
```bash
ssh atoz@192.168.0.201
cd /volume1/docker/rfms-uploader
docker-compose -f docker-compose-nas.yml up -d
```

## Current Status

- ✅ Container Port: 5007 (configured in docker-compose-nas.yml)
- ✅ Container: Running
- ⚠️ Reverse Proxy: Needs to be configured in Synology DSM
- ⚠️ DNS: Needs to be configured (hosts file or DNS server)

## Quick Commands

### Check container status:
```bash
ssh atoz@192.168.0.201 'docker ps | grep uploader'
```

### View container logs:
```bash
ssh atoz@192.168.0.201 'cd /volume1/docker/rfms-uploader && docker logs uploader -f'
```

### Restart container:
```bash
ssh atoz@192.168.0.201 'cd /volume1/docker/rfms-uploader && docker-compose -f docker-compose-nas.yml restart'
```

### Test port:
```bash
ssh atoz@192.168.0.201 'curl -I http://localhost:5007'
```




