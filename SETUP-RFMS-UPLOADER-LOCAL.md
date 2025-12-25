# Setup Guide: rfms-uploader.local

This guide shows you how to configure the RFMS Uploader app to be accessible at `http://rfms-uploader.local` instead of `http://192.168.0.201:5005`.

## Method 1: Using Synology Reverse Proxy (Recommended - No Hosts File Needed!)

This method allows access from ANY computer on your network **without editing hosts files** by using your Synology's hostname or IP address.

### Step 1: Find Your Synology Hostname

1. **Check your Synology's hostname:**
   - Open Synology DSM → Control Panel → Info Center → General
   - Look for "Server Name" (e.g., `AtozServer`, `synology`, etc.)
   - Or check Network → Network Interface → Your adapter for hostname

### Step 2: Configure Synology Reverse Proxy

1. **Open Synology DSM**
   - Go to: `http://192.168.0.201:5000` (or your NAS IP)
   - Log in with your admin account

2. **Navigate to Reverse Proxy Settings**
   - Go to **Control Panel** > **Login Portal** (or **Application Portal**)
   - Click the **Advanced** tab
   - Click **Reverse Proxy**

3. **Create New Reverse Proxy Rule**
   - Click the **Create** button
   - Fill in the following:

   **Option A: Using Synology Hostname (Best - No hosts file needed!)**
   - **Reverse Proxy Name:** `rfms-uploader`
   - **Source Hostname:** `AtozServer.local` (or your Synology's hostname + `.local`)
   - **Source Port:** `80`
   - **Destination:** `localhost:5005`
   - **Access via:** `http://AtozServer.local/rfms-uploader` (or similar)

   **Option B: Using IP with Path (Also works without hosts file!)**
   - **Reverse Proxy Name:** `rfms-uploader`
   - **Source Hostname:** `192.168.0.201` (or leave blank for "All")
   - **Source Port:** `80`
   - **Path:** `/rfms-uploader` (optional - allows multiple apps)
   - **Destination:** `localhost:5005`
   - **Access via:** `http://192.168.0.201/rfms-uploader` (or just `http://192.168.0.201` if no path)

   **Option C: Using Custom Domain (Requires hosts file or DNS)**
   - **Reverse Proxy Name:** `rfms-uploader`
   - **Source Hostname:** `rfms-uploader.local`
   - **Source Port:** `80`
   - **Destination:** `localhost:5005`
   - **Access via:** `http://rfms-uploader.local` (requires hosts file or DNS)

4. **Click Save**

### Step 2: Access Your Application

**If you used Option A (Synology hostname):**
- Access at: `http://AtozServer.local` or `http://AtozServer.local/rfms-uploader` (depending on path)
- Works from ANY computer on your network automatically!

**If you used Option B (IP address):**
- Access at: `http://192.168.0.201` or `http://192.168.0.201/rfms-uploader`
- Works from ANY computer - just use the IP!

**If you used Option C (custom domain) - Skip to Method 1B below:**

---

## Method 1B: Using Custom Domain with Reverse Proxy (If you want rfms-uploader.local specifically)

**Note:** This method requires hosts file configuration OR network DNS setup.

### Configure DNS/Hosts File on Each Computer

If you want to use `rfms-uploader.local` specifically, each computer needs to know where to find it:

#### On Windows:
1. Open Notepad as **Administrator**
2. Open file: `C:\Windows\System32\drivers\etc\hosts`
3. Add this line at the end:
   ```
   192.168.0.201    rfms-uploader.local
   ```
4. Save the file
5. Run: `ipconfig /flushdns` (in Command Prompt as Admin)

#### On Mac:
1. Open Terminal
2. Edit hosts file:
   ```bash
   sudo nano /etc/hosts
   ```
3. Add this line:
   ```
   192.168.0.201    rfms-uploader.local
   ```
4. Press `Ctrl+X`, then `Y`, then `Enter` to save
5. Run: `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder`

#### On Linux:
1. Open Terminal
2. Edit hosts file:
   ```bash
   sudo nano /etc/hosts
   ```
3. Add this line:
   ```
   192.168.0.201    rfms-uploader.local
   ```
4. Press `Ctrl+X`, then `Y`, then `Enter` to save

### Verify Setup

1. Open a web browser
2. Navigate to your configured URL (from Step 1)
3. You should see the RFMS Uploader application!

---

## Method 2: Using Direct IP Access (Simplest - No Configuration!)

Just access directly using the IP address:
- **URL:** `http://192.168.0.201:5005`
- Works immediately from any computer
- No configuration needed!

---

## Method 3: Using Hosts File Only (Quick & Simple)

This method is simpler but only works on computers where you edit the hosts file.

### Steps:

1. **Edit hosts file** (same as Step 2 above)
2. **Access via:** `http://rfms-uploader.local:5005`
   - Note: You still need to include `:5005` port with this method

### Pros:
- ✅ Quick setup
- ✅ No Synology configuration needed

### Cons:
- ❌ Must configure each computer individually
- ❌ Still requires port number in URL

---

## Method 4: Local Network DNS (Advanced)

If you have a router that supports custom DNS entries or a local DNS server, you can configure `rfms-uploader.local` at the network level so no hosts file editing is needed.

Check your router's admin panel for DNS or Hostname settings.

---

## Troubleshooting

### Can't access rfms-uploader.local

1. **Check hosts file:**
   ```bash
   # Windows PowerShell
   Get-Content C:\Windows\System32\drivers\etc\hosts | Select-String "rfms-uploader"
   
   # Linux/Mac
   cat /etc/hosts | grep rfms-uploader
   ```

2. **Flush DNS cache:**
   ```bash
   # Windows
   ipconfig /flushdns
   
   # Mac
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
   
   # Linux
   sudo systemd-resolve --flush-caches
   ```

3. **Test connection:**
   ```bash
   # Ping test
   ping rfms-uploader.local
   
   # Should return: 192.168.0.201
   ```

4. **Check reverse proxy is running:**
   - Go to Synology DSM > Control Panel > Reverse Proxy
   - Verify the rule is enabled

5. **Check Docker container is running:**
   ```bash
   ssh atoz@AtozServer
   docker ps | grep pdf-extractor
   ```

6. **Test direct access:**
   - Try: `http://192.168.0.201:5005`
   - If this works but `rfms-uploader.local` doesn't, the issue is DNS/hosts file

### Reverse Proxy Issues

If reverse proxy isn't working:

1. **Check reverse proxy logs:**
   - Synology DSM > Log Center > Reverse Proxy logs

2. **Verify port 5005 is correct:**
   - Container must be running on port 5005
   - Check: `docker ps` and verify port mapping

3. **Check firewall:**
   - Ensure port 80 (HTTP) is not blocked
   - Synology Control Panel > Security > Firewall

---

## Next Steps

After setup is complete:

1. **Bookmark the URL:** `http://rfms-uploader.local`
2. **Test from multiple devices** to ensure it works
3. **Consider HTTPS:** For production, set up SSL certificate (Let's Encrypt via Synology)

---

## Summary

- **Recommended:** Use Method 1 (Reverse Proxy) for network-wide access
- **Quick Test:** Use Method 2 (Hosts File) if you just want it on one computer
- **Production:** Consider Method 3 (Network DNS) for permanent solution

Your app is now accessible at: **http://rfms-uploader.local** 🎉

