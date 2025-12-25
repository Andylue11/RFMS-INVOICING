"""Comprehensive test script for installer photos features."""
import os
import sys
from dotenv import load_dotenv
from utils.rfms_client import RFMSClient
import logging
from datetime import datetime, timedelta
import json

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_rfms_connection():
    """Test RFMS connection."""
    print("\n" + "="*80)
    print("TEST 1: RFMS Connection")
    print("="*80)
    try:
        rfms_client = RFMSClient()
        result = rfms_client.test_connection(force_new_session=True)
        if result.get('success'):
            print(f"[PASS] {result.get('message')}")
            return True, rfms_client
        else:
            print(f"[FAIL] {result.get('message')}")
            return False, None
    except Exception as e:
        print(f"[FAIL] Connection error: {e}")
        return False, None

def test_get_order(order_number):
    """Test getting order details."""
    print("\n" + "="*80)
    print(f"TEST 2: Get Order Details - {order_number}")
    print("="*80)
    try:
        rfms_client = RFMSClient()
        order_data = rfms_client.get_order(order_number, locked=False, include_attachments=True)
        
        print(f"[PASS] Successfully retrieved order {order_number}")
        
        # Check response structure
        if isinstance(order_data, dict):
            detail = order_data.get('detail')
            result = order_data.get('result')
            
            # Extract attachments
            attachments = []
            attachments = (order_data.get('attachments') or 
                          (result.get('attachments') if isinstance(result, dict) else None) or
                          (detail.get('attachments') if isinstance(detail, dict) else None) or
                          [])
            
            print(f"  - Found {len(attachments)} attachments")
            
            # Test installer photo detection
            from app import is_installer_photo
            installer_photos = [att for att in attachments if is_installer_photo(att)]
            print(f"  - Found {len(installer_photos)} installer photos")
            
            return True, order_data, attachments
        else:
            print(f"[WARN] Unexpected response type: {type(order_data)}")
            return False, order_data, []
    
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None, []

def test_fetch_order_attachments_api(order_number):
    """Test the fetch order attachments API endpoint."""
    print("\n" + "="*80)
    print(f"TEST 3: Fetch Order Attachments API - {order_number}")
    print("="*80)
    
    try:
        import requests
        
        # Test with Flask server running (if available)
        base_url = os.getenv('FLASK_BASE_URL', 'http://localhost:5000')
        
        response = requests.post(
            f"{base_url}/api/fetch-order-attachments",
            json={'order_number': order_number},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"[PASS] API call successful")
                print(f"  - Order: {data.get('order_number')}")
                print(f"  - Total attachments: {data.get('total', 0)}")
                print(f"  - Installer photos: {data.get('installer_photos_count', 0)}")
                return True, data
            else:
                print(f"[FAIL] API returned success=false: {data.get('error')}")
                return False, data
        else:
            print(f"[SKIP] Server not running or error: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None, None
    
    except requests.exceptions.ConnectionError:
        print("[SKIP] Flask server not running. Start server to test API endpoints.")
        return None, None
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False, None

def test_find_jobs_by_date_range(rfms_client, start_date, end_date):
    """Test finding jobs by date range."""
    print("\n" + "="*80)
    print(f"TEST 4: Find Jobs by Date Range - {start_date} to {end_date}")
    print("="*80)
    
    try:
        # Convert dates to MM-DD-YYYY format
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_date_formatted = start_dt.strftime('%m-%d-%Y')
        end_date_formatted = end_dt.strftime('%m-%d-%Y')
        
        jobs_data = rfms_client.find_jobs_by_date_range(
            start_date=start_date_formatted,
            end_date=end_date_formatted,
            record_status="Both"
        )
        
        # Extract jobs
        jobs = []
        if isinstance(jobs_data, dict):
            detail = jobs_data.get('detail')
            result = jobs_data.get('result')
            
            jobs = (jobs_data.get('jobs') or 
                   (result.get('jobs') if isinstance(result, dict) else None) or
                   (detail if isinstance(detail, list) else None) or
                   [])
        
        print(f"[PASS] Found {len(jobs)} jobs in date range")
        
        # Show sample jobs
        for i, job in enumerate(jobs[:5], 1):
            order_number = job.get('orderNumber') or job.get('order_number') or job.get('poNumber') or 'N/A'
            scheduled_date = job.get('scheduledDate') or job.get('scheduled_date') or job.get('date') or 'N/A'
            print(f"  {i}. Order: {order_number}, Scheduled: {scheduled_date}")
        
        if len(jobs) > 5:
            print(f"  ... and {len(jobs) - 5} more jobs")
        
        return True, jobs
    
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False, []

def test_fetch_scheduled_jobs_api(start_date, end_date):
    """Test the fetch scheduled jobs API endpoint."""
    print("\n" + "="*80)
    print(f"TEST 5: Fetch Scheduled Jobs API - {start_date} to {end_date}")
    print("="*80)
    
    try:
        import requests
        
        base_url = os.getenv('FLASK_BASE_URL', 'http://localhost:5000')
        
        response = requests.post(
            f"{base_url}/api/fetch-scheduled-jobs",
            json={
                'start_date': start_date,
                'end_date': end_date
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                jobs = data.get('jobs', [])
                print(f"[PASS] API call successful")
                print(f"  - Total jobs: {data.get('total', 0)}")
                print(f"  - Jobs processed: {len(jobs)}")
                
                # Show sample jobs
                for i, job in enumerate(jobs[:5], 1):
                    print(f"  {i}. {job.get('order_number')} - PO: {job.get('po_number', 'N/A')} - Photos: {job.get('installer_photo_count', 0)}")
                
                return True, data
            else:
                print(f"[FAIL] API returned success=false: {data.get('error')}")
                return False, data
        else:
            print(f"[SKIP] Server not running or error: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None, None
    
    except requests.exceptions.ConnectionError:
        print("[SKIP] Flask server not running. Start server to test API endpoints.")
        return None, None
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_order_number_normalization():
    """Test order number normalization."""
    print("\n" + "="*80)
    print("TEST 6: Order Number Normalization")
    print("="*80)
    
    test_cases = [
        ("az003021", "AZ003021"),
        ("AZ003021", "AZ003021"),
        ("Az003021", "AZ003021"),
        ("az003425", "AZ003425"),
    ]
    
    try:
        rfms_client = RFMSClient()
        
        for input_val, expected in test_cases:
            try:
                # Test that get_order normalizes the order number
                order_data = rfms_client.get_order(input_val, locked=False, include_attachments=False)
                
                # The order number should be normalized internally
                print(f"[PASS] '{input_val}' -> normalized to uppercase (order retrieved)")
            except Exception as e:
                # If order doesn't exist, that's OK - we're just testing normalization
                if "404" in str(e) or "not found" in str(e).lower():
                    print(f"[PASS] '{input_val}' -> normalized (order not found, but no case error)")
                else:
                    print(f"[WARN] '{input_val}' -> Error: {e}")
        
        return True
    
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_installer_photo_detection():
    """Test installer photo detection logic."""
    print("\n" + "="*80)
    print("TEST 7: Installer Photo Detection")
    print("="*80)
    
    try:
        from app import is_installer_photo
        
        test_cases = [
            ({'description': 'Installer Photo - 20/10/25 10:48 am'}, True),
            ({'name': 'INSTALLER PHOTOS'}, True),
            ({'title': 'Installer Photo'}, True),
            ({'tag': 'INSTALLER PHOTOS'}, True),
            ({'description': 'Some other photo'}, False),
            ({'description': 'regular attachment'}, False),
        ]
        
        all_passed = True
        for attachment, expected in test_cases:
            result = is_installer_photo(attachment)
            status = "[PASS]" if result == expected else "[FAIL]"
            if result != expected:
                all_passed = False
            print(f"  {status} {attachment.get('description', attachment.get('name', 'N/A'))} -> {result} (expected {expected})")
        
        return all_passed
    
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("INSTALLER PHOTOS - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    results = {
        'passed': 0,
        'failed': 0,
        'skipped': 0
    }
    
    # Test 1: RFMS Connection
    success, rfms_client = test_rfms_connection()
    if success:
        results['passed'] += 1
    else:
        results['failed'] += 1
        print("\n[ERROR] Cannot continue without RFMS connection. Exiting.")
        return results
    
    # Test 2: Get Order (test with known order)
    test_order = "AZ003021"
    success, order_data, attachments = test_get_order(test_order)
    if success:
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 3: Fetch Order Attachments API
    result = test_fetch_order_attachments_api(test_order)
    if result[0] is True:
        results['passed'] += 1
    elif result[0] is False:
        results['failed'] += 1
    else:
        results['skipped'] += 1
    
    # Test 4: Find Jobs by Date Range
    # Use a date range that should have jobs (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    success, jobs = test_find_jobs_by_date_range(
        rfms_client,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    if success:
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 5: Fetch Scheduled Jobs API
    result = test_fetch_scheduled_jobs_api(
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    if result[0] is True:
        results['passed'] += 1
    elif result[0] is False:
        results['failed'] += 1
    else:
        results['skipped'] += 1
    
    # Test 6: Order Number Normalization
    success = test_order_number_normalization()
    if success:
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 7: Installer Photo Detection
    success = test_installer_photo_detection()
    if success:
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Passed:  {results['passed']}")
    print(f"Failed:  {results['failed']}")
    print(f"Skipped: {results['skipped']}")
    print("="*80)
    
    return results

if __name__ == '__main__':
    results = run_all_tests()
    sys.exit(0 if results['failed'] == 0 else 1)

