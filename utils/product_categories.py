"""
Product category codes and descriptions for RFMS system.

These are product category codes (not specific SKU codes) used for:
- Product type detection (Roll Stock vs Items)
- UI display and categorization
- Purchase order matching
- Consignment note and invoice cross-checking
- AP record creation
"""

PRODUCT_CATEGORIES = {
    "01": "CARPET",
    "1": "CARPET",
    "02": "VINYL",
    "2": "VINYL",
    "03": "HYBRID",
    "3": "HYBRID",
    "04": "TIMBER",
    "4": "TIMBER",
    "05": "LAMINATE",
    "5": "LAMINATE",
    "06": "VINYL PLANKS",
    "6": "VINYL PLANKS",
    "07": "VINYL TILES",
    "7": "VINYL TILES",
    "08": "CARPET TILES",
    "8": "CARPET TILES",
    "09": "UNDERLAYS",
    "9": "UNDERLAYS",
    "10": "NOSINGS & TRIMS",
    "11": "ACCESSORIES",
    "12": "COMMERCIAL VINYL"
}

# Roll Stock products (measured in linear meters, received as rolls)
ROLL_STOCK_CODES = ["01", "1"]

# Items/Pallet Stock products (measured in square meters, received as boxes/pallets)
ITEMS_CODES = ["02", "2", "03", "3", "04", "4", "05", "5", "06", "6", "07", "7", 
               "08", "8", "09", "9", "10", "11", "12"]

# Scotia/Trim/Accessory products (may require dual line assessment)
SCOTIA_TRIM_CODES = ["10", "11"]  # NOSINGS & TRIMS, ACCESSORIES

# Products that start with "8" (80-89) are typically installation/labor/removal services
# But "08" is CARPET TILES which is an item
INSTALLATION_SERVICE_CODES = ["80", "81", "82", "83", "84", "85", "86", "87", "88", "89"]


def get_category_description(product_code: str) -> str:
    """
    Get the product category description for a product code.
    
    Args:
        product_code: The product code (e.g., "01", "1", "02", etc.)
        
    Returns:
        Category description or "Unknown" if not found
    """
    if not product_code:
        return "Unknown"
    
    # Normalize product code (remove leading zeros if present, but keep original format)
    code = str(product_code).strip()
    
    # Try exact match first
    if code in PRODUCT_CATEGORIES:
        return PRODUCT_CATEGORIES[code]
    
    # Try with leading zero
    if len(code) == 1:
        code_with_zero = "0" + code
        if code_with_zero in PRODUCT_CATEGORIES:
            return PRODUCT_CATEGORIES[code_with_zero]
    
    # Try without leading zero
    if len(code) == 2 and code.startswith("0"):
        code_without_zero = code[1:]
        if code_without_zero in PRODUCT_CATEGORIES:
            return PRODUCT_CATEGORIES[code_without_zero]
    
    return "Unknown"


def is_roll_stock(product_code: str) -> bool:
    """
    Check if a product code represents Roll Stock (carpet).
    
    Args:
        product_code: The product code to check
        
    Returns:
        True if Roll Stock, False otherwise
    """
    if not product_code:
        return False
    
    code = str(product_code).strip()
    
    # Check exact match
    if code in ROLL_STOCK_CODES:
        return True
    
    # Check with/without leading zero
    if len(code) == 1 and code == "1":
        return True
    if len(code) == 2 and code == "01":
        return True
    
    return False


def is_item(product_code: str) -> bool:
    """
    Check if a product code represents an Item (pallet stock).
    
    Args:
        product_code: The product code to check
        
    Returns:
        True if Item, False otherwise
    """
    if not product_code:
        return False
    
    code = str(product_code).strip()
    
    # Normalize code
    if len(code) == 1:
        code = "0" + code
    
    # Check if it's in items codes (but not roll stock)
    if code in ITEMS_CODES and not is_roll_stock(code):
        return True
    
    return False


def is_scotia_trim(product_code: str, description: str = "", style_name: str = "") -> bool:
    """
    Check if a product is a scotia/trim/accessory.
    
    Args:
        product_code: The product code to check
        description: Product description (optional, for additional matching)
        style_name: Style name (optional, for additional matching)
        
    Returns:
        True if scotia/trim/accessory, False otherwise
    """
    if not product_code:
        return False
    
    code = str(product_code).strip()
    
    # Normalize code
    if len(code) == 1:
        code = "0" + code
    
    # Check category codes
    if code in SCOTIA_TRIM_CODES:
        return True
    
    # Check installation service codes (80-89) - these might be scotias/trims in some contexts
    if code in INSTALLATION_SERVICE_CODES:
        # But check description to be sure
        desc_lower = (description or "").lower()
        style_lower = (style_name or "").lower()
        if any(keyword in desc_lower or keyword in style_lower 
               for keyword in ["scotia", "trim", "accessory", "nosing"]):
            return True
    
    # Check description and style name for keywords
    desc_lower = (description or "").lower()
    style_lower = (style_name or "").lower()
    if any(keyword in desc_lower or keyword in style_lower 
           for keyword in ["scotia", "trim", "accessory", "nosing"]):
        return True
    
    return False


def get_product_type(product_code: str, description: str = "", style_name: str = "") -> str:
    """
    Get the product type classification.
    
    Args:
        product_code: The product code
        description: Product description (optional)
        style_name: Style name (optional)
        
    Returns:
        "roll_stock", "item", "scotia_trim", or "unknown"
    """
    if is_scotia_trim(product_code, description, style_name):
        return "scotia_trim"
    elif is_roll_stock(product_code):
        return "roll_stock"
    elif is_item(product_code):
        return "item"
    else:
        return "unknown"

