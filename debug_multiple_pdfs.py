"""
Debug script for multiple PDF creation endpoint.
Tests and debugs the /api/create-multiple-installer-pdfs endpoint with detailed logging.
"""

import requests
import json
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

def test_endpoint_availability(base_url):
    """Test if the endpoint is available and responding."""
    print("="*80)
    print("TEST 1: Endpoint Availability Check")
    print("="*80)
    
    try:
        # Test basic server health
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"[OK] Server is accessible: {response.status_code}")
        
        # Test endpoint with empty payload
        endpoint = f"{base_url}/api/create-multiple-installer-pdfs"
        response = requests.post(
            endpoint,
            json={},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"[OK] Endpoint is accessible: {response.status_code}")
        if response.status_code == 400:
            print("[OK] Endpoint correctly rejects empty payload")
            try:
                data = response.json()
                print(f"    Error message: {data.get('error', 'N/A')}")
            except:
                pass
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to server at {base_url}")
        print("    Make sure the server is running")
        return False
    except Exception as e:
        print(f"[ERROR] Error testing endpoint: {e}")
        return False

def test_single_order(base_url, order_number):
    """Test creating PDF for a single order."""
    print("\n" + "="*80)
    print(f"TEST 2: Single Order Test - {order_number}")
    print("="*80)
    
    endpoint = f"{base_url}/api/create-multiple-installer-pdfs"
    payload = {
        "order_numbers": [order_number]
    }
    
    print(f"Sending request for order: {order_number}")
    start_time = time.time()
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5 minute timeout
        )
        
        elapsed = time.time() - start_time
        print(f"Response received in {elapsed:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        content_type = response.headers.get('Content-Type', '')
        print(f"Content-Type: {content_type}")
        
        if response.status_code == 200:
            if 'application/zip' in content_type:
                print(f"[OK] Received ZIP file ({len(response.content)} bytes)")
                return True
            else:
                print(f"[WARNING] Unexpected content type: {content_type}")
                print(f"Response text (first 500 chars): {response.text[:500]}")
                return False
        elif response.status_code == 504:
            print(f"[ERROR] Gateway Timeout - request took {elapsed:.2f}s")
            print("    The server/gateway timed out before the request completed")
            print("    This suggests the timeout is less than 5 minutes")
            return False
        else:
            # Try to parse error response
            try:
                data = response.json()
                print(f"[FAIL] Request failed: {data.get('error', 'Unknown error')}")
                if 'results' in data:
                    print("\nResults:")
                    for result in data['results']:
                        status = "[OK]" if result.get('success') else "[FAIL]"
                        print(f"  {status} {result.get('order_number')}: {result.get('error', 'Success')}")
            except:
                print(f"[FAIL] Request failed with status {response.status_code}")
                print(f"Response text (first 500 chars): {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"[ERROR] Request timed out after {elapsed:.2f} seconds")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] Unexpected error after {elapsed:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_orders(base_url, order_numbers):
    """Test creating PDFs for multiple orders."""
    print("\n" + "="*80)
    print(f"TEST 3: Multiple Orders Test - {len(order_numbers)} orders")
    print("="*80)
    
    endpoint = f"{base_url}/api/create-multiple-installer-pdfs"
    payload = {
        "order_numbers": order_numbers
    }
    
    print(f"Orders: {', '.join(order_numbers)}")
    print(f"Sending request for {len(order_numbers)} orders...")
    start_time = time.time()
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=600  # 10 minute timeout for multiple orders
        )
        
        elapsed = time.time() - start_time
        print(f"\nResponse received in {elapsed:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        content_type = response.headers.get('Content-Type', '')
        print(f"Content-Type: {content_type}")
        
        if response.status_code == 200:
            if 'application/zip' in content_type:
                zip_size = len(response.content)
                print(f"[OK] Received ZIP file ({zip_size} bytes, {zip_size/1024:.2f} KB)")
                
                # Try to save it
                filename = f"test_output_{int(time.time())}.zip"
                try:
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"[OK] Saved ZIP file to: {filename}")
                except Exception as e:
                    print(f"[WARNING] Could not save ZIP file: {e}")
                
                return True
            else:
                print(f"[WARNING] Unexpected content type: {content_type}")
                print(f"Response text (first 500 chars): {response.text[:500]}")
                return False
        elif response.status_code == 504:
            print(f"[ERROR] Gateway Timeout - request took {elapsed:.2f}s")
            print("    The server/gateway timed out before the request completed")
            print(f"    Average time per order: {elapsed/len(order_numbers):.2f}s")
            print("\n    Recommendations:")
            print("    1. Check server/gateway timeout settings (nginx, Apache, etc.)")
            print("    2. Process fewer orders at a time")
            print("    3. Check server logs for detailed error information")
            return False
        elif response.status_code == 400:
            try:
                data = response.json()
                error = data.get('error', 'Unknown error')
                print(f"[FAIL] Request rejected: {error}")
                if 'Too many orders' in error:
                    print("    Try with fewer orders or increase MAX_PDF_ORDERS")
            except:
                print(f"[FAIL] Request rejected with status 400")
            return False
        else:
            # Try to parse error response
            try:
                data = response.json()
                print(f"[FAIL] Request failed: {data.get('error', 'Unknown error')}")
                if 'results' in data:
                    print("\nResults breakdown:")
                    success_count = sum(1 for r in data['results'] if r.get('success'))
                    fail_count = len(data['results']) - success_count
                    print(f"  Successful: {success_count}")
                    print(f"  Failed: {fail_count}")
                    print("\nDetailed results:")
                    for result in data['results']:
                        status = "[OK]" if result.get('success') else "[FAIL]"
                        order_num = result.get('order_number', 'N/A')
                        error = result.get('error', 'Success')
                        print(f"  {status} {order_num}: {error}")
            except:
                print(f"[FAIL] Request failed with status {response.status_code}")
                print(f"Response text (first 500 chars): {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"[ERROR] Request timed out after {elapsed:.2f} seconds")
        print(f"    Average time per order: {elapsed/len(order_numbers):.2f}s")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] Unexpected error after {elapsed:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_order_limit(base_url):
    """Test the order limit validation."""
    print("\n" + "="*80)
    print("TEST 4: Order Limit Validation")
    print("="*80)
    
    # Create a list of 60 fake order numbers (should exceed the 50 limit)
    fake_orders = [f"AZ{i:06d}" for i in range(1, 61)]
    
    endpoint = f"{base_url}/api/create-multiple-installer-pdfs"
    payload = {
        "order_numbers": fake_orders
    }
    
    print(f"Testing with {len(fake_orders)} orders (should exceed limit of 50)")
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 400:
            try:
                data = response.json()
                error = data.get('error', '')
                if 'Too many orders' in error:
                    print(f"[OK] Order limit validation working: {error}")
                    return True
                else:
                    print(f"[WARNING] Got 400 but unexpected error: {error}")
            except:
                print(f"[WARNING] Got 400 but could not parse response")
        else:
            print(f"[FAIL] Expected 400 but got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error testing order limit: {e}")
        return False

def main():
    """Main test function."""
    print("="*80)
    print("MULTIPLE PDF CREATION - DEBUG AND TEST SCRIPT")
    print("="*80)
    
    # Get base URL
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        if not base_url.startswith('http'):
            base_url = f"http://{base_url}"
    else:
        base_url = os.getenv('FLASK_URL', 'http://localhost:5000')
    
    print(f"\nBase URL: {base_url}")
    print("\nUsage: python debug_multiple_pdfs.py [SERVER_URL] [ORDER_NUMBERS...]")
    print("Example: python debug_multiple_pdfs.py http://192.168.0.201:5000 AZ003425 AZ003459\n")
    
    # Test 1: Endpoint availability
    if not test_endpoint_availability(base_url):
        print("\n[ERROR] Cannot connect to server. Exiting.")
        return
    
    # Test 2: Order limit validation
    test_order_limit(base_url)
    
    # Get order numbers from command line or use defaults
    if len(sys.argv) > 2:
        order_numbers = sys.argv[2:]
    else:
        # Use test order numbers
        print("\n[INFO] No order numbers provided. Using test order numbers.")
        print("       Provide order numbers as arguments to test specific orders.")
        print("       Example: python debug_multiple_pdfs.py http://localhost:5000 AZ003425 AZ003459\n")
        order_numbers = ["AZ003425"]  # Single test order
    
    # Test 3: Single order test
    if len(order_numbers) == 1:
        test_single_order(base_url, order_numbers[0])
    elif len(order_numbers) > 1:
        # Test 4: Multiple orders test
        test_multiple_orders(base_url, order_numbers)
    
    print("\n" + "="*80)
    print("DEBUG SUMMARY")
    print("="*80)
    print("\nIf you're seeing 504 Gateway Timeout errors:")
    print("1. Check server logs for detailed error information")
    print("2. Test with fewer orders to find the timeout threshold")
    print("3. Check server/gateway timeout settings (nginx, Apache, Docker, etc.)")
    print("4. Consider processing orders in smaller batches")
    print("\nNext steps:")
    print("- Review server logs (app.log) for detailed error messages")
    print("- Use test_server_timeout.py to check server timeout configuration")
    print("- Try with 1-2 orders first, then gradually increase")

if __name__ == "__main__":
    main()

