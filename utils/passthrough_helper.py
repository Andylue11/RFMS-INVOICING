"""
Helper utilities for RFMS Passthrough API endpoint.

The passthrough endpoint allows calling raw RFMS methods directly.
This module provides utilities to work with the passthrough API.

Known Methods:
- Inventory.ReceiveFromInvoice - Receive inventory and optionally satisfy/close purchase orders
  - Receiving_SatisfyPo: True/False - If True, closes the purchase order

To discover more methods, you would need to:
1. Check RFMS documentation
2. Contact RFMS support
3. Use RFMS API explorer if available
4. Try common method naming patterns (e.g., Inventory.*, Order.*, etc.)
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def test_passthrough_method(rfms_client, method_name: str, request_payload: Dict) -> Dict:
    """
    Test a passthrough method call.
    
    Args:
        rfms_client: RFMSClient instance
        method_name: The method name to test (e.g., "Inventory.ReceiveFromInvoice")
        request_payload: The payload for the method
        
    Returns:
        Dict: Response from the API
    """
    try:
        result = rfms_client.passthrough(method_name, request_payload)
        logger.info(f"Method {method_name} returned: {result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"Error testing method {method_name}: {e}")
        raise


# Known RFMS Passthrough Methods
KNOWN_METHODS = {
    "Inventory.ReceiveFromInvoice": {
        "description": "Receive inventory from invoice and optionally satisfy/close purchase orders",
        "key_fields": {
            "Receiving_SatisfyPo": "Boolean - If True, closes the purchase order",
            "InventoryDataRows": "Array of inventory items to receive",
            "Supplier": "Supplier name",
            "InvoiceNumber": "Invoice number (optional)",
            "Payable": "AP record (optional, for costing)"
        },
        "response": {
            "ReceivingResults": "Contains receiving status and results",
            "CostingResults": "Contains costing status (if costing attempted)"
        }
    }
}


def get_method_info(method_name: str) -> Optional[Dict]:
    """
    Get information about a known passthrough method.
    
    Args:
        method_name: The method name
        
    Returns:
        Dict with method information, or None if unknown
    """
    return KNOWN_METHODS.get(method_name)


def list_known_methods() -> list:
    """
    List all known passthrough methods.
    
    Returns:
        List of method names
    """
    return list(KNOWN_METHODS.keys())

