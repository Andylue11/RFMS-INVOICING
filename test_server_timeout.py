"""
Test script to check server timeout configuration.
This script tests various timeout scenarios to diagnose 504 Gateway Timeout errors.
"""

import requests
import time
import os
from dotenv import load_dotenv
import json

load_dotenv()

def test_server_response_time(url, method='GET', payload=None):
    """Test how long the server takes to respond."""
    print(f"\n{'='*80}")
    print(f"Testing: {method} {url}")
    print(f"{'='*80}")
    
    start_time = time.time()
    try:
        if method == 'GET':
            response = requests.get(url, timeout=600)  # 10 minute timeout for test
        elif method == 'POST':
            response = requests.post(
                url, 
                json=payload if payload else {},
                headers={'Content-Type': 'application/json'},
                timeout=600  # 10 minute timeout for test
            )
        
        elapsed = time.time() - start_time
        
        print(f"[OK] Response received in {elapsed:.2f} seconds")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Content-Length: {response.headers.get('Content-Length', 'N/A')} bytes")
        
        if response.status_code == 504:
            print(f"   [WARNING] GATEWAY TIMEOUT detected at {elapsed:.2f} seconds")
        
        return {
            'success': True,
            'status_code': response.status_code,
            'elapsed_time': elapsed,
            'is_timeout': response.status_code == 504
        }
        
    except requests.exceptions.Timeout as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] Request timed out after {elapsed:.2f} seconds")
        print(f"   Error: {e}")
        return {
            'success': False,
            'status_code': None,
            'elapsed_time': elapsed,
            'is_timeout': True,
            'error': str(e)
        }
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection error: {e}")
        return {
            'success': False,
            'status_code': None,
            'elapsed_time': None,
            'is_timeout': False,
            'error': f'Connection error: {str(e)}'
        }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] Error: {e}")
        return {
            'success': False,
            'status_code': None,
            'elapsed_time': elapsed,
            'is_timeout': False,
            'error': str(e)
        }

def test_long_running_endpoint(base_url, duration_seconds):
    """Test if the server can handle long-running requests."""
    print(f"\n{'='*80}")
    print(f"Testing long-running request (simulating {duration_seconds}s processing)")
    print(f"{'='*80}")
    
    # Try to find a test endpoint, or use a simulated one
    # For now, we'll test with a small PDF creation request
    test_url = f"{base_url}/api/create-multiple-installer-pdfs"
    
    # Use a small number of orders to test
    payload = {
        'order_numbers': ['TEST']  # This will fail, but we want to see timeout behavior
    }
    
    print(f"Sending request that should take ~{duration_seconds} seconds...")
    start_time = time.time()
    
    try:
        response = requests.post(
            test_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=duration_seconds + 60  # Add buffer
        )
        
        elapsed = time.time() - start_time
        print(f"[OK] Response received in {elapsed:.2f} seconds")
        print(f"   Status Code: {response.status_code}")
        
        return {
            'success': True,
            'status_code': response.status_code,
            'elapsed_time': elapsed
        }
        
    except requests.exceptions.Timeout as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] Request timed out after {elapsed:.2f} seconds")
        print(f"   This suggests the server timeout is less than {duration_seconds} seconds")
        return {
            'success': False,
            'status_code': 504,
            'elapsed_time': elapsed,
            'is_timeout': True
        }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[WARNING] Request completed/errored in {elapsed:.2f} seconds: {e}")
        return {
            'success': False,
            'elapsed_time': elapsed,
            'error': str(e)
        }

def test_server_health(base_url):
    """Test basic server health endpoints."""
    print(f"\n{'='*80}")
    print("Testing Server Health Endpoints")
    print(f"{'='*80}")
    
    health_endpoints = [
        '/',
        '/api/rfms-status',
        '/installer-photos'
    ]
    
    results = []
    for endpoint in health_endpoints:
        url = f"{base_url}{endpoint}"
        result = test_server_response_time(url, method='GET')
        results.append({
            'endpoint': endpoint,
            **result
        })
        time.sleep(1)  # Small delay between requests
    
    return results

def check_timeout_headers(response):
    """Check response headers for timeout information."""
    print(f"\n{'='*80}")
    print("Response Headers Analysis")
    print(f"{'='*80}")
    
    timeout_related_headers = [
        'X-Timeout',
        'X-Request-Timeout',
        'X-Proxy-Timeout',
        'Proxy-Timeout',
        'Retry-After',
        'Server',
        'X-Powered-By'
    ]
    
    print("Timeout-related headers found:")
    found_any = False
    for header in timeout_related_headers:
        value = response.headers.get(header)
        if value:
            print(f"  {header}: {value}")
            found_any = True
    
    if not found_any:
        print("  (No timeout-related headers found)")
    
    # Check for common reverse proxy headers
    proxy_headers = [
        'Via',
        'X-Forwarded-For',
        'X-Forwarded-Proto',
        'X-Real-IP',
        'Server'
    ]
    
    print("\nReverse proxy indicators:")
    for header in proxy_headers:
        value = response.headers.get(header)
        if value:
            print(f"  {header}: {value}")
            if header == 'Server':
                if 'nginx' in value.lower():
                    print("    [WARNING] nginx detected - check nginx timeout settings")
                elif 'apache' in value.lower() or 'httpd' in value.lower():
                    print("    [WARNING] Apache detected - check Apache Timeout directive")

def main():
    """Main test function."""
    import sys
    
    print("="*80)
    print("SERVER TIMEOUT CONFIGURATION TEST")
    print("="*80)
    
    # Check for command line argument
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        if not base_url.startswith('http'):
            base_url = f"http://{base_url}"
    else:
        base_url = os.getenv('FLASK_URL', 'http://localhost:5000')
    
    print(f"\nBase URL: {base_url}")
    print("Testing server timeout configuration...")
    print("\nNote: This script will test the server's timeout configuration.")
    print("Make sure the server is running before proceeding.")
    print("\nUsage: python test_server_timeout.py [SERVER_URL]")
        print("Example: python test_server_timeout.py http://192.168.0.201:5000\n")
    
    # Check if server is accessible
    try:
        test_response = requests.get(f"{base_url}/", timeout=5)
        print(f"[OK] Server is accessible at {base_url}")
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to server at {base_url}")
        print("\nPlease either:")
        print("1. Start the server locally, or")
        print("2. Set FLASK_URL environment variable to point to your production server")
        print("   Example: export FLASK_URL=http://192.168.0.201:5000")
        return
    except Exception as e:
        print(f"[WARNING] Server check returned: {e}")
        print("Continuing with tests anyway...\n")
    
    # Test 1: Basic health check
    print("\n" + "="*80)
    print("TEST 1: Basic Server Health")
    print("="*80)
    health_results = test_server_health(base_url)
    
    # Test 2: Test response headers for timeout info
    print("\n" + "="*80)
    print("TEST 2: Response Headers Analysis")
    print("="*80)
    try:
        response = requests.get(f"{base_url}/", timeout=30)
        check_timeout_headers(response)
    except Exception as e:
        print(f"Could not fetch headers: {e}")
    
    # Test 3: Test progressively longer timeouts
    print("\n" + "="*80)
    print("TEST 3: Progressive Timeout Test")
    print("="*80)
    print("Testing different timeout scenarios...")
    
    timeout_tests = [30, 60, 90, 120, 180, 300]  # 30s, 1m, 1.5m, 2m, 3m, 5m
    
    timeout_results = []
    for timeout_seconds in timeout_tests:
        print(f"\nTesting {timeout_seconds}-second timeout threshold...")
        result = test_long_running_endpoint(base_url, timeout_seconds)
        timeout_results.append({
            'timeout_threshold': timeout_seconds,
            **result
        })
        
        if result.get('is_timeout'):
            print(f"[WARNING] Server times out before {timeout_seconds} seconds")
            break
        
        time.sleep(2)  # Small delay between tests
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    print("\nHealth Check Results:")
    for result in health_results:
        status = "[OK]" if result.get('success') else "[ERROR]"
        elapsed = result.get('elapsed_time', 0) if result.get('elapsed_time') else 0
        print(f"  {status} {result.get('endpoint', 'N/A')}: {elapsed:.2f}s (Status: {result.get('status_code', 'N/A')})")
    
    print("\nTimeout Test Results:")
    max_timeout = 0
    for result in timeout_results:
        elapsed = result.get('elapsed_time', 0) if result.get('elapsed_time') else 0
        if result.get('is_timeout'):
            print(f"  [ERROR] Timeout detected at {elapsed:.2f}s (test threshold: {result.get('timeout_threshold')}s)")
            max_timeout = elapsed
            break
        else:
            print(f"  [OK] Request completed in {elapsed:.2f}s (test threshold: {result.get('timeout_threshold')}s)")
            max_timeout = elapsed
    
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    if max_timeout > 0:
        if max_timeout < 60:
            print(f"[WARNING] Server timeout appears to be very short ({max_timeout:.0f} seconds)")
            print("   Recommendation: Increase server timeout to at least 300 seconds (5 minutes)")
        elif max_timeout < 180:
            print(f"[WARNING] Server timeout is {max_timeout:.0f} seconds")
            print("   Recommendation: Consider increasing to 300-600 seconds for PDF generation")
        else:
            print(f"[OK] Server timeout appears sufficient ({max_timeout:.0f} seconds)")
    else:
        print("[WARNING] Could not determine server timeout")
        print("   Recommendation: Check server logs and reverse proxy configuration")
    
    print("\nNext Steps:")
    print("1. If using nginx: Increase 'proxy_read_timeout' in nginx.conf")
    print("2. If using Apache: Increase 'Timeout' directive in httpd.conf")
    print("3. If using Docker: Check container/proxy timeout settings")
    print("4. Check application server (gunicorn/uwsgi) timeout settings")
    print("5. Consider implementing background job processing for long-running tasks")

if __name__ == '__main__':
    main()

