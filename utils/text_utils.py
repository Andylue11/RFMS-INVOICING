"""
Text Utilities

Helper functions for text processing, including uppercase conversion for RFMS compatibility.
"""

from typing import Dict, Any, List, Union


def uppercase_text_fields(data: Union[Dict, str, List], fields_to_uppercase: List[str] = None) -> Union[Dict, str, List]:
    """
    Convert specified text fields to uppercase in a dictionary or data structure.
    If fields_to_uppercase is None, converts all string values.
    
    Args:
        data: Dictionary, string, or list to process
        fields_to_uppercase: List of field names to convert (None = all string fields)
        
    Returns:
        Data with text fields converted to uppercase
    """
    if isinstance(data, str):
        return data.upper()
    
    if isinstance(data, list):
        return [uppercase_text_fields(item, fields_to_uppercase) for item in data]
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Convert if field is in list, or if no list specified (convert all)
                if fields_to_uppercase is None or key in fields_to_uppercase:
                    result[key] = value.upper()
                else:
                    result[key] = value
            elif isinstance(value, (dict, list)):
                result[key] = uppercase_text_fields(value, fields_to_uppercase)
            else:
                result[key] = value
        return result
    
    return data


def uppercase_rfms_fields(data: Dict) -> Dict:
    """
    Convert common RFMS-related fields to uppercase.
    
    Args:
        data: Dictionary with RFMS-related fields
        
    Returns:
        Dictionary with RFMS fields converted to uppercase
    """
    # Common RFMS fields that should be uppercase
    rfms_fields = [
        'order_number', 'orderNumber', 'order_number',
        'purchase_order_number', 'purchaseOrderNumber', 'po_number', 'poNumber',
        'qr_number', 'qrNumber', 'quote_number', 'quoteNumber',
        'supplier_name', 'supplierName',
        'customer_name', 'customerName', 'customer_name',
        'first_name', 'firstName', 'first_name',
        'last_name', 'lastName', 'surname',
        'business_name', 'businessName',
        'address1', 'address2', 'address_1', 'address_2',
        'city', 'suburb', 'state',
        'postal_code', 'postalCode',
        'phone', 'phone1', 'phone2', 'mobile',
        # 'email' - excluded: email addresses should preserve case
        'salesperson', 'salesperson1', 'salesperson2',
        'contract_type', 'contractType',
        'order_type', 'orderType',
        'ad_source', 'adSource',
        'labour_service_type', 'labourServiceType',
        'product_code', 'productCode',
        'style_name', 'styleName',
        'color_name', 'colorName',
        'supplier_name', 'supplierName',
        'packing_slip_number', 'packingSlipNumber',
        'tracking_number', 'trackingNumber',
        'enquiry_number', 'enquiryNumber'
    ]
    
    return uppercase_text_fields(data, rfms_fields)

