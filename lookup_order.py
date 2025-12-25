#!/usr/bin/env python3
"""
Look up an order by order number and display the full raw payload data.
Usage: python lookup_order.py <order_number>
"""
import os
import sys
import json
from dotenv import load_dotenv
from utils.rfms_client import RFMSClient
import logging

# Load environment variables
load_dotenv()

# Set up logging (only show errors)
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def lookup_order(order_number: str, include_attachments: bool = True):
    """
    Look up an order and display the full raw payload.
    
    Args:
        order_number: The order number to look up
        include_attachments: Whether to include attachments in the response
    """
    print("=" * 80)
    print(f"Looking up order: {order_number}")
    print("=" * 80)
    print()
    
    try:
        # Initialize RFMS client
        rfms_client = RFMSClient()
        
        # Test connection first
        print("[1/3] Testing RFMS connection...")
        connection_test = rfms_client.test_connection(force_new_session=True)
        if not connection_test.get('success'):
            print(f"[ERROR] Connection failed: {connection_test.get('message')}")
            return False
        print("[OK] Connection successful")
        print()
        
        # Get order details
        print(f"[2/3] Fetching order details (include_attachments={include_attachments})...")
        order_data = rfms_client.get_order(
            order_number, 
            locked=False, 
            include_attachments=include_attachments
        )
        print("[OK] Order data retrieved")
        print()
        
        # Display the full raw payload
        print("[3/3] Full Raw Payload Data:")
        print("=" * 80)
        print(json.dumps(order_data, indent=2, ensure_ascii=False))
        print("=" * 80)
        
        # Also save to file for easier viewing
        output_file = f"order_{order_number}_payload.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(order_data, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Full payload also saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Get order number from command line or use default
    if len(sys.argv) > 1:
        order_number = sys.argv[1]
    else:
        # Default order number from user query
        order_number = "AZ003521"
    
    # Optional: include attachments flag
    include_attachments = True
    if len(sys.argv) > 2:
        include_attachments = sys.argv[2].lower() in ('true', '1', 'yes')
    
    success = lookup_order(order_number, include_attachments)
    sys.exit(0 if success else 1)

