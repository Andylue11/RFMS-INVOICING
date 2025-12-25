"""
Utility functions for normalizing and parsing order numbers.

Handles various formats of order numbers:
- AZ003463 (base order number)
- AZ003463-0001 (with hyphen and suffix)
- AZ0034630001 (joined suffix, no hyphen)
- Ref: AZ0034630001 (with reference prefix)
"""
import re
import logging

logger = logging.getLogger(__name__)


def normalize_order_number(order_number: str) -> dict:
    """
    Normalize an order number and extract its components.
    
    Handles formats like:
    - AZ003463 (base only)
    - AZ003463-0001 (with hyphen and suffix)
    - AZ0034630001 (joined suffix)
    - Ref: AZ0034630001 (with reference prefix)
    - AZ0034630004 (different suffix)
    
    Args:
        order_number: The order number string to normalize
        
    Returns:
        Dict with keys:
            - base: Base order number (e.g., "AZ003463")
            - suffix: Suffix if present (e.g., "0001", "0004"), None if not found
            - full: Full normalized order number with hyphen (e.g., "AZ003463-0001")
            - full_joined: Full order number without hyphen (e.g., "AZ0034630001")
            - original: Original input string
    """
    if not order_number:
        return {
            'base': None,
            'suffix': None,
            'full': None,
            'full_joined': None,
            'original': None
        }
    
    original = str(order_number).strip()
    
    # Remove common prefixes like "Ref:", "Reference:", "Order:", etc.
    cleaned = re.sub(r'^(ref|reference|order|po|p/o|purchase\s*order)[:\s]+', 
                     '', original, flags=re.IGNORECASE).strip()
    
    # Remove any whitespace
    cleaned = re.sub(r'\s+', '', cleaned)
    
    # Pattern to match order numbers:
    # - Starts with 2-3 letters (AZ, CG, ST, etc.)
    # - Followed by 5-6 digits (base number - ST orders use 5 digits, others use 6)
    # - Optionally followed by a hyphen and 4 digits (suffix)
    # - OR optionally followed directly by 4 digits (joined suffix)
    
    # Special handling for #ST orders (ST + 5 digits, e.g., ST00536)
    if cleaned.upper().startswith('ST') and len(cleaned) >= 7:
        # ST orders: ST + 5 digits (e.g., ST00536)
        st_pattern = re.compile(r'^(ST)(\d{5})$', re.IGNORECASE)
        match = st_pattern.match(cleaned)
        if match:
            prefix = match.group(1).upper()
            base_num = match.group(2)
            base = f"{prefix}{base_num}"
            suffix = None
            full = base
            full_joined = base
        else:
            # Try ST with # prefix
            st_hash_pattern = re.compile(r'^#?(ST)(\d{5})$', re.IGNORECASE)
            match = st_hash_pattern.match(cleaned)
            if match:
                prefix = match.group(1).upper()
                base_num = match.group(2)
                base = f"#{prefix}{base_num}"
                suffix = None
                full = base
                full_joined = base
            else:
                # If no pattern matches, return as-is
                logger.warning(f"Could not parse ST order number format: {original}")
                base = cleaned.upper()
                suffix = None
                full = base
                full_joined = base
    else:
        # Standard order numbers (AZ, CG, etc. with 6 digits)
        # Try pattern with hyphen first: AZ003463-0001
        pattern_with_hyphen = re.compile(r'^([A-Z]{2,3})(\d{6})-(\d{4})$', re.IGNORECASE)
        match = pattern_with_hyphen.match(cleaned)
        
        if match:
            prefix = match.group(1).upper()
            base_num = match.group(2)
            suffix = match.group(3)
            base = f"{prefix}{base_num}"
            full = f"{base}-{suffix}"
            full_joined = f"{base}{suffix}"
        else:
            # Try pattern without hyphen but with suffix: AZ0034630001
            pattern_joined = re.compile(r'^([A-Z]{2,3})(\d{6})(\d{4})$', re.IGNORECASE)
            match = pattern_joined.match(cleaned)
            
            if match:
                prefix = match.group(1).upper()
                base_num = match.group(2)
                suffix = match.group(3)
                base = f"{prefix}{base_num}"
                full = f"{base}-{suffix}"
                full_joined = f"{base}{suffix}"
            else:
                # Try base only: AZ003463
                pattern_base = re.compile(r'^([A-Z]{2,3})(\d{6})$', re.IGNORECASE)
                match = pattern_base.match(cleaned)
                
                if match:
                    prefix = match.group(1).upper()
                    base_num = match.group(2)
                    base = f"{prefix}{base_num}"
                    suffix = None
                    full = base
                    full_joined = base
                else:
                    # If no pattern matches, return as-is but try to extract what we can
                    # Check if it's a numeric-only order number (like 6396458)
                    if cleaned.isdigit():
                        # Numeric-only order number - return as-is
                        base = cleaned
                        suffix = None
                        full = base
                        full_joined = base
                    else:
                        logger.warning(f"Could not parse order number format: {original}")
                        base = cleaned.upper()
                        suffix = None
                        full = base
                        full_joined = base
    
    return {
        'base': base,
        'suffix': suffix,
        'full': full,
        'full_joined': full_joined,
        'original': original
    }


def get_order_number_variations(order_number: str) -> list:
    """
    Get all possible variations of an order number for searching.
    
    For example, if input is "AZ0034630001", returns:
    - AZ0034630001 (original joined)
    - AZ003463-0001 (with hyphen)
    - AZ003463 (base only)
    
    Args:
        order_number: The order number string
        
    Returns:
        List of order number variations to search for
    """
    normalized = normalize_order_number(order_number)
    variations = []
    
    if normalized['full']:
        variations.append(normalized['full'])
    
    if normalized['full_joined'] and normalized['full_joined'] != normalized['full']:
        variations.append(normalized['full_joined'])
    
    if normalized['base'] and normalized['base'] not in variations:
        variations.append(normalized['base'])
    
    # Also include original if it's different
    if normalized['original'] and normalized['original'] not in variations:
        # Only add if it looks like a valid order number
        if re.match(r'^[A-Z]{2,3}\d{6}', normalized['original'], re.IGNORECASE):
            variations.append(normalized['original'])
    
    return variations


def extract_order_number_from_text(text: str) -> list:
    """
    Extract all potential order numbers from a text string.
    
    Looks for patterns like:
    - AZ003463
    - AZ003463-0001
    - AZ0034630001
    - Ref: AZ0034630001
    
    Args:
        text: Text to search for order numbers
        
    Returns:
        List of found order number strings
    """
    if not text:
        return []
    
    # Pattern to find order numbers in text
    # Matches: 2-3 letters + 6 digits, optionally followed by -4digits or 4digits
    pattern = re.compile(
        r'\b([A-Z]{2,3}\d{6}(?:-?\d{4})?)\b',
        re.IGNORECASE
    )
    
    matches = pattern.findall(text)
    return [match.upper() for match in matches if match]

