"""
Australian Postcode Lookup Utility
Loads and searches Australian postcodes from CSV file.
"""
import csv
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the CSV file
CSV_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'australian_postcodes.csv')

# In-memory cache for postcodes
_postcode_cache: Optional[List[Dict]] = None


def load_postcodes() -> List[Dict]:
    """
    Load postcodes from CSV file into memory.
    Returns list of dictionaries with postcode, locality (suburb), and state.
    """
    global _postcode_cache
    
    if _postcode_cache is not None:
        return _postcode_cache
    
    _postcode_cache = []
    
    if not os.path.exists(CSV_FILE_PATH):
        logger.warning(f"Postcode CSV file not found at {CSV_FILE_PATH}")
        return _postcode_cache
    
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Extract relevant fields: postcode, locality (suburb), state
                postcode = row.get('postcode', '').strip()
                locality = row.get('locality', '').strip()
                state = row.get('state', '').strip()
                
                # Skip empty rows
                if not postcode or not locality or not state:
                    continue
                
                _postcode_cache.append({
                    'postcode': postcode,
                    'suburb': locality,
                    'state': state
                })
        
        logger.info(f"Loaded {len(_postcode_cache)} postcodes from CSV")
    except Exception as e:
        logger.error(f"Error loading postcodes CSV: {str(e)}")
        _postcode_cache = []
    
    return _postcode_cache


def search_suburbs(query: str, limit: int = 10) -> List[Dict]:
    """
    Search for suburbs matching the query string.
    
    Args:
        query: Search query (suburb name, case-insensitive partial match)
        limit: Maximum number of results to return
    
    Returns:
        List of dictionaries with postcode, suburb, and state
    """
    if not query or len(query) < 2:
        return []
    
    postcodes = load_postcodes()
    query_lower = query.lower().strip()
    
    # Filter suburbs that match the query
    matches = []
    seen = set()  # Track unique suburb+postcode combinations
    
    for entry in postcodes:
        suburb_lower = entry['suburb'].lower()
        
        # Check if query matches suburb name (starts with or contains)
        if suburb_lower.startswith(query_lower) or query_lower in suburb_lower:
            # Create a unique key for suburb+postcode+state combination
            key = (entry['suburb'].lower(), entry['postcode'], entry['state'])
            if key not in seen:
                seen.add(key)
                matches.append(entry)
    
    # Sort by relevance (exact matches first, then by suburb name)
    matches.sort(key=lambda x: (
        0 if x['suburb'].lower().startswith(query_lower) else 1,
        x['suburb'].lower()
    ))
    
    return matches[:limit]


def get_suburb_details(suburb: str, state: Optional[str] = None, postcode: Optional[str] = None) -> Optional[Dict]:
    """
    Get details for a specific suburb.
    If multiple matches exist, returns the first one.
    
    Args:
        suburb: Suburb name
        state: Optional state filter
        postcode: Optional postcode filter
    
    Returns:
        Dictionary with postcode, suburb, and state, or None if not found
    """
    if not suburb:
        return None
    
    postcodes = load_postcodes()
    suburb_lower = suburb.lower().strip()
    
    for entry in postcodes:
        if entry['suburb'].lower() == suburb_lower:
            # If state is provided, match it
            if state and entry['state'].upper() != state.upper():
                continue
            # If postcode is provided, match it
            if postcode and entry['postcode'] != postcode:
                continue
            
            return entry
    
    return None


def reload_postcodes():
    """Reload postcodes from CSV file (clears cache)."""
    global _postcode_cache
    _postcode_cache = None
    return load_postcodes()

