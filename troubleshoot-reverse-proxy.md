# Troubleshooting: Reverse Proxy Not Working

If you set up reverse proxy but it's not working, check these common issues:

## Quick Diagnostics

1. **Test direct access first:**
   ```
   http://192.168.0.201:5005
   ```
   - If this works, your Docker container is fine
   - If this doesn't work, fix the container first

2. **Check reverse proxy configuration:**
   - Synology DSM → Control Panel → Reverse Proxy
   - Verify the rule is **enabled** (green toggle)
   - Verify **Destination** is `localhost:5005` (or `127.0.0.1:5005`)

3. **Check what URL you're trying to use:**
   - If using `http://rfms-uploader.local` → Requires hosts file or DNS
   - If using `http://192.168.0.201` → Should work immediately
   - If using `http://AtozServer.local` → Should work if mDNS is enabled

## Common Issues

### Issue 1: "Can't reach this page" or connection refused

**Cause:** Reverse proxy destination is wrong or container isn't running

**Fix:**
```bash
# SSH into server
ssh atoz@AtozServer

# Check if container is running
docker ps | grep pdf-extractor

# Check what port it's actually using
docker port pdf-extractor

# Test from inside the server
curl http://localhost:5005
```

**Solution:** Verify reverse proxy destination matches the actual container port.

---

### Issue 2: Reverse proxy works but shows "502 Bad Gateway"

**Cause:** Container is running but not responding properly

**Fix:**
```bash
# Check container logs
docker logs pdf-extractor --tail 50

# Check if app is listening
docker exec pdf-extractor netstat -tlnp | grep 5000

# Restart container
docker-compose -f docker-compose-synology.yml restart
```

---

### Issue 3: Can't access using custom domain (rfms-uploader.local)

**Cause:** DNS/hosts file not configured

**Solutions:**

**Option A: Use IP instead (Easiest)**
- Just use: `http://192.168.0.201` (if reverse proxy is on port 80)
- Or: `http://192.168.0.201:5005` (direct access)

**Option B: Use Synology hostname**
- Use: `http://AtozServer.local` (or your Synology's hostname)
- Usually works automatically via mDNS

**Option C: Configure hosts file**
- See Method 1B in SETUP-RFMS-UPLOADER-LOCAL.md

---

### Issue 4: Reverse proxy works from one computer but not others

**Cause:** Hosts file only configured on one computer, or firewall issue

**Solutions:**
- Use IP address method instead (works everywhere)
- Use Synology hostname (works everywhere if mDNS enabled)
- Or configure hosts file on each computer

---

### Issue 5: "This site can't be reached" - DNS_PROBE_FINISHED_NXDOMAIN

**Cause:** DNS can't resolve the hostname

**Fix:**
- If using custom domain: Add to hosts file or configure DNS
- If using IP: Just use `http://192.168.0.201` directly
- If using Synology hostname: Make sure mDNS is enabled

---

## Best Practice Recommendation

**For easiest setup that works everywhere:**

1. Configure reverse proxy with:
   - **Source Hostname:** Leave blank (means "all") OR use `192.168.0.201`
   - **Source Port:** `80`
   - **Destination:** `localhost:5005`

2. Access via:
   - `http://192.168.0.201` (works from any computer!)

3. Optional: Bookmark it as "RFMS Uploader" in your browser

**This works from every computer on your network without any configuration!**

---

## Still Not Working?

Run these diagnostic commands:

```bash
# On server
docker ps
docker logs pdf-extractor --tail 50
curl http://localhost:5005

# On client computer
ping 192.168.0.201
curl http://192.168.0.201:5005
```

Share the output if you need more help!

