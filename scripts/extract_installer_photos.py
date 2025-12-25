#!/usr/bin/env python3
"""
Extract Installer Photos from RFMS Order and Compile into Compressed PDF

This script:
1. Retrieves an order from RFMS by order number
2. Filters attachments tagged as "INSTALLER PHOTOS"
3. Downloads and compresses the photo attachments
4. Compiles them into a single compressed PDF file

Usage:
    python scripts/extract_installer_photos.py <ORDER_NUMBER>

Example:
    python scripts/extract_installer_photos.py P1BW-1828
"""

import sys
import os
import base64
import tempfile
import shutil
import json
from pathlib import Path
from typing import List, Dict
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.rfms_client import RFMSClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    logger.error("Pillow (PIL) is not installed. Please install it with: pip install Pillow")
    PIL_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    logger.warning("reportlab is not installed. Will attempt to use PyPDF2/pymupdf instead.")
    REPORTLAB_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


def filter_installer_photos(attachments: List[Dict]) -> List[Dict]:
    """
    Filter attachments to only include those tagged as "INSTALLER PHOTOS".
    
    Args:
        attachments: List of attachment dictionaries from RFMS
        
    Returns:
        List of filtered attachments
    """
    installer_photos = []
    
    # Log sample attachment structure for debugging
    if attachments:
        sample_attachment = attachments[0]
        logger.debug(f"Sample attachment structure: {list(sample_attachment.keys())}")
        logger.debug(f"Sample attachment: {json.dumps({k: str(v)[:100] for k, v in sample_attachment.items()}, indent=2)}")
    
    for attachment in attachments:
        # Check various possible fields for the tag
        description = str(attachment.get('description', '') or '').upper()
        tag = str(attachment.get('tag', '') or '').upper()
        attachment_type = str(attachment.get('type', '') or '').upper()
        
        # Also check other possible fields
        name = str(attachment.get('name', '') or '').upper()
        title = str(attachment.get('title', '') or '').upper()
        category = str(attachment.get('category', '') or '').upper()
        
        # Check if any field contains "INSTALLER PHOTOS" or similar
        search_fields = {
            'description': description,
            'tag': tag,
            'type': attachment_type,
            'name': name,
            'title': title,
            'category': category
        }
        
        found = False
        for field_name, field_value in search_fields.items():
            if 'INSTALLER PHOTOS' in field_value or 'INSTALLER PHOTO' in field_value:
                logger.info(f"Found installer photo in {field_name}: {field_value}")
                installer_photos.append(attachment)
                found = True
                break
        
        # Also check exact match
        if not found:
            if (description.strip() == 'INSTALLER PHOTOS' or 
                tag.strip() == 'INSTALLER PHOTOS' or
                name.strip() == 'INSTALLER PHOTOS' or
                title.strip() == 'INSTALLER PHOTOS'):
                installer_photos.append(attachment)
                logger.info(f"Found installer photo (exact match): {description or tag or name or title}")
    
    logger.info(f"Found {len(installer_photos)} installer photo attachments out of {len(attachments)} total attachments")
    
    # If no installer photos found, log some sample descriptions to help debug
    if not installer_photos and attachments:
        logger.info("Sample attachment descriptions/types:")
        for i, att in enumerate(attachments[:5]):  # Show first 5
            desc = att.get('description', 'N/A')
            att_type = att.get('type', 'N/A')
            tag = att.get('tag', 'N/A')
            name = att.get('name', 'N/A')
            logger.info(f"  Attachment {i+1}: description='{desc}', type='{att_type}', tag='{tag}', name='{name}'")
    
    return installer_photos


def download_attachment(rfms_client: RFMSClient, attachment: Dict, output_dir: Path) -> Path:
    """
    Download an attachment from RFMS and save it to disk.
    
    Args:
        rfms_client: RFMS client instance
        attachment: Attachment dictionary with ID
        output_dir: Directory to save the file
        
    Returns:
        Path to the downloaded file
    """
    attachment_id = (attachment.get('id') or 
                    attachment.get('attachmentId') or 
                    attachment.get('attachment_id'))
    if not attachment_id:
        raise ValueError(f"Attachment missing ID: {attachment}")
    
    logger.info(f"Downloading attachment {attachment_id}...")
    attachment_data = rfms_client.get_attachment(attachment_id)
    
    # Debug: log response type and structure
    logger.debug(f"Attachment data type: {type(attachment_data)}")
    if isinstance(attachment_data, dict):
        logger.debug(f"Attachment data keys: {list(attachment_data.keys())}")
    
    # Handle different response structures
    file_data_b64 = None
    
    if isinstance(attachment_data, dict):
        # Check if detail is a string (base64 data directly)
        detail = attachment_data.get('detail')
        if isinstance(detail, str):
            # Detail contains base64 string directly
            file_data_b64 = detail
        elif isinstance(detail, dict):
            # Detail is a dict, extract file data from it
            file_data_b64 = detail.get('fileData') or detail.get('data') or detail.get('file')
        
        # If not found yet, check other locations
        if not file_data_b64:
            file_data_b64 = (attachment_data.get('fileData') or 
                            attachment_data.get('data') or
                            attachment_data.get('file'))
        
        # Also check if the whole response is in result
        if not file_data_b64:
            result = attachment_data.get('result')
            if isinstance(result, str) and result != 'OK':
                # Result might be base64 string
                file_data_b64 = result
            elif isinstance(result, dict):
                file_data_b64 = result.get('fileData') or result.get('data') or result.get('file')
    
    elif isinstance(attachment_data, str):
        # If response is directly a base64 string, use it
        file_data_b64 = attachment_data
    
    if not file_data_b64:
        logger.error(f"Attachment {attachment_id} response: {str(attachment_data)[:500]}")
        raise ValueError(f"Attachment {attachment_id} has no file data. Response type: {type(attachment_data)}")
    
    # Decode base64 data
    try:
        file_bytes = base64.b64decode(file_data_b64)
    except Exception as e:
        logger.error(f"Failed to decode attachment {attachment_id}: {e}")
        raise
    
    # Determine file extension
    file_extension = (attachment_data.get('fileExtension') or 
                     attachment.get('fileExtension') or
                     attachment_data.get('extension', 'jpg'))
    if not file_extension.startswith('.'):
        file_extension = '.' + file_extension
    
    # Save file
    filename = f"attachment_{attachment_id}{file_extension}"
    file_path = output_dir / filename
    with open(file_path, 'wb') as f:
        f.write(file_bytes)
    
    logger.info(f"Saved attachment to {file_path} ({len(file_bytes):,} bytes)")
    return file_path


def compress_image(image_path: Path, max_size: tuple = (1920, 1920), quality: int = 75) -> Path:
    """
    Compress an image file.
    
    Args:
        image_path: Path to the image file
        max_size: Maximum dimensions (width, height) for the compressed image
        quality: JPEG quality (1-100) for output
        
    Returns:
        Path to the compressed image
    """
    if not PIL_AVAILABLE:
        logger.warning("Pillow not available, skipping compression")
        return image_path
    
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if necessary
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save compressed version
            compressed_path = image_path.parent / f"compressed_{image_path.name}"
            img.save(compressed_path, 'JPEG', quality=quality, optimize=True)
            
            original_size = image_path.stat().st_size
            compressed_size = compressed_path.stat().st_size
            logger.info(f"Compressed {image_path.name}: {original_size:,} bytes -> {compressed_size:,} bytes "
                       f"({compressed_size/original_size*100:.1f}%)")
            
            return compressed_path
    except Exception as e:
        logger.error(f"Failed to compress {image_path}: {e}")
        return image_path


def create_pdf_from_images(image_paths: List[Path], output_pdf_path: Path) -> Path:
    """
    Create a PDF file from a list of image paths.
    
    Args:
        image_paths: List of paths to image files
        output_pdf_path: Path for the output PDF
        
    Returns:
        Path to the created PDF
    """
    if not image_paths:
        raise ValueError("No images to compile into PDF")
    
    if REPORTLAB_AVAILABLE:
        return _create_pdf_reportlab(image_paths, output_pdf_path)
    elif PYMUPDF_AVAILABLE:
        return _create_pdf_pymupdf(image_paths, output_pdf_path)
    else:
        raise ImportError("Neither reportlab nor PyMuPDF available. Please install one: pip install reportlab or pip install pymupdf")


def _create_pdf_reportlab(image_paths: List[Path], output_pdf_path: Path) -> Path:
    """Create PDF using reportlab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    
    c = canvas.Canvas(str(output_pdf_path), pagesize=letter)
    page_width, page_height = letter
    
    for img_path in image_paths:
        try:
            # Open image to get dimensions
            img = Image.open(img_path)
            img_width, img_height = img.size
            
            # Calculate scaling to fit page
            scale_x = page_width / img_width
            scale_y = page_height / img_height
            scale = min(scale_x, scale_y)
            
            # Calculate centered position
            scaled_width = img_width * scale
            scaled_height = img_height * scale
            x = (page_width - scaled_width) / 2
            y = (page_height - scaled_height) / 2
            
            # Draw image
            c.drawImage(ImageReader(img), x, y, width=scaled_width, height=scaled_height)
            c.showPage()
        except Exception as e:
            logger.error(f"Failed to add image {img_path} to PDF: {e}")
            continue
    
    c.save()
    logger.info(f"Created PDF with {len(image_paths)} images: {output_pdf_path}")
    return output_pdf_path


def _create_pdf_pymupdf(image_paths: List[Path], output_pdf_path: Path) -> Path:
    """Create PDF using PyMuPDF (fitz)."""
    doc = fitz.open()
    
    for img_path in image_paths:
        try:
            # Open image
            img = Image.open(img_path)
            img_width, img_height = img.size
            
            # Create a page (A4 size)
            page = doc.new_page(width=img_width, height=img_height)
            
            # Insert image
            page.insert_image(fitz.Rect(0, 0, img_width, img_height), filename=str(img_path))
        except Exception as e:
            logger.error(f"Failed to add image {img_path} to PDF: {e}")
            continue
    
    doc.save(str(output_pdf_path))
    doc.close()
    logger.info(f"Created PDF with {len(image_paths)} images: {output_pdf_path}")
    return output_pdf_path


def main():
    """Main function to extract installer photos and create PDF."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    order_number = sys.argv[1]
    
    if not PIL_AVAILABLE:
        logger.error("Pillow (PIL) is required for image compression. Install with: pip install Pillow")
        sys.exit(1)
    
    # Initialize RFMS client
    try:
        # Check if credentials are set
        store_code = os.getenv('RFMS_STORE_CODE')
        api_key = os.getenv('RFMS_API_KEY')
        
        if not store_code or not api_key:
            logger.error("RFMS credentials not found in environment variables.")
            logger.error("Please ensure RFMS_STORE_CODE and RFMS_API_KEY are set in your .env file or environment.")
            sys.exit(1)
        
        logger.info("Initializing RFMS client...")
        rfms_client = RFMSClient()
        rfms_client.start_session()
        logger.info("RFMS client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RFMS client: {e}")
        logger.error("Make sure your .env file contains valid RFMS credentials")
        sys.exit(1)
    
    # Create temporary directory for downloaded files
    temp_dir = Path(tempfile.mkdtemp(prefix=f"installer_photos_{order_number}_"))
    logger.info(f"Working directory: {temp_dir}")
    
    try:
        # Get order details
        logger.info(f"Retrieving order {order_number}...")
        order_data = rfms_client.get_order(order_number, locked=False, include_attachments=True)
        
        # Debug: log the order data structure
        logger.debug(f"Order data type: {type(order_data)}")
        if isinstance(order_data, dict):
            logger.debug(f"Order data keys: {list(order_data.keys())}")
        
        # Extract attachments - handle different response structures
        attachments = []
        if isinstance(order_data, dict):
            # Check various possible locations for attachments
            detail = order_data.get('detail')
            data = order_data.get('data')
            result = order_data.get('result')
            
            # Log structure for debugging
            logger.debug(f"Checking for attachments in order_data keys: {list(order_data.keys())}")
            if isinstance(result, dict):
                logger.debug(f"Result keys: {list(result.keys())}")
            if isinstance(detail, dict):
                logger.debug(f"Detail keys: {list(detail.keys())}")
            
            attachments = (order_data.get('attachments') or 
                          (result.get('attachments') if isinstance(result, dict) else None) or
                          (detail.get('attachments') if isinstance(detail, dict) else None) or
                          (data.get('attachments') if isinstance(data, dict) else None) or
                          [])
            
            # Also try checking nested structures
            if not attachments and isinstance(result, dict):
                attachments = result.get('attachments') or result.get('order', {}).get('attachments') or []
            if not attachments and isinstance(detail, dict):
                attachments = detail.get('attachments') or detail.get('order', {}).get('attachments') or []
            if not attachments and isinstance(data, dict):
                attachments = data.get('attachments') or data.get('order', {}).get('attachments') or []
        
        logger.info(f"Found {len(attachments)} total attachments")
        
        if not attachments:
            logger.warning(f"No attachments found for order {order_number}")
            # Log more detailed structure for debugging
            if isinstance(order_data, dict):
                result = order_data.get('result')
                if isinstance(result, dict):
                    logger.info(f"Order result structure (first 1000 chars): {json.dumps(result, indent=2, default=str)[:1000]}")
                else:
                    logger.info(f"Order data structure: {json.dumps({k: str(type(v)) for k, v in order_data.items()}, indent=2)}")
            else:
                logger.info(f"Order data type: {type(order_data)}")
            sys.exit(0)
        
        logger.info(f"Found {len(attachments)} total attachments")
        
        # Filter installer photos
        installer_photos = filter_installer_photos(attachments)
        if not installer_photos:
            logger.warning(f"No 'INSTALLER PHOTOS' attachments found for order {order_number}")
            sys.exit(0)
        
        # Download attachments
        logger.info(f"Downloading {len(installer_photos)} installer photo attachments...")
        downloaded_files = []
        for attachment in installer_photos:
            try:
                file_path = download_attachment(rfms_client, attachment, temp_dir)
                downloaded_files.append(file_path)
            except Exception as e:
                logger.error(f"Failed to download attachment {attachment.get('id')}: {e}")
                continue
        
        if not downloaded_files:
            logger.error("No attachments were successfully downloaded")
            sys.exit(1)
        
        # Compress images
        logger.info("Compressing images...")
        compressed_files = []
        for file_path in downloaded_files:
            try:
                compressed_path = compress_image(file_path)
                compressed_files.append(compressed_path)
            except Exception as e:
                logger.warning(f"Failed to compress {file_path}: {e}, using original")
                compressed_files.append(file_path)
        
        # Create PDF
        output_pdf = Path.cwd() / f"{order_number}_installer_photos.pdf"
        logger.info(f"Creating PDF from {len(compressed_files)} images...")
        try:
            create_pdf_from_images(compressed_files, output_pdf)
            logger.info(f"Successfully created PDF: {output_pdf}")
            print(f"\nPDF created successfully: {output_pdf}")
        except Exception as e:
            logger.error(f"Failed to create PDF: {e}")
            sys.exit(1)
    
    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
            logger.debug(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary directory: {e}")


if __name__ == '__main__':
    main()

