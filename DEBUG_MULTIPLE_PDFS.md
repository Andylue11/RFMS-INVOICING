# Debug Guide: Multiple PDF Creation (504 Gateway Timeout)

## Issue Summary
The `/api/create-multiple-installer-pdfs` endpoint is returning 504 Gateway Timeout errors when creating multiple PDFs.

## Code Review Status
✅ Code compiles successfully  
✅ Error handling is in place  
✅ Progress logging added  
✅ Order limit validation (50 max)  
✅ Frontend timeout handling (5 minutes)

## Potential Causes

### 1. Server/Gateway Timeout (Most Likely)
The 504 error suggests the reverse proxy (nginx, Apache, or Docker gateway) is timing out before Flask can respond.

**Check:**
- Nginx: `proxy_read_timeout` in nginx.conf (default: 60s)
- Apache: `Timeout` directive in httpd.conf (default: 60s)
- Docker: Container/proxy timeout settings
- Gunicorn/uWSGI: Worker timeout settings

**Fix:**
- Increase timeout to 300-600 seconds (5-10 minutes) for long-running PDF generation

### 2. Request Processing Time
Multiple PDFs can take a long time:
- Each order: Fetch attachments → Download → Compress → Create PDF
- With 10 orders × 5 photos each = 50 images to process

**Mitigations Already in Place:**
- Order limit: 50 orders max (configurable via `MAX_PDF_ORDERS`)
- Progress logging to identify slow steps
- Frontend timeout: 5 minutes with clear error messages

### 3. Resource Exhaustion
Large file processing can exhaust memory or disk space.

**Check:**
- Available disk space in temp directories
- Available memory
- Server logs for out-of-memory errors

## Testing Steps

### 1. Test Endpoint Availability
```bash
python debug_multiple_pdfs.py http://YOUR_SERVER_URL:PORT
```

### 2. Test Single Order (Baseline)
```bash
python debug_multiple_pdfs.py http://YOUR_SERVER_URL:PORT AZ003425
```
This establishes baseline performance for a single order.

### 3. Test Multiple Orders (Progressive)
Start with 2 orders, then gradually increase:
```bash
python debug_multiple_pdfs.py http://YOUR_SERVER_URL:PORT AZ003425 AZ003459
python debug_multiple_pdfs.py http://YOUR_SERVER_URL:PORT AZ003425 AZ003459 AZ003460
```

### 4. Test Server Timeout Configuration
```bash
python test_server_timeout.py http://YOUR_SERVER_URL:PORT
```
This will test progressively longer timeouts to find the threshold.

## Debugging Checklist

### Server-Side
- [ ] Check server logs (`app.log`) for error messages
- [ ] Look for timeout values in logs
- [ ] Check reverse proxy configuration (nginx/Apache)
- [ ] Verify disk space available
- [ ] Check memory usage during PDF generation
- [ ] Review Docker/container timeout settings

### Application-Side
- [ ] Verify RFMS API calls are completing successfully
- [ ] Check if downloads are timing out
- [ ] Verify image compression is working
- [ ] Confirm PDF creation is completing
- [ ] Check ZIP file creation is working

### Network-Side
- [ ] Test with fewer orders (find timeout threshold)
- [ ] Monitor network latency to RFMS API
- [ ] Check if downloads are slow
- [ ] Verify file sizes aren't too large

## Code Improvements Made

1. **Progress Logging**
   - Logs timing for each order
   - Logs total processing time
   - Logs success/failure counts

2. **Order Limit**
   - Maximum 50 orders (configurable via `MAX_PDF_ORDERS` env var)
   - Returns clear error if limit exceeded

3. **Error Handling**
   - Detailed error messages
   - Individual order failure tracking
   - Graceful degradation (continues with other orders if one fails)

4. **Frontend Timeout**
   - 5-minute timeout with AbortController
   - Clear error messages for timeout scenarios
   - Better user feedback

## Recommended Fixes

### If Server Timeout is the Issue:

**For Nginx:**
```nginx
location / {
    proxy_pass http://flask_app;
    proxy_read_timeout 600s;  # 10 minutes
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
}
```

**For Apache:**
```apache
Timeout 600
ProxyTimeout 600
```

**For Docker (docker-compose.yml):**
```yaml
services:
  pdf-extractor:
    environment:
      - NGINX_PROXY_READ_TIMEOUT=600
```

### If Processing is Too Slow:

1. **Process in smaller batches**
   - Limit to 10-20 orders at a time
   - Process remaining orders separately

2. **Optimize processing**
   - Consider parallel processing (if supported)
   - Reduce image compression quality (already at 75%)
   - Skip compression for small images

3. **Implement background jobs**
   - Move to async task queue (Celery, RQ)
   - Send email notification when ready
   - Provide download link instead of immediate response

## Monitoring

### Key Metrics to Track:
- Average time per order
- Time per step (download, compress, PDF creation)
- Success rate
- Timeout frequency
- File sizes generated

### Log Messages to Watch:
```
Processing order X/Y: AZ######
Created PDF for AZ######: ... in X.XXs
Completed processing Y orders in X.XXs. Success: X, Failed: Y
```

## Next Steps

1. Run `debug_multiple_pdfs.py` on production server
2. Review server logs during a timeout
3. Check reverse proxy timeout configuration
4. Test with progressively more orders to find threshold
5. Implement fixes based on findings

## Support Commands

```bash
# Test single order
python debug_multiple_pdfs.py http://192.168.0.201:5000 AZ003425

# Test multiple orders
python debug_multiple_pdfs.py http://192.168.0.201:5000 AZ003425 AZ003459 AZ003460

# Test server timeout
python test_server_timeout.py http://192.168.0.201:5000

# Test endpoint with default orders
python test_multiple_pdfs.py
```

