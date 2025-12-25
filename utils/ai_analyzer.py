from google import genai
from google.api_core import retry
import json
import pathlib
from dataclasses import dataclass
from typing import Optional, Dict
from google.genai import types
from bs4 import BeautifulSoup
import os
import time
import logging

logger = logging.getLogger(__name__)


# Catch transient Gemini errors
# Distinguish between rate limiting (retryable) and quota exhaustion (not retryable)
def is_retryable(e) -> bool:
    # Use built-in transient error detection first
    if retry.if_transient_error(e):
        return True
    
    # Check for quota exhaustion (RESOURCE_EXHAUSTED) - DO NOT retry these
    error_str = str(e).lower()
    is_quota_exhausted = (
        "resource_exhausted" in error_str or
        "quota exceeded" in error_str or
        "quota limit" in error_str
    )
    if is_quota_exhausted:
        return False  # Don't retry quota exhaustion
    
    # Rate limiting 429s (too many requests per second) ARE retryable with backoff
    # Quota exhaustion is different from rate limiting
    if isinstance(e, genai.errors.ClientError) and hasattr(e, 'code') and e.code == 429:
        # Check if it's rate limiting (retryable) vs quota exhaustion (not retryable)
        # If error message doesn't mention quota/resource_exhausted, it's likely rate limiting
        if not is_quota_exhausted:
            return True  # Rate limiting - retry with backoff
    
    # Server errors like 503 are retryable
    elif (isinstance(e, genai.errors.ServerError) and hasattr(e, 'code') and e.code == 503):
        return True
    
        return False


@dataclass
class AIProcessingResult:
    po_number: str
    job_description: str
    main_contacts: list
    job_address: Dict
    model_used: str
    amount: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    job_summary: Optional[str] = None
    email_contact: Optional[Dict] = None
    is_provisional: Optional[bool] = None
    notes: Optional[str] = None
    raw_response: Optional[dict] = None


class DocumentAnalyzer:
    """Analyzer for both Purchase Orders and Quotations"""
    
    def __init__(self):
        """Initialize the analyzer with Google AI credentials"""
        # Set the API key before creating the client
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Initialize the client with the API key
        self.client = genai.Client(api_key=api_key)
        
        # Get model from environment or use default
        self.model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
        
    @retry.Retry(
        predicate=is_retryable,
        initial=1.0,
        maximum=30.0,  # Reduced from 60.0 to fail faster
        multiplier=2.0,
        timeout=60.0  # Reduced from 120.0 to 60 seconds total timeout
    )
    def _generate_content(self, file_content, prompt):
        """Wrapper method for generate_content with retry logic"""
        start_time = time.time()
        try:
            response = self.client.models.generate_content(
            model=self.model,
            contents=[file_content, prompt],
            config={
                "response_mime_type": "application/json",
            }
        )
            elapsed = time.time() - start_time
            logger.info(f"AI API call completed in {elapsed:.2f} seconds")
            return response
        except Exception as e:
            elapsed = time.time() - start_time
            # Check for quota exhaustion specifically (different from rate limiting)
            error_str = str(e).lower()
            is_quota_exhausted = (
                "resource_exhausted" in error_str or 
                "quota exceeded" in error_str or
                "quota limit" in error_str
            )
            
            # Check if it's a 429 but distinguish rate limiting from quota exhaustion
            is_429 = (
                "429" in str(e) or
                (isinstance(e, genai.errors.ClientError) and hasattr(e, 'code') and e.code == 429)
            )
            
            if is_quota_exhausted:
                logger.error(f"AI API quota exhausted after {elapsed:.2f} seconds - NOT retrying")
            elif is_429 and not is_quota_exhausted:
                logger.warning(f"AI API rate limited (429) after {elapsed:.2f} seconds - will retry with backoff: {e}")
            else:
                logger.warning(f"AI API call failed after {elapsed:.2f} seconds: {e}")
            raise

    def analyze_document(self, pdf_path: str, content: str = None, email_body: str = None, document_type: str = "purchase_order") -> AIProcessingResult:
        """
        Analyze a document (PO or Quote) and extract relevant information
        
        Args:
            pdf_path: Path to the PDF file
            content: The content of the online order if it exists
            email_body: Email body text for extracting sender info
            document_type: Either "purchase_order" or "quotation"
            
        Returns:
            AIProcessingResult containing extracted information and metadata
        """
    
        content = None
        if pdf_path:
            read_start = time.time()
            # Read the file and determine MIME type
            pdf_path = pathlib.Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"File not found: {pdf_path}")
            
            # Validate file type - reject .msg files (emails must be parsed separately)
            file_ext = pdf_path.suffix.lower()
            if file_ext == '.msg':
                raise ValueError(
                    f"Email files (.msg) cannot be processed as documents. "
                    f"Email files should be parsed first and email_body passed to analyze_document() instead."
                )
            
            # Get file size for logging
            file_size = pdf_path.stat().st_size
            logger.info(f"Reading file: {pdf_path.name} ({file_size:,} bytes, type: {file_ext})")
            
            # Determine MIME type based on file extension
            if file_ext in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif file_ext == '.png':
                mime_type = 'image/png'
            elif file_ext == '.pdf':
                mime_type = 'application/pdf'
            else:
                # Warn about unknown extension but allow it (in case of edge cases)
                logger.warning(f"Unknown file extension '{file_ext}', defaulting to 'application/pdf'")
                mime_type = 'application/pdf'
            
            # Read file bytes
            file_bytes = pdf_path.read_bytes()
            read_elapsed = time.time() - read_start
            logger.info(f"File read completed in {read_elapsed:.2f} seconds")
                
            content = types.Part.from_bytes(
                data=file_bytes,
                mime_type=mime_type,
            )
        
        # Clean HTML from email body if present
        if email_body:
            # Ensure email_body is a string (it might be bytes)
            if isinstance(email_body, bytes):
                try:
                    email_body = email_body.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        email_body = email_body.decode('latin-1')
                    except UnicodeDecodeError:
                        email_body = email_body.decode('utf-8', errors='replace')
            
            # Ensure it's a string for string operations
            email_body = str(email_body) if not isinstance(email_body, str) else email_body
            
            if '<html' in email_body.lower() or '<body' in email_body.lower():
                soup = BeautifulSoup(email_body, 'html.parser')
                email_body = soup.get_text()
                # Remove extra whitespace and clean up
                email_body = '\n'.join(line.strip() for line in email_body.split('\n') if line.strip())
        
        # Determine the appropriate field name based on document type
        if document_type == "purchase_order":
            number_field = "po_number"
            number_description = "purchase order number (sometimes referred to as order number/contract number)"
        elif document_type == "quotation":
            number_field = "qr_number"
            number_description = "quotation reference number or quote number"
        elif document_type == "customer_enquiry":
            number_field = "enquiry_number"
            number_description = "enquiry number or reference if found, otherwise null"
        else:
            number_field = "po_number"
            number_description = "purchase order number (sometimes referred to as order number/contract number)"
        
        # Build prompt based on whether we have a document or just email
        if content:
            # We have a document to analyze
            prompt_intro = f"""
        Extract and return ONLY a JSON object with these exact fields from the document content:
        """
        else:
            # Email-only analysis - focus on extracting customer info from email body and signature
            prompt_intro = f"""
        Extract and return ONLY a JSON object with these exact fields from the email body and signature below.
        Focus on extracting customer contact details from the email signature, reply-to address, and any dimensions/requirements mentioned in the email body:
        """
        
        prompt = prompt_intro + f"""
        {{
            "{number_field}": "the complete {number_description} if found, preserving ALL prefixes (like 'QR', 'PO', etc.) and ALL suffixes (like '-002', '-001', etc.). For example, 'QR113126-DQ01-002' should be returned as 'QR113126-DQ01-002', not '113126-DQ01'. Extract the FULL reference number exactly as it appears, including any letters and numbers at the beginning and end. If found in the email body or attached document, null if not found",
            "job_description": "any job description, dimensions, flooring requirements, or work details mentioned in the email body. Extract what the customer is requesting (e.g., room measurements, flooring type, area descriptions). Use line breaks <br> for newlines instead of \\n. If nothing is mentioned, return null",
            "job_address": "address where the actual job needs to be done, null if not found". Should be 
            in the form e.g. : {{
                        "address1": "12 Adelaide Tce",
                        "address2": "",
                        "city": "Perth",
                        "state": "WA",
                        "postalCode": "6000"
                    }},
            "main_contacts": [{{
                "first_name": "main contact's first name, null if not found",
                "last_name": "main contact's last name, null if not found",
                "emails": "main contact's email address, null if not found",
                "phone": "main contact's landline phone number, null if not found",
                "mobile": "main contact's mobile phone number, null if not found",
                "title": "eg Main contact, Job Contact, Site Manager, Owner etc, whatever the document refers to them as. Shouldn't be blank so if it's not clear who they are then use Job Contact"
            }},...],
            "amount": "the total amount for the document if specified (excluding GST), null if not found. For customer enquiry forms: if no clear total amount is written, use '1.00' as default. If amount includes GST, calculate the amount excluding GST (divide by 1.1 for 10% GST)",
            "start_date": "the start date/commencement date/measure date etc of the job if specified in form yyyy-mm-dd, null if not found"
            "end_date": "the end date/completion date etc of the job if specified in form yyyy-mm-dd, null if not found",
            "job_summary": "Brief summary of what needs to be done",
            "email_contact":{{
                    "first_name": "first name of the contact, null if not found", 
                    "last_name": "last name of the contact, null if not found", 
                    "emails": "email address of the contact, null if not found",
                    "phone": "phone number of the contact, null if not found",
                    "mobile": "mobile number of the contact, null if not found", 
                    "title": "title of the contact, null if not found"
                }},
            "is_provisional": "whether the words 'pc allowance' are present anywhere (case insensitive). returns true or false",
            "notes": "any additional notes, comments, or special instructions from the document. For customer enquiry forms, include all handwritten notes and comments. Use line breaks <br> for newlines instead of \\n"
        }}
        Only return the JSON object, no other text. The description should be as is, not 
        paraphrased or summarised, with focus being on the actual work that needs to be done.
        Leave out anything that seems like disclaimers/agreements. No need to follow the newlines as they appear in document but 
        make it well structured with newlines and paragraphs that make sense.
        If there are subheadings ensure they are included.
        Be very careful to ensure the main_contacts and address are correct. 
        Take extra care about the amount. It should be the total that's excluding the GST, sometimes referred to as subtotal.
        If there are multiple phone or mobile numbers for a contact then include them in the respective field separated by / e.g. 0432234675/0453672123. But don't list same number twice
        If there are no contacts then return empty main_contacts list. If there are multiple contacts, 
        always ensure the first one in the list is whoever appears to be the owner or otherwise in charge at the site.
        Never include any reference to costings, payments or $ amounts in the description.
        Sometimes the data is in a table. Carefully analyse the table and don't let it confuse you. If a column/s is critical to the job description then include its detail
        Be very careful with {number_field} as sometimes it's not clearly labeled.
        If there are multiple candidates for the number that are similar, best to pick the longer version that isn't 'job number'.
        CRITICAL: Preserve the COMPLETE {number_field} including ALL prefixes (e.g., 'QR', 'PO', 'WO') and ALL suffixes (e.g., '-002', '-001', '-A', '-DQ01'). 
        For example, if you see 'QR113126-DQ01-002', extract it as 'QR113126-DQ01-002' NOT '113126-DQ01' or 'QR113126'.
        Also check the filename of the document if it contains the {number_field} (e.g., 'QR113126-DQ01-002.pdf').
        If the document is clearly not a {document_type.replace('_', ' ')}, return empty strings/dicts/list depending on the key.
        Sometimes amount is not clearly labelled. Analyse carefully and derive it if possible, otherwise set it to null.
        address1 in job_address is Primary street address (street number, street name, main identifier). address2 is for 
        Secondary address details - unit/suite numbers, building names, floor numbers, or overflow from address1 if too long)
        The email_contact comes from the email body. Find their details in the email signature. Extract name, email, phone, mobile from the signature.
        
        Email body to analyze:
        {email_body if email_body else 'N/A'}
        
        {'For email-only analysis: Focus on extracting customer contact information from the email signature. Look for name, phone numbers, email addresses, and any business details. Also extract any dimensions, flooring requirements, or job details mentioned in the email body.' if not content else ''}
        """
        
        try:
            analysis_start = time.time()
            logger.info(f"Starting AI analysis for document_type={document_type}, has_content={content is not None}, has_email_body={bool(email_body)}")
            
            # Validate we have exactly one source of content
            if content and email_body:
                logger.warning("Both content and email_body provided - using content (document) and ignoring email_body")
            elif not content and not email_body:
                raise ValueError("Either pdf_path or email_body must be provided")
            
            # Analyse content (if we have a document) or email body only
            if content:
                # We have a document to analyze (PDF or image)
                file_size = len(content._raw_bytes) if hasattr(content, '_raw_bytes') else 'unknown'
                logger.info(f"Analyzing document (size: {file_size} bytes)")
                response = self._generate_content(content, prompt)
            elif email_body:
                # Email-only analysis - pass email body as text content
                email_size = len(email_body)
                logger.info(f"Analyzing email body (size: {email_size} characters)")
                # Create a Part object from text - use text parameter instead of from_text method
                email_content = types.Part(text=email_body)
                response = self._generate_content(email_content, prompt)
            
            analysis_elapsed = time.time() - analysis_start
            logger.info(f"AI analysis completed in {analysis_elapsed:.2f} seconds")
            
            # Extract the JSON response
            result = json.loads(response.text)
            logger.debug(f"AI parsed result: {json.dumps(result, indent=2)}")
            
            # Normalize the number field to po_number for consistency
            po_number = result.get(number_field) or result.get('po_number') or result.get('qr_number')
            
            # Create AIProcessingResult
            return AIProcessingResult(
                po_number=po_number,
                job_description=result.get('job_description'),
                job_address=result.get('job_address', {}),
                main_contacts=result.get('main_contacts', []),
                model_used=self.model,
                amount=result.get('amount'),
                start_date=result.get('start_date'),
                end_date=result.get('end_date'),
                job_summary=result.get('job_summary'),
                email_contact=result.get('email_contact', {}),
                is_provisional=result.get('is_provisional'),
                notes=result.get('notes'),
                raw_response=result
            )
            
        except Exception as e:
            raise Exception(f"Failed to analyze document: {str(e)}")

    def analyze_consignment_note(self, pdf_path: str) -> Dict:
        """
        Analyze a consignment note document and extract order numbers, supplier details, and stock information.
        
        Args:
            pdf_path: Path to the consignment note image/PDF
            
        Returns:
            Dict containing extracted information:
            - order_number: Our order number (e.g., AZ003325-0001)
            - purchase_order_number: Purchase order number
            - supplier_name: Supplier name
            - supplier_order_number: Supplier's order/reference number
            - stock_items: List of stock items mentioned
            - tracking_number: Tracking/consignment number
            - delivery_date: Delivery date if mentioned
        """
        pdf_path = pathlib.Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"File not found: {pdf_path}")
        
        file_ext = pdf_path.suffix.lower()
        if file_ext in ['.jpg', '.jpeg']:
            mime_type = 'image/jpeg'
        elif file_ext == '.png':
            mime_type = 'image/png'
        elif file_ext == '.pdf':
            mime_type = 'application/pdf'
        else:
            mime_type = 'application/pdf'
        
        file_bytes = pdf_path.read_bytes()
        content = types.Part.from_bytes(
            data=file_bytes,
            mime_type=mime_type,
        )
        
        prompt = """
        Extract and return ONLY a JSON object with these exact fields from this consignment note document:
        {
            "order_number": "Our company's order number if found (e.g., AZ003325-0001, AZ0033250001, AZ003325, CG105159, etc.), null if not found",
            "purchase_order_number": "Purchase order number if found, null if not found",
            "supplier_name": "Name of the supplier/vendor, null if not found",
            "supplier_order_number": "Supplier's order number or reference number, null if not found",
            "packing_slip_number": "Packing slip number, supplier invoice reference, or supplier reference number (may start with SI-, INV, INV-, SALES INVOICE I..., SALES INVOICE-PSI..., or just be a number/string). This is the reference number the supplier uses on their invoice. null if not found",
            "stock_items": ["List of stock/product names mentioned in the document, empty array if none"],
            "tracking_number": "Tracking number, consignment number, or waybill number, null if not found",
            "delivery_date": "Delivery date in format yyyy-mm-dd if found, null if not found",
            "quantity": "Total quantity of items if mentioned, null if not found",
            "rolls_count": "Total number of rolls (for carpet/roll stock), null if not found or not applicable",
            "boxes_count": "Total number of boxes or packs (for items/pallet stock), null if not found or not applicable",
            "total_quantity": "Total quantity supplied (could be in square meters, linear meters, or units depending on product type), null if not found",
            "notes": "Any additional notes or special instructions from the consignment note"
        }
        
        CRITICAL: Order number extraction rules:
        - Order numbers can appear in various formats:
          * Base only: AZ003463, CG105159
          * With hyphen and suffix: AZ003463-0001, AZ003463-0004
          * Joined suffix (no hyphen): AZ0034630001, AZ0034630004
        - Order numbers may appear with prefixes like "Ref:", "Reference:", "Order:", "PO:", etc.
          Example: "Ref: AZ0034630001" should extract as "AZ0034630001"
        - The order_number field is typically the same as purchase_order_number (our PO number)
        - Extract the COMPLETE order number including any suffix (0001, 0004, etc.) if present
        - Preserve the exact format found (with or without hyphen) - do not modify it
        - If you see "AZ0034630001" extract it as-is, not as "AZ003463-0001"
        - If you see "AZ003463-0001" extract it as-is, not as "AZ0034630001"
        
        Focus on extracting:
        - Order numbers that match patterns like AZ######, AZ######-####, AZ##########, CG######, or similar formats
        - Purchase order numbers (may be labeled as PO, P/O, Purchase Order, etc.) - often the same as order_number
        - Supplier information (name, contact details)
        - Stock/product names and descriptions
        - Product categories/types (CARPET, VINYL, HYBRID, TIMBER, LAMINATE, VINYL PLANKS, VINYL TILES, CARPET TILES, UNDERLAYS, NOSINGS & TRIMS, ACCESSORIES, COMMERCIAL VINYL)
        - Tracking or consignment numbers
        - Any reference numbers that could help identify the order
        
        Product Category Reference:
        - 01/CARPET: Roll stock (measured in linear meters, received as rolls)
        - 02-12: Items/pallet stock (measured in square meters, received as boxes)
        - 10/NOSINGS & TRIMS, 11/ACCESSORIES: May require dual line assessment (costing and receiving)
        
        Only return the JSON object, no other text.
        """
        
        try:
            response = self._generate_content(content, prompt)
            
            # Parse JSON response
            json_str = response.text.strip()
            # Remove markdown code blocks if present
            if json_str.startswith('```json'):
                json_str = json_str[7:]
            if json_str.startswith('```'):
                json_str = json_str[3:]
            if json_str.endswith('```'):
                json_str = json_str[:-3]
            json_str = json_str.strip()
            
            result = json.loads(json_str)
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from consignment note analysis: {e}")
            logger.error(f"Response text: {response.text[:500] if 'response' in locals() else 'No response'}")
            return {
                "order_number": None,
                "purchase_order_number": None,
                "supplier_name": None,
                "supplier_order_number": None,
                "stock_items": [],
                "tracking_number": None,
                "delivery_date": None,
                "quantity": None,
                "notes": None
            }
        except Exception as e:
            logger.error(f"Error analyzing consignment note: {e}", exc_info=True)
            return {
                "order_number": None,
                "purchase_order_number": None,
                "supplier_name": None,
                "supplier_order_number": None,
                "stock_items": [],
                "tracking_number": None,
                "delivery_date": None,
                "quantity": None,
                "notes": None
            }
    
    def analyze_supplier_invoice(self, pdf_path: str) -> Dict:
        """
        Analyze a supplier invoice PDF to extract invoice details, line items, and charges.
        
        Args:
            pdf_path: Path to the invoice PDF file
            
        Returns:
            Dictionary with invoice data including:
            - invoice_number: Invoice number
            - supplier_name: Supplier name
            - invoice_date: Invoice date
            - due_date: Due date (if available)
            - order_number: Order number or PO number referenced
            - po_number: Purchase order number
            - line_items: List of line items with product, quantity, price
            - subtotal: Subtotal amount
            - freight: Freight charges
            - baling_handling: Baling and handling charges
            - supplier_discount: Supplier discount amount
            - tax: Tax amount (if applicable)
            - total: Total invoice amount
            - other_charges: Dictionary of other charges
        """
        try:
            file_path = pathlib.Path(pdf_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Invoice file not found: {pdf_path}")
            
            # Read file
            file_bytes = file_path.read_bytes()
            mime_type = "application/pdf"
            
            # Upload file to Gemini
            file = self.client.files.upload(
                data=file_bytes,
                mime_type=mime_type,
            )
            
            content = types.Part.from_uri(
                file_uri=file.uri,
                mime_type=mime_type,
            )
            
            prompt = """
        Extract and return ONLY a JSON object with these exact fields from this supplier invoice document:
        {
            "invoice_number": "Invoice number from the invoice, null if not found",
            "supplier_name": "Name of the supplier/vendor, null if not found",
            "invoice_date": "Invoice date in format yyyy-mm-dd if found, null if not found",
            "due_date": "Due date in format yyyy-mm-dd if found, null if not found",
            "order_number": "Order number or PO number referenced on invoice (e.g., AZ003463-0001, AZ0034630001, CG105159), null if not found",
            "po_number": "Purchase order number if different from order_number, null if not found",
            "line_items": [
                {
                    "product_name": "Product name or description",
                    "product_code": "Product code or SKU if available",
                    "quantity": "Quantity (number)",
                    "unit_price": "Unit price (number)",
                    "total": "Line total (number)"
                }
            ],
            "subtotal": "Subtotal amount before charges (number), null if not found",
            "freight": "Freight or shipping charges (number), null if not found",
            "baling_handling": "Baling and/or handling charges (number), null if not found",
            "supplier_discount": "Supplier discount amount (number), null if not found",
            "tax": "Tax amount (number), null if not found",
            "total": "Total invoice amount (number), null if not found",
            "other_charges": {
                "charge_name": "charge_amount"
            }
        }
        
        CRITICAL extraction rules:
        - Extract ALL charges separately: freight, baling, handling, discounts, surcharges, etc.
        - Look for charges labeled as: "Freight", "Shipping", "Delivery", "Baling", "Handling", "Baling/Handling", "Discount", "Surcharge", etc.
        - Extract order numbers in various formats (with/without hyphens, with suffixes)
        - Extract line items with product names, quantities, and prices
        - Convert all amounts to numbers (remove currency symbols, commas)
        - If a charge is not found, set it to null (not 0)
        
        Product categories to identify:
        - CARPET (roll stock)
        - VINYL, HYBRID, TIMBER, LAMINATE (items/pallet stock)
        - NOSINGS & TRIMS, ACCESSORIES (may require dual line assessment)
        - UNDERLAYS
        
        Only return the JSON object, no other text.
        """
            
            try:
                response = self._generate_content(content, prompt)
                
                # Parse JSON response
                json_str = response.text.strip()
                # Remove markdown code blocks if present
                if json_str.startswith('```json'):
                    json_str = json_str[7:]
                if json_str.startswith('```'):
                    json_str = json_str[3:]
                if json_str.endswith('```'):
                    json_str = json_str[:-3]
                json_str = json_str.strip()
                
                result = json.loads(json_str)
                
                # Ensure numeric fields are properly converted
                numeric_fields = ['subtotal', 'freight', 'baling_handling', 'supplier_discount', 'tax', 'total']
                for field in numeric_fields:
                    if field in result and result[field] is not None:
                        try:
                            if isinstance(result[field], str):
                                result[field] = float(result[field].replace('$', '').replace(',', '').strip())
                            else:
                                result[field] = float(result[field])
                        except:
                            result[field] = None
                
                # Ensure line_items have proper numeric fields
                if 'line_items' in result and isinstance(result['line_items'], list):
                    for item in result['line_items']:
                        for field in ['quantity', 'unit_price', 'total']:
                            if field in item and item[field] is not None:
                                try:
                                    if isinstance(item[field], str):
                                        item[field] = float(item[field].replace('$', '').replace(',', '').strip())
                                    else:
                                        item[field] = float(item[field])
                                except:
                                    item[field] = None
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from invoice analysis: {e}")
                logger.error(f"Response text: {response.text[:500] if 'response' in locals() else 'No response'}")
                return self._default_invoice_result()
            except Exception as e:
                logger.error(f"Error analyzing invoice: {e}", exc_info=True)
                return self._default_invoice_result()
                
        except Exception as e:
            logger.error(f"Error processing invoice file: {e}", exc_info=True)
            return self._default_invoice_result()
    
    def _default_invoice_result(self) -> Dict:
        """Return default empty invoice result structure"""
        return {
            "invoice_number": None,
            "supplier_name": None,
            "invoice_date": None,
            "due_date": None,
            "order_number": None,
            "po_number": None,
            "line_items": [],
            "subtotal": None,
            "freight": None,
            "baling_handling": None,
            "supplier_discount": None,
            "tax": None,
            "total": None,
            "other_charges": {}
        }

