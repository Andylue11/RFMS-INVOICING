"""
Test script for the multiple installer PDFs creation endpoint.
Tests the /api/create-multiple-installer-pdfs endpoint.
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_create_multiple_pdfs(order_numbers):
    """Test creating multiple PDFs from order numbers."""
    base_url = os.getenv('FLASK_URL', 'http://localhost:5000')
    endpoint = f"{base_url}/api/create-multiple-installer-pdfs"
    
    print("="*80)
    print("TESTING MULTIPLE PDF CREATION ENDPOINT")
    print("="*80)
    print(f"Endpoint: {endpoint}")
    print(f"Order numbers: {order_numbers}")
    print()
    
    payload = {
        "order_numbers": order_numbers
    }
    
    try:
        print("Sending POST request...")
        response = requests.post(
            endpoint,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=120  # 2 minute timeout for multiple PDFs
        )
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        # Check if response is JSON or a file (ZIP)
        content_type = response.headers.get('Content-Type', '')
        print(f"Content-Type: {content_type}")
        
        if 'application/json' in content_type:
            # JSON response (error or no PDFs)
            try:
                data = response.json()
                print(f"\nJSON Response:")
                print(json.dumps(data, indent=2))
                
                if data.get('success'):
                    print("\n[OK] Request successful")
                else:
                    print(f"\n[FAIL] Request failed: {data.get('error', 'Unknown error')}")
                    if 'results' in data:
                        print("\nResults:")
                        for result in data['results']:
                            status = "[OK]" if result.get('success') else "[FAIL]"
                            print(f"  {status} {result.get('order_number')}: {result.get('error', 'Success')}")
                    
            except json.JSONDecodeError as e:
                print(f"\n[FAIL] Failed to parse JSON response: {e}")
                print(f"Response text (first 500 chars): {response.text[:500]}")
        
        elif 'application/zip' in content_type or 'application/octet-stream' in content_type:
            # ZIP file response
            content_disposition = response.headers.get('Content-Disposition', '')
            filename = 'installer_photos.zip'
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            
            print(f"\n[OK] Received ZIP file: {filename}")
            print(f"File size: {len(response.content)} bytes ({len(response.content)/1024:.2f} KB)")
            
            # Save the ZIP file
            output_path = f"test_output_{filename}"
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"Saved to: {output_path}")
            
        else:
            # Unexpected response type
            print(f"\n[WARNING] Unexpected Content-Type: {content_type}")
            print(f"Response text (first 500 chars): {response.text[:500]}")
            
            # Try to parse as JSON anyway
            try:
                data = response.json()
                print(f"Parsed as JSON:")
                print(json.dumps(data, indent=2))
            except:
                print("Could not parse as JSON")
    
    except requests.exceptions.Timeout:
        print("\n[FAIL] Request timed out after 120 seconds")
    except requests.exceptions.ConnectionError as e:
        print(f"\n[FAIL] Connection error: {e}")
        print("Make sure the Flask server is running at the specified URL")
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Use order numbers from command line
        order_numbers = sys.argv[1:]
    else:
        # Use test order numbers
        order_numbers = ["AZ003425", "AZ003459"]  # Add test order numbers here
    
    print(f"Testing with order numbers: {order_numbers}")
    print()
    
    test_create_multiple_pdfs(order_numbers)

