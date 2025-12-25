"""
Supplier Folder Mapping Utility

Maps supplier names from consignment notes to email folder names
based on the SUPPLIERS FOLDERS.MD file.
"""

import os
import re
import logging
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def load_supplier_folders() -> List[str]:
    """
    Load supplier folder names from SUPPLIERS FOLDERS.MD file.
    
    Returns:
        List of supplier folder names
    """
    suppliers_file = Path(__file__).parent.parent / "SUPPLIERS FOLDERS.MD"
    
    if not suppliers_file.exists():
        logger.warning(f"SUPPLIERS FOLDERS.MD not found at {suppliers_file}")
        return []
    
    suppliers = []
    try:
        with open(suppliers_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines, comments, and special markers
                if line and not line.startswith('#') and not line.startswith('>'):
                    # Clean up the line (remove extra spaces, etc.)
                    cleaned = ' '.join(line.split())
                    if cleaned:
                        suppliers.append(cleaned)
        
        logger.info(f"Loaded {len(suppliers)} supplier folders from SUPPLIERS FOLDERS.MD")
        return suppliers
        
    except Exception as e:
        logger.error(f"Error loading supplier folders: {e}", exc_info=True)
        return []


def match_supplier_to_folders(supplier_name: str, supplier_folders: List[str] = None) -> List[str]:
    """
    Match a supplier name to folder names (full or partial match).
    
    Args:
        supplier_name: Supplier name from consignment note
        supplier_folders: List of supplier folder names (if None, loads from file)
        
    Returns:
        List of matching folder names (can be multiple matches)
    """
    if not supplier_name:
        return []
    
    if supplier_folders is None:
        supplier_folders = load_supplier_folders()
    
    if not supplier_folders:
        return []
    
    supplier_name_lower = supplier_name.lower().strip()
    matches = []
    
    # Try exact match first
    for folder in supplier_folders:
        folder_lower = folder.lower().strip()
        
        # Exact match
        if supplier_name_lower == folder_lower:
            matches.append(folder)
            continue
        
        # Check if supplier name is contained in folder name
        if supplier_name_lower in folder_lower:
            matches.append(folder)
            continue
        
        # Check if folder name is contained in supplier name
        if folder_lower in supplier_name_lower:
            matches.append(folder)
            continue
        
        # Check for word-by-word matching (handle cases like "Big Panda Flooring" matching "Big Panda")
        supplier_words = set(supplier_name_lower.split())
        folder_words = set(folder_lower.split())
        
        # If at least 2 words match, consider it a match
        common_words = supplier_words.intersection(folder_words)
        if len(common_words) >= 2:
            matches.append(folder)
            continue
        
        # Check for partial word matches (e.g., "A1 RUBBER" matching "A1")
        # Split on common separators
        supplier_parts = set(re.split(r'[\s\-_/]+', supplier_name_lower))
        folder_parts = set(re.split(r'[\s\-_/]+', folder_lower))
        
        if supplier_parts.intersection(folder_parts):
            matches.append(folder)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_matches = []
    for match in matches:
        if match not in seen:
            seen.add(match)
            unique_matches.append(match)
    
    if unique_matches:
        logger.info(f"Matched supplier '{supplier_name}' to folders: {unique_matches}")
    
    return unique_matches


def get_supplier_folder_paths(supplier_name: str) -> List[str]:
    """
    Get full folder paths for a supplier (e.g., "Suppliers/Big Panda Flooring").
    
    Args:
        supplier_name: Supplier name from consignment note
        
    Returns:
        List of folder paths to search (e.g., ["Suppliers/Big Panda Flooring"])
    """
    matched_folders = match_supplier_to_folders(supplier_name)
    
    # Convert to full paths under "Suppliers" section
    folder_paths = []
    for folder in matched_folders:
        # Handle nested folders (e.g., "NFD - National Flooring Distributors > Overlocking")
        if '>' in folder:
            parts = [p.strip() for p in folder.split('>')]
            # Create path like "Suppliers/NFD - National Flooring Distributors/Overlocking"
            path = "Suppliers/" + "/".join(parts)
        else:
            path = f"Suppliers/{folder}"
        
        folder_paths.append(path)
    
    return folder_paths

