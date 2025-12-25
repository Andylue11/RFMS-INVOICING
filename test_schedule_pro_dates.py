"""
Test script for Schedule Pro date range API calls.
Tests different date formats to understand RFMS API requirements.
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.rfms_client import RFMSClient

def test_date_format(date_input, format_name, description):
    """Test converting a date input to MM-DD-YYYY format."""
    print(f"\n{description}")
    print(f"  Input: {date_input} ({format_name})")
    
    # Try parsing as different formats
    formats = [
        ('%d/%m/%Y', 'DD/MM/YYYY (AUS/UK)'),
        ('%m/%d/%Y', 'MM/DD/YYYY (US)'),
        ('%Y-%m-%d', 'YYYY-MM-DD (ISO)'),
        ('%d-%m-%Y', 'DD-MM-YYYY'),
        ('%m-%d-%Y', 'MM-DD-YYYY'),
    ]
    
    parsed_date = None
    used_format = None
    
    for fmt, fmt_name in formats:
        try:
            parsed_date = datetime.strptime(date_input, fmt)
            used_format = fmt_name
            break
        except ValueError:
            continue
    
    if parsed_date:
        us_format = parsed_date.strftime('%m-%d-%Y')
        iso_format = parsed_date.strftime('%Y-%m-%d')
        print(f"  Parsed as: {parsed_date.strftime('%B %d, %Y')} ({used_format})")
        print(f"  Converted to US format (MM-DD-YYYY): {us_format}")
        print(f"  ISO format (YYYY-MM-DD): {iso_format}")
        return us_format, iso_format
    else:
        print(f"  ERROR: Could not parse date in any format!")
        return None, None

def test_rfms_jobs_api(start_date_input, end_date_input, start_format, end_format):
    """Test the RFMS jobs API with the given date inputs."""
    print("\n" + "="*80)
    print(f"TESTING RFMS JOBS API")
    print("="*80)
    
    # Test date parsing
    start_us, start_iso = test_date_format(start_date_input, start_format, "Start Date:")
    end_us, end_iso = test_date_format(end_date_input, end_format, "End Date:")
    
    if not start_us or not end_us:
        print("\nERROR: Could not parse dates. Aborting test.")
        return
    
    print(f"\n{'='*80}")
    print("RFMS API CALL DETAILS")
    print(f"{'='*80}")
    print(f"Store Code: {os.getenv('RFMS_STORE_CODE', 'NOT SET')}")
    print(f"API URL: https://api.rfms.online/v2/jobs/find")
    print(f"\nDate range to send to API (US format MM-DD-YYYY):")
    print(f"  Start: {start_us}")
    print(f"  End: {end_us}")
    
    # Initialize RFMS client
    try:
        rfms_client = RFMSClient()
        rfms_client.start_session()
        print("\n[OK] RFMS client initialized successfully")
    except Exception as e:
        print(f"\n[FAIL] Failed to initialize RFMS client: {e}")
        return
    
    # Make API call
    print(f"\n{'='*80}")
    print("MAKING API CALL...")
    print(f"{'='*80}")
    
    try:
        # Test with US format (MM-DD-YYYY)
        jobs_data = rfms_client.find_jobs_by_date_range(
            start_date=start_us,
            end_date=end_us,
            record_status="Both"
        )
        
        print(f"\n[OK] API call successful")
        print(f"\nResponse structure:")
        print(f"  Type: {type(jobs_data)}")
        
        if isinstance(jobs_data, dict):
            print(f"  Keys: {list(jobs_data.keys())}")
            
            # Check for jobs in different locations
            detail = jobs_data.get('detail')
            result = jobs_data.get('result')
            jobs = jobs_data.get('jobs')
            
            print(f"\n  'detail' field: {type(detail)} - {len(detail) if isinstance(detail, list) else 'N/A'}")
            print(f"  'result' field: {type(result)} - {len(result) if isinstance(result, list) else 'N/A'}")
            print(f"  'jobs' field: {type(jobs) if jobs else None}")
            
            # Extract jobs count
            jobs_list = []
            if isinstance(detail, list):
                jobs_list = detail
            elif isinstance(result, list):
                jobs_list = result
            elif isinstance(jobs, list):
                jobs_list = jobs
            
            print(f"\n  Total jobs found: {len(jobs_list)}")
            
            if len(jobs_list) > 0:
                print(f"\n  Sample jobs (first 5):")
                for i, job in enumerate(jobs_list[:5], 1):
                    doc_num = job.get('documentNumber', 'N/A')
                    scheduled = job.get('scheduledStart', job.get('scheduledDate', 'N/A'))
                    store_num = job.get('storeNumber', 'N/A')
                    print(f"    {i}. Document: {doc_num}, Scheduled: {scheduled}, Store: {store_num}")
                
                # Show date formats in response
                if len(jobs_list) > 0:
                    sample_job = jobs_list[0]
                    print(f"\n  Sample job date fields:")
                    for key in ['scheduledStart', 'scheduledEnd', 'scheduledDate', 'date']:
                        if key in sample_job:
                            print(f"    {key}: {sample_job[key]} (type: {type(sample_job[key])})")
            else:
                print(f"\n  [WARNING] No jobs found in response")
                print(f"\n  Full response structure:")
                print(f"    {jobs_data}")
        else:
            print(f"  Unexpected response type: {type(jobs_data)}")
            print(f"  Response: {jobs_data}")
            
    except Exception as e:
        print(f"\n[FAIL] API call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("="*80)
    print("SCHEDULE PRO DATE RANGE API TEST")
    print("="*80)
    
    # Test with the dates provided by user (DD/MM/YYYY format)
    start_date = "17/11/2025"
    end_date = "21/11/2025"
    
    print(f"\nInput dates (as provided by user):")
    print(f"  Start: {start_date}")
    print(f"  End: {end_date}")
    
    # Test the API call
    test_rfms_jobs_api(start_date, end_date, "DD/MM/YYYY", "DD/MM/YYYY")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

