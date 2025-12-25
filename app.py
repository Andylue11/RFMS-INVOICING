from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session, send_file, make_response, send_from_directory
from markupsafe import Markup
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta, timezone
import uuid
import base64
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict

# Import models and database
from models import db, Quote, Job, PdfData
from sqlalchemy import or_

# Import utility modules
from utils.rfms_api import RfmsApi
from utils.ai_analyzer import DocumentAnalyzer
from utils.rfms_client import RFMSClient
from utils.postcode_lookup import search_suburbs, get_suburb_details
from utils.email_parser import EmailParser
from utils.email_scraper import EmailScraper, extract_invoice_charges
from utils.email_sender import send_no_invoice_notification
from utils.text_utils import uppercase_rfms_fields

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

# App configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///instance/rfms_xtracr.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'jpg', 'jpeg', 'png', 'heic', 'heif', 'msg'}
app.config['ALLOWED_ATTACHMENT_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'heic', 'heif'}

# Favicon route (serve SVG for favicon requests)
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.svg',
        mimetype='image/svg+xml'
    )

# Ensure necessary directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('instance', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Initialize database with app
db.init_app(app)

# Add custom Jinja2 filters
@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to HTML line breaks."""
    if value is None:
        return ''
    return value.replace('\n', '<br>')

# Initialize RFMS API client
rfms_api = RfmsApi(
    base_url=os.getenv('RFMS_BASE_URL', 'https://api.rfms.online'),
    store_code=os.getenv('RFMS_STORE_CODE'),
    username=os.getenv('RFMS_USERNAME'),
    api_key=os.getenv('RFMS_API_KEY')
)

# Initialize enhanced RFMS client and AI analyzer
rfms_client = RFMSClient()

# Initialize AI analyzer only if API key is available
document_analyzer = None
try:
    if os.getenv('GEMINI_API_KEY'):
        document_analyzer = DocumentAnalyzer()
        logger.info("AI analyzer initialized successfully")
    else:
        logger.warning("GEMINI_API_KEY not found, AI features will be disabled")
except Exception as e:
    logger.warning(f"Failed to initialize AI analyzer: {e}")
    document_analyzer = None

# RFMS configuration mappings (sourced from updated RFMS CONFIG ID NUMBERS.xlsx)
CONTRACT_TYPE_DEFAULT = 'DEPOSIT & COD'
CONTRACT_TYPE_IDS = {
    'DEPOSIT & COD': 5,
    '30 DAY ACCOUNT': 1,
    '14 DAY ACCOUNT': 3,
    '7 DAY ACCOUNT': 2,
    'COD ACCOUNT': 9,
    'CREDIT CLAIM/REFUND': 15,
    'PAID IN FULL': 11,
    'REPAYMENT PLAN': 14,
}

ORDER_TYPE_DEFAULT = 'RESIDENTIAL HOME'
ORDER_TYPE_IDS = {
    'RESIDENTIAL HOME': 3,
    'BUILDER CLIENT ADD ON': 31,
    'COMMERCIAL OFFICE': 21,
    'COMMERCIAL RETAIL': 36,
    'COMMERICAL RESIDENTIAL': 23,
    'CREDIT CLAIM/REFUND': 28,
    'GOOD WILL': 26,
    'INSTALLER REPLACEMENT': 34,
    'INSTALLER S/O PURCHASE': 39,
    'MANUFACTURER REPLACEMENT': 24,
    'NEW BUILD': 2,
    'ONLINE SEBO SALE': 40,
    'RESIDENTIAL INSURANCE': 18,
    'RESIDENTIAL RENTAL': 20,
    'RESIDENTIAL TOWNHOUSE': 30,
    'RESIDENTIAL UNIT': 29,
    'RETURN TO MANUFACTURER': 38,
    'SHORT MEASURE': 25,
    'SHORT SUPPLIED ADD ON': 27,
    'SUPPLY & INSTALL': 32,
    'SUPPLY ONLY': 33,
    'WAREHOUSE STOCK SALE': 37,
    'WARRANTY FOR INSTALLER': 22,
    'WARRANTY INSPECTION': 19,
    'WARRANTY REPAIR': 16,
    'WARRANTY REPLACEMENT': 17,
    'WRITE OFF JOB': 35,
}
ORDER_TYPE_ALIASES = {
    'COMMERCIAL RESIDENTIAL': 'COMMERICAL RESIDENTIAL',
    'SHORT SUPPLIED': 'SHORT SUPPLIED ADD ON',
    'SUPPLY AND INSTALL': 'SUPPLY & INSTALL',
}
ORDER_TYPE_DISPLAY_OVERRIDES = {
    'COMMERICAL RESIDENTIAL': 'COMMERCIAL RESIDENTIAL',
    'SHORT SUPPLIED ADD ON': 'SHORT SUPPLIED ADD ON',
}

AD_SOURCE_DEFAULT = 'BUILDER CLIENT'
AD_SOURCE_IDS = {
    'BUILDER CLIENT': 5,
    'BUILDER REFERRAL': 7,
    'CLIENT REFERRAL': 3,
    'COMMUNITY LEADER ADVERTISMENT': 19,
    'ESTIMATE ONE TENDER': 18,
    'EXISTING CLIENT': 4,
    'FACEBOOK ENQUIRY': 2,
    'FAMILY REFERRAL': 11,
    'GOOGLE ENQUIRY': 1,
    'INSPIRATIONS PAINT REFERRAL': 15,
    'INSTALLER BUSINESS': 16,
    'INSTALLER REFERRAL': 10,
    'KITCHEN CONNECTIONS': 17,
    'PHONE ENQUIRY': 9,
    'SHOWROOM WALK IN': 8,
    'WEBSITE ENQUIRY': 12,
}
AD_SOURCE_ALIASES = {
    'COMMUNITY LEADER ADV': 'COMMUNITY LEADER ADVERTISMENT',
    'COMMUNITY LEADER ADVERTISEMENT': 'COMMUNITY LEADER ADVERTISMENT',
}

LABOUR_SERVICE_TYPE_DEFAULT = 'SUPPLY & INSTALL'
LABOUR_SERVICE_TYPE_IDS = {
    'SUPPLY & INSTALL': 8,
    'MIXED SERVICES': 9,
    'FLOOR PREPERATION': 2,
    'GENERAL LABOUR': 1,
    'INSTALLATION': 3,
    'MIN. CALL OUT CHARGE': 6,
    'PRODUCT ONLY RETURN': 11,
    'PRODUCT REPAIRS': 10,
    'SUPPLY ONLY': 7,
    'UPLIFT ONLY': 4,
    'FEATURE WORK': 5,
}
LABOUR_SERVICE_TYPE_ALIASES = {
    'FLOOR PREPARATION': 'FLOOR PREPERATION',
    'SUPPLY AND INSTALL': 'SUPPLY & INSTALL',
}
LABOUR_SERVICE_TYPE_DISPLAY_OVERRIDES = {
    'FLOOR PREPERATION': 'FLOOR PREPARATION',
}


def _normalize_choice(value, aliases):
    """Normalize UI input to canonical uppercase key."""
    if not value:
        return ''
    key = value.strip().upper()
    return aliases.get(key, key) if aliases else key


def _build_choice_list(mapping, display_overrides=None):
    """Return a list of dictionaries suitable for dropdown APIs."""
    items = []
    for key in mapping:
        display_name = display_overrides.get(key, key) if display_overrides else key
        items.append({'id': key, 'name': display_name})
    return items


def format_rfms_document_number(doc_number, is_quote):
    """Format RFMS document number with AQ/AZ prefix when appropriate."""
    if not doc_number:
        return None

    doc_str = str(doc_number).strip()
    if not doc_str:
        return None

    doc_upper = doc_str.upper()
    if doc_upper.startswith('AQ') or doc_upper.startswith('AZ'):
        return doc_str

    if doc_str.isdigit():
        prefix = 'AQ' if is_quote else 'AZ'
        return f"{prefix}{doc_str.zfill(4)}"

    return doc_str


def extract_rfms_document_details(rfms_result, is_quote):
    """Extract status, raw/display document numbers, and parent document from RFMS response."""
    status = None
    raw_document_number = None
    parent_document = None

    logger.info(f"Extracting RFMS document details from result: {rfms_result}")

    if isinstance(rfms_result, dict):
        status = rfms_result.get('status')
        order_info = rfms_result.get('order') or {}
        
        logger.info(f"RFMS result status: {status}, order_info keys: {order_info.keys() if isinstance(order_info, dict) else 'Not a dict'}")

        if status in ['new_order', 'billing_group_added', 'new_quote']:
            # For new documents, the document number is typically in order_info['result']
            raw_document_number = (
                order_info.get('result')
                or order_info.get('orderNumber')
                or order_info.get('documentNumber')
                or order_info.get('quoteNumber')  # Some APIs use quoteNumber
            )
            logger.info(f"New document - extracted raw_document_number: {raw_document_number}")
        elif status in ['existing_order', 'existing_quote']:
            # For existing documents, check multiple possible fields
            raw_document_number = (
                order_info.get('documentNumber')
                or order_info.get('result')
                or order_info.get('orderNumber')
                or order_info.get('quoteNumber')
            )
            logger.info(f"Existing document - extracted raw_document_number: {raw_document_number}")
        else:
            # Fallback: try to extract from top level if status is unexpected
            logger.warning(f"Unexpected status '{status}', attempting to extract document number from top level")
            raw_document_number = (
                rfms_result.get('result')
                or rfms_result.get('orderNumber')
                or rfms_result.get('documentNumber')
                or rfms_result.get('quoteNumber')
            )

        if status == 'billing_group_added':
            parent_order = rfms_result.get('parent_order') or {}
            parent_document = (
                parent_order.get('documentNumber')
                or parent_order.get('result')
                or parent_order.get('orderNumber')
                or parent_order.get('quoteNumber')
            )
            logger.info(f"Billing group - parent_document: {parent_document}")

    display_document_number = (
        format_rfms_document_number(raw_document_number, is_quote)
        if raw_document_number
        else None
    )
    
    logger.info(f"Final extraction result - status: {status}, raw: {raw_document_number}, display: {display_document_number}")

    return {
        'status': status,
        'raw_document_number': raw_document_number,
        'display_document_number': display_document_number,
        'parent_document': parent_document,
    }


# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def allowed_attachment(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_ATTACHMENT_EXTENSIONS']

# Routes
@app.route('/')
def index():
    """Render the main dashboard page."""
    # Calculate stats
    processed_uploads = PdfData.query.filter_by(processed=True).count()
    quotes_created = Quote.query.count()
    jobs_created = Job.query.count()
    
    stats = {
        'processed_uploads': processed_uploads,
        'quotes_created': quotes_created,
        'jobs_created': jobs_created
    }
    
    return render_template('index.html', stats=stats)

@app.route('/upload', methods=['POST'])
def upload_pdf():
    """Handle PDF upload and AI-powered extraction."""
    if 'pdf_file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    
    file = request.files['pdf_file']
    document_type_raw = request.form.get('document_type', 'purchase_order')  # Get document type from form
    
    # Normalize document types: map email types to their base types
    document_type = document_type_raw.strip().lower() if document_type_raw else 'purchase_order'
    if document_type == 'email_quotation':
        document_type = 'quotation'  # Email MSG to Quote -> creates a quote
    elif document_type == 'email_order':
        document_type = 'purchase_order'  # Email Msg to Order -> creates an order
    # Keep other types as-is: purchase_order, quotation, customer_enquiry
    
    # Get configuration settings from form and convert to uppercase
    salesperson = request.form.get('salesperson', 'STEVE WHYTE').upper()
    contract_type = request.form.get('contractType', 'DEPOSIT & COD').upper()
    order_type = request.form.get('orderType', 'RESIDENTIAL HOME').upper()
    ad_source = request.form.get('adSource', 'BUILDER CLIENT').upper()
    date_type = request.form.get('dateType', 'estimated').lower()  # Keep lowercase for date type
    required_date = request.form.get('requiredDate', '')
    labour_service_type = request.form.get('labourServiceType', 'SUPPLY & INSTALL').upper()
    
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Check if this is an email (.msg) file
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            is_email = file_ext == 'msg'
            
            # Validate file extension is supported
            if file_ext and file_ext not in ['msg', 'pdf', 'jpg', 'jpeg', 'png']:
                logger.warning(f"Unexpected file extension '{file_ext}' for file {filename}")
            
            email_body = ""
            email_data = {}
            saved_attachments = []
            email_attachments = []
            
            if is_email:
                logger.info(f"Detected email file (.msg): {filename}")
                # Parse email file
                logger.info(f"Processing email file: {filename}")
                email_parser = EmailParser(file_path)
                email_data = email_parser.parse()
                
                email_body = email_data.get('email_body', '') or email_data.get('body_text', '')
                
                # Extract email attachments to a separate directory
                email_attachments_dir = os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    'email_attachments',
                    str(uuid.uuid4())
                )
                os.makedirs(email_attachments_dir, exist_ok=True)
                
                # Extract and save attachments
                pdf_attachment_path = None
                try:
                    saved_attachments = email_parser.extract_attachments(email_attachments_dir)
                    
                    # Store attachment paths relative to app root for later upload
                    for attachment in saved_attachments:
                        email_attachments.append({
                            'original_filename': attachment['original_filename'],
                            'stored_filename': attachment['stored_filename'],
                            'path': os.path.relpath(attachment['path'], app.root_path)
                        })
                        
                        # Look for PDF attachments to extract ship-to data from
                        if not pdf_attachment_path:
                            att_path = attachment['path']
                            att_ext = os.path.splitext(att_path)[1].lower()
                            if att_ext == '.pdf' and os.path.exists(att_path):
                                pdf_attachment_path = att_path
                                logger.info(f"Found PDF attachment for analysis: {attachment['original_filename']}")
                    
                    logger.info(f"Extracted {len(saved_attachments)} attachments from email")
                except Exception as e:
                    logger.warning(f"Failed to extract email attachments: {str(e)}")
                
                # Use reply-to email or sender email for customer lookup
                reply_email = email_data.get('reply_to_email') or email_data.get('sender_email', '')
                
            # Use AI to extract data from PDF or email if available
            if document_analyzer is None:
                return jsonify({"error": "AI analyzer not available. Please check GEMINI_API_KEY configuration."}), 500
                
            logger.info(f"Processing {filename} as {document_type} (is_email={is_email})")
            
            # For email files, analyze the email body and signature to extract customer details
            # For PDF files, analyze the document
            if is_email:
                # Try to analyze attached PDF first for ship-to data (customer name, address, etc.)
                # Fall back to email body/signature if PDF can't be read or isn't available
                pdf_result = None
                pdf_filename_number = None
                if pdf_attachment_path:
                    try:
                        # Extract potential QR/PO number from PDF filename (e.g., "QR113126-DQ01-002.pdf")
                        pdf_filename = os.path.basename(pdf_attachment_path)
                        pdf_basename = os.path.splitext(pdf_filename)[0]  # Remove extension
                        logger.info(f"PDF filename: {pdf_basename}")
                        
                        # Check if filename looks like it contains a QR/PO number
                        # Patterns like: QR123456-DQ01-002, PO123456-001, etc.
                        import re
                        number_patterns = [
                            r'^([A-Z]{1,4}\d+-[A-Z0-9]+(?:-\d+)?)',  # QR113126-DQ01-002, PO123-001
                            r'([A-Z]{1,4}\d{4,}[A-Z0-9\-]+)',  # Any alphanumeric pattern
                        ]
                        for pattern in number_patterns:
                            match = re.match(pattern, pdf_basename, re.IGNORECASE)
                            if match:
                                pdf_filename_number = match.group(1).upper()
                                logger.info(f"Extracted number from PDF filename: {pdf_filename_number}")
                                break
                        
                        logger.info(f"Attempting to analyze PDF attachment: {pdf_attachment_path}")
                        pdf_result = document_analyzer.analyze_document(
                            pdf_path=pdf_attachment_path,
                            email_body=None,  # Don't use email body when we have PDF
                            document_type=document_type
                        )
                        
                        # If no number was extracted from PDF content, use filename number as fallback
                        if pdf_result and not pdf_result.po_number and pdf_filename_number:
                            pdf_result.po_number = pdf_filename_number
                            logger.info(f"Using number from PDF filename as fallback: {pdf_filename_number}")
                        
                        logger.info("Successfully analyzed PDF attachment for ship-to data")
                    except Exception as e:
                        logger.warning(f"Failed to analyze PDF attachment (will use email body as fallback): {str(e)}")
                        pdf_result = None
                
                # Analyze email body and signature using AI (fallback if no PDF or if PDF failed)
                # This extracts email contact info and any details from email signature
                email_result = document_analyzer.analyze_document(
                    pdf_path=None,  # No PDF for email body analysis
                    email_body=email_body,  # Email body for signature analysis
                    document_type=document_type
                )
                
                # Merge results: prioritize PDF data for ship-to, use email for email contact
                if pdf_result:
                    # Use PDF data for ship-to information (main_contacts, job_address, etc.)
                    # Use email_result for email_contact
                    ai_result = pdf_result
                    # Copy email_contact from email_result if available
                    if hasattr(email_result, 'email_contact') and email_result.email_contact:
                        ai_result.email_contact = email_result.email_contact
                    logger.info("Using PDF attachment data for ship-to information, email body for email contact")
                else:
                    # Fallback: use email body analysis only
                    ai_result = email_result
                    # If we have a PDF filename number but no number was extracted from email, use filename number
                    if pdf_filename_number and not ai_result.po_number:
                        ai_result.po_number = pdf_filename_number
                        logger.info(f"Using number from PDF filename as fallback: {pdf_filename_number}")
                    logger.info("Using email body/signature data (PDF attachment not available or failed to process)")
            else:
                # Analyze PDF/image document (not an email)
                logger.info(f"Detected document file ({file_ext}): {filename}")
                # Validate it's not accidentally an email file
                if file_ext == 'msg':
                    raise ValueError("Email files must be processed through email parsing logic")
                ai_result = document_analyzer.analyze_document(
                    pdf_path=file_path,
                    email_body="",  # No email body for direct uploads
                    document_type=document_type
                )
            
            # Calculate dates (similar to AWS Lambda logic)
            # Measure date: today + 5 days
            measure_date = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d")
            
            # Estimated delivery date: use end_date if present, otherwise today + 21 days
            if ai_result.end_date:
                estimated_delivery_date = ai_result.end_date
            else:
                estimated_delivery_date = (datetime.now(timezone.utc) + timedelta(days=21)).strftime("%Y-%m-%d")
            
            # Convert AI result to dictionary format
            # Handle different document types for number field
            # Note: AIProcessingResult only has po_number, which is used for all document types
            number_field = ai_result.po_number or ''
            
            # Handle dollar amount with special logic for customer enquiry
            dollar_value = 1.0  # Default for customer enquiry
            if ai_result.amount:
                try:
                    amount_str = ai_result.amount.replace('$', '').replace(',', '')
                    dollar_value = float(amount_str)
                except (ValueError, AttributeError):
                    dollar_value = 1.0
            elif document_type != "customer_enquiry":
                dollar_value = 1.0
            
            # Extract supervisor and customer contact info from main_contacts
            supervisor_name = ''
            supervisor_phone = ''
            supervisor_mobile = ''
            customer_phone = ''
            customer_mobile = ''
            customer_email = ''
            customer_first_name = ''
            customer_last_name = ''
            
            main_contacts = ai_result.main_contacts or []
            if main_contacts:
                # Find supervisor contact (look for titles like "Supervisor", "Site Manager", etc.)
                supervisor_keywords = ['supervisor', 'super', 'site manager', 'site mgr', 'foreman', 'foreperson']
                supervisor_contact = None
                
                for contact in main_contacts:
                    title = (contact.get('title') or '').lower()
                    if any(keyword in title for keyword in supervisor_keywords):
                        supervisor_contact = contact
                        break
                
                # Extract supervisor info if found
                if supervisor_contact:
                    supervisor_name = f"{supervisor_contact.get('first_name', '')} {supervisor_contact.get('last_name', '')}".strip()
                    supervisor_phone = supervisor_contact.get('phone', '') or ''
                    supervisor_mobile = supervisor_contact.get('mobile', '') or ''
                
                # Extract customer contact info from first contact (or first non-supervisor contact)
                customer_contact = None
                if supervisor_contact and len(main_contacts) > 1:
                    # Use second contact if first is supervisor
                    customer_contact = main_contacts[1] if len(main_contacts) > 1 else main_contacts[0]
                else:
                    # Use first contact
                    customer_contact = main_contacts[0] if main_contacts else None
                
                if customer_contact:
                    customer_first_name = customer_contact.get('first_name', '') or ''
                    customer_last_name = customer_contact.get('last_name', '') or ''
                    customer_phone = customer_contact.get('phone', '') or ''
                    customer_mobile = customer_contact.get('mobile', '') or ''
                    customer_email = customer_contact.get('emails', '') or ''
            
            # Also check email_contact for customer info (prioritize over main_contacts if available)
            email_contact = ai_result.email_contact or {}
            if email_contact:
                if not customer_first_name:
                    customer_first_name = email_contact.get('first_name', '') or ''
                if not customer_last_name:
                    customer_last_name = email_contact.get('last_name', '') or ''
                if not customer_phone:
                    customer_phone = email_contact.get('phone', '') or ''
                if not customer_mobile:
                    customer_mobile = email_contact.get('mobile', '') or ''
                if not customer_email:
                    customer_email = email_contact.get('emails', '') or ''
            
            extracted_data = {
                'po_number': number_field,
                'customer_name': '',
                'business_name': '',
                'scope_of_work': ai_result.job_description or '',
                'dollar_value': dollar_value,
                'first_name': customer_first_name,
                'last_name': customer_last_name,
                'address1': ai_result.job_address.get('address1', '') if ai_result.job_address else '',
                'address2': ai_result.job_address.get('address2', '') if ai_result.job_address else '',
                'city': ai_result.job_address.get('city', '') if ai_result.job_address else '',
                'state': ai_result.job_address.get('state', '') if ai_result.job_address else '',
                'postal_code': ai_result.job_address.get('postalCode', '') if ai_result.job_address else '',
                'phone': customer_phone,
                'mobile': customer_mobile,
                'email': customer_email,
                'measure_date': measure_date,
                'estimated_delivery_date': estimated_delivery_date,
                'supervisor_name': supervisor_name,
                'supervisor_phone': supervisor_phone,
                'supervisor_mobile': supervisor_mobile,
                'description_of_works': ai_result.job_description or '',
                'builder_type': 'AI Processed',
                'document_type': document_type,
                'is_provisional': ai_result.is_provisional or False,
                'job_summary': ai_result.job_summary or '',
                'main_contacts': main_contacts,
                'email_contact': email_contact,
                'ai_model': ai_result.model_used,
                'notes': ai_result.notes or '',
                'salesperson': salesperson,
                'contract_type': contract_type,
                'order_type': order_type,
                'ad_source': ad_source,
                'date_type': date_type,
                'required_date': required_date,
                'labour_service_type': labour_service_type,
                'customer_type': 'BUILDERS'  # PDF uploads default to BUILDERS
            }
            
            # For email files, prioritize email sender/reply-to information
            if is_email:
                # Extract from email signature using AI email_contact if available
                email_contact = ai_result.email_contact or {}
                sender_name = email_data.get('sender_name', '')
                sender_email = email_data.get('sender_email', '')
                reply_email = email_data.get('reply_to_email', '') or sender_email
                reply_to_name = email_data.get('reply_to_name', '')  # Name from forwarded email body
                
                # Prioritize reply-to name from body (for forwarded emails) since it's likely the actual customer
                # Then try AI-extracted contact info, then sender info
                if reply_to_name:
                    # Parse reply-to name from forwarded email (this is the actual customer)
                    name_parts = reply_to_name.split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = ' '.join(name_parts[1:])
                    else:
                        first_name = reply_to_name
                        last_name = ''
                    logger.info(f"Using reply-to name from forwarded email body: {reply_to_name} <{reply_email}>")
                elif email_contact.get('first_name') or email_contact.get('last_name'):
                    first_name = email_contact.get('first_name', '')
                    last_name = email_contact.get('last_name', '')
                elif sender_name:
                    # Parse sender name if available
                    name_parts = sender_name.split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = ' '.join(name_parts[1:])
                    else:
                        first_name = sender_name
                        last_name = ''
                else:
                    # Fallback: try to extract from email address
                    if reply_email and '@' in reply_email:
                        first_name = reply_email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
                        last_name = ''
                    else:
                        first_name = ''
                        last_name = ''
                
                # Use AI-extracted contacts for additional info, but prioritize email contact
                # Preserve already-extracted supervisor fields
                if ai_result.main_contacts and len(ai_result.main_contacts) > 0:
                    main_contact = ai_result.main_contacts[0]
                    # Merge AI-extracted info with email contact info, but preserve supervisor fields
                    extracted_data['first_name'] = first_name or main_contact.get('first_name', '') or extracted_data.get('first_name', '')
                    extracted_data['last_name'] = last_name or main_contact.get('last_name', '') or extracted_data.get('last_name', '')
                    # Use email contact, then main_contact, then already-extracted value
                    extracted_data['phone'] = email_contact.get('phone', '') or main_contact.get('phone', '') or extracted_data.get('phone', '')
                    extracted_data['mobile'] = email_contact.get('mobile', '') or main_contact.get('mobile', '') or extracted_data.get('mobile', '')
                    extracted_data['email'] = email_contact.get('emails', '') or main_contact.get('emails', '') or reply_email or extracted_data.get('email', '')
                else:
                    # Preserve already-extracted values if they exist
                    extracted_data['first_name'] = first_name or extracted_data.get('first_name', '')
                    extracted_data['last_name'] = last_name or extracted_data.get('last_name', '')
                    extracted_data['email'] = email_contact.get('emails', '') or reply_email or extracted_data.get('email', '')
                    extracted_data['phone'] = email_contact.get('phone', '') or extracted_data.get('phone', '')
                    extracted_data['mobile'] = email_contact.get('mobile', '') or extracted_data.get('mobile', '')
                
                extracted_data['customer_name'] = f"{extracted_data['first_name']} {extracted_data['last_name']}".strip() or reply_to_name or sender_name or (reply_email.split('@')[0] if reply_email and '@' in reply_email else '')
                
                # Add email metadata to extracted_data
                extracted_data['email_subject'] = email_data.get('subject', '')
                extracted_data['email_sender'] = email_data.get('sender_email', '')
                extracted_data['email_reply_to'] = email_data.get('reply_to_email', '')
                extracted_data['email_reply_to_name'] = reply_to_name  # Name from forwarded email body
                extracted_data['email_date'] = email_data.get('date', '')
                extracted_data['email_attachments'] = email_attachments  # Save attachment paths
                
                # Combine email body with notes
                if email_body:
                    if extracted_data.get('notes'):
                        extracted_data['notes'] = f"Email Body:\n{email_body}\n\n{extracted_data['notes']}"
                    else:
                        extracted_data['notes'] = f"Email Body:\n{email_body}"
                
                # For emails, default customer type to RESIDENTIAL (email requests from clients)
                extracted_data['customer_type'] = 'RESIDENTIAL'
            else:
                # Extract main contact info if available (for PDF uploads)
                if ai_result.main_contacts and len(ai_result.main_contacts) > 0:
                    main_contact = ai_result.main_contacts[0]
                    extracted_data['first_name'] = main_contact.get('first_name', '')
                    extracted_data['last_name'] = main_contact.get('last_name', '')
                    extracted_data['phone'] = main_contact.get('phone', '')
                    extracted_data['mobile'] = main_contact.get('mobile', '')
                    extracted_data['email'] = main_contact.get('emails', '')
                    extracted_data['customer_name'] = f"{main_contact.get('first_name', '')} {main_contact.get('last_name', '')}".strip()
            
            # Save extracted data to session for preview
            session['extracted_data'] = extracted_data
            if is_email:
                # For emails, save the .msg file path and email attachments info
                session['file_path'] = file_path
                session['email_attachments'] = email_attachments
            else:
                # For PDFs, save the file path for later attachment
                session['file_path'] = file_path
            
            # Save to database for persistence
            pdf_data = PdfData(
                filename=filename,
                customer_name=extracted_data.get('customer_name', ''),
                business_name=extracted_data.get('business_name', ''),
                po_number=extracted_data.get('po_number', ''),
                scope_of_work=extracted_data.get('scope_of_work', ''),
                dollar_value=extracted_data.get('dollar_value', 0),
                extracted_data=extracted_data,
                notes=extracted_data.get('notes', ''),
                created_at=datetime.now()
            )
            
            db.session.add(pdf_data)
            db.session.commit()
            
            logger.info(f"Successfully processed {filename} with AI, redirecting to preview")
            return redirect(url_for('preview_data', pdf_id=pdf_data.id))
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error extracting data from PDF: {error_msg}", exc_info=True)
            
            # Check if this is a Gemini API quota error
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                user_friendly_msg = (
                    "<strong>The AI processing service has reached its usage limit.</strong><br><br>"
                    "Please try one of the following:<br>"
                    "• Use the 'Manual Customer Enquiry' form to enter the information manually<br>"
                    "• Wait a few minutes and try again<br>"
                    "• Contact your administrator to upgrade the Gemini API quota"
                )
                flash(Markup(user_friendly_msg), 'danger')
            elif "GEMINI_API_KEY" in error_msg or "API key" in error_msg.lower():
                flash("AI processing is not configured. Please use the 'Manual Customer Enquiry' form instead.", 'danger')
            else:
                # Generic error message for other issues
                flash(f"Error processing document: {error_msg[:200]}", 'danger')
            
            return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a PDF or JPEG image.')
    return redirect(url_for('index'))

@app.route('/preview/<int:pdf_id>')
def preview_data(pdf_id):
    """Preview extracted data before creating quote/job."""
    pdf_data = PdfData.query.get_or_404(pdf_id)
    return render_template('preview.html', pdf_data=pdf_data)

@app.route('/history')
def history():
    """Display all processed jobs with filtering and search capabilities."""
    return render_template('history.html')

@app.route('/api/history/search')
def history_search():
    """API endpoint for searching/filtering history."""
    # Get filter parameter
    doc_filter = request.args.get('filter', 'all')
    search_query = request.args.get('search', '').strip()
    
    # Base query for processed items
    query = PdfData.query.filter_by(processed=True)
    
    # Get all items first, then filter in Python for JSON field
    all_items = query.order_by(PdfData.created_at.desc()).all()
    
    # Apply document type filter in Python (since SQLite JSON querying is limited)
    if doc_filter == 'quotes':
        all_items = [item for item in all_items 
                     if item.extracted_data and item.extracted_data.get('document_type') in ['quotation', 'customer_enquiry']]
    elif doc_filter == 'workorders':
        all_items = [item for item in all_items 
                     if item.extracted_data and item.extracted_data.get('document_type') in ['purchase_order', 'work_order']]
    
    # Apply search filter across multiple fields in Python
    if search_query:
        search_lower = search_query.lower()
        filtered_items = []
        for item in all_items:
            # Check if search term matches any field
            if (
                (item.po_number and search_lower in item.po_number.lower()) or
                (item.customer_name and search_lower in item.customer_name.lower()) or
                (item.business_name and search_lower in item.business_name.lower()) or
                (item.filename and search_lower in item.filename.lower()) or
                (item.rfms_document_number and search_lower in item.rfms_document_number.lower()) or
                (item.scope_of_work and search_lower in item.scope_of_work.lower())
            ):
                filtered_items.append(item)
        all_items = filtered_items
    
    # Convert to JSON-serializable format
    results = []
    for item in all_items:
        doc_type = item.extracted_data.get('document_type', 'unknown') if item.extracted_data else 'unknown'
        results.append({
            'id': item.id,
            'po_number': item.po_number or 'N/A',
            'document_type': doc_type,
            'customer_name': item.customer_name,
            'business_name': item.business_name,
            'rfms_document_number': item.rfms_document_number,
            'rfms_status': item.rfms_status,
            'dollar_value': item.dollar_value,
            'filename': item.filename,
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M') if item.created_at else ''
        })
    
    return jsonify({
        'success': True,
        'count': len(results),
        'items': results
    })

@app.route('/api/customers/search')
def search_customers():
    """Search for customers in RFMS API."""
    search_term = request.args.get('term', '')
    customer_type = request.args.get('type', 'all')  # 'all', 'builder', 'customer'
    
    if not search_term:
        logger.warning("Empty search term provided")
        return jsonify({"error": "Search term is required"}), 400
    
    try:
        logger.info(f"Searching for {customer_type} customers with term: {search_term}")
        result = rfms_api.find_customers(search_term)
        
        # Log the raw result for debugging
        if result:
            logger.info(f"RFMS API returned {len(result) if isinstance(result, list) else 'non-list'} result(s)")
            if isinstance(result, list) and len(result) > 0:
                sample = result[0]
                logger.info(f"Sample customer fields: {list(sample.keys()) if isinstance(sample, dict) else 'non-dict'}")
                if isinstance(sample, dict):
                    logger.info(f"Sample customerType: '{sample.get('customerType', 'N/A')}', customerBusinessName: '{sample.get('customerBusinessName', 'N/A')}', customerName: '{sample.get('customerName', 'N/A')}'")
        
        # Check if the result is an error response
        if isinstance(result, dict) and result.get('status') == 'failed':
            logger.info(f"No customers found for search term: {search_term}")
            # Return mock data for testing if no real customers found
            if search_term.lower() in ['test', 'a', 'b', 'c', 'd', 'e']:
                mock_customers = [
                    {
                        'id': 1,
                        'name': 'Test Builder Company',
                        'business_name': 'Test Builder Company',
                        'address1': '123 Builder St',
                        'city': 'Builder City',
                        'state': 'BC',
                        'postal_code': '12345',
                        'phone': '555-0123',
                        'email': 'builder@test.com'
                    },
                    {
                        'id': 2,
                        'name': 'A to Z Flooring Solutions',
                        'business_name': 'A to Z Flooring Solutions',
                        'address1': '456 Flooring Ave',
                        'city': 'Floor City',
                        'state': 'FC',
                        'postal_code': '54321',
                        'phone': '555-0456',
                        'email': 'flooring@test.com'
                    },
                    {
                        'id': 3,
                        'name': 'John Smith',
                        'business_name': 'Smith Construction',
                        'address1': '789 Construction Blvd',
                        'city': 'Build City',
                        'state': 'BC',
                        'postal_code': '67890',
                        'phone': '555-0789',
                        'email': 'smith@test.com'
                    },
                    {
                        'id': 4,
                        'name': 'Derek Mathieson',
                        'business_name': 'Derek Mathieson',
                        'address1': '2 Kinloch Road',
                        'city': 'Daisy Hill',
                        'state': 'QLD',
                        'postal_code': '4127',
                        'phone': '0474 044 620',
                        'email': 'derek@example.com'
                    },
                    {
                        'id': 5,
                        'name': 'Jane Doe',
                        'business_name': 'Jane Doe',
                        'address1': '456 Main Street',
                        'city': 'Sydney',
                        'state': 'NSW',
                        'postal_code': '2000',
                        'phone': '02 1234 5678',
                        'email': 'jane@example.com'
                    }
                ]
                logger.info(f"Using mock data for testing with {len(mock_customers)} customers")
                result = mock_customers
            else:
                return jsonify([])
        
        # Ensure result is a list
        if not isinstance(result, list):
            logger.warning(f"Unexpected result type from RFMS API: {type(result)}")
            return jsonify([])
        
        if not result:
            logger.info(f"No customers found for search term: {search_term}")
            return jsonify([])
        
        # Filter by customer type if specified
        if customer_type == 'builder':
            # First, log what we received from RFMS for debugging
            logger.info(f"RFMS returned {len(result)} customers. Sample customer types: {[c.get('customerType', 'N/A') for c in result[:5] if isinstance(c, dict)]}")
            
            # Filter for builders based on customerType field and business names
            customers = [c for c in result if isinstance(c, dict) and (
                c.get('customerType', '').upper() == 'BUILDERS' or
                c.get('customerType', '').upper() == 'BUILDER' or
                'builder' in c.get('customerBusinessName', '').lower() or 
                'construction' in c.get('customerBusinessName', '').lower() or
                'build' in c.get('customerBusinessName', '').lower() or
                'flooring' in c.get('customerBusinessName', '').lower() or
                'builder' in c.get('customerName', '').lower() or
                'construction' in c.get('customerName', '').lower() or
                'group' in c.get('customerBusinessName', '').lower() or
                'group' in c.get('customerName', '').lower()
            )]
            
            # If no customers match builder criteria, return all results (user may be searching for a known builder)
            if not customers and result:
                logger.warning(f"No customers matched builder filter criteria. Returning all {len(result)} results as fallback.")
                customers = [c for c in result if isinstance(c, dict)]
            elif not customers:
                logger.info(f"No customers found at all for search term: {search_term}")
            
            # Sort by relevance - prioritize matches in business name, then customer name
            search_lower = search_term.lower()
            if customers:
                customers.sort(key=lambda x: (
                    # Exact matches first
                    search_lower not in (x.get('customerBusinessName', '').lower() or ''),
                    search_lower not in (x.get('customerName', '').lower() or ''),
                    # Then starts with matches
                    not (x.get('customerBusinessName', '').lower() or '').startswith(search_lower),
                    not (x.get('customerName', '').lower() or '').startswith(search_lower)
                ))
        elif customer_type == 'customer':
            # Filter for regular customers (exclude builders)
            customers = [c for c in result if isinstance(c, dict) and not (
                c.get('customerType', '').upper() == 'BUILDERS' or
                'builder' in c.get('customerBusinessName', '').lower() or 
                'construction' in c.get('customerBusinessName', '').lower() or
                'build' in c.get('customerBusinessName', '').lower() or
                'flooring' in c.get('customerBusinessName', '').lower() or
                'builder' in c.get('customerName', '').lower() or
                'construction' in c.get('customerName', '').lower()
            )]
        else:
            customers = [c for c in result if isinstance(c, dict)]
        
        logger.info(f"Found {len(customers)} {customer_type} customers for search term: {search_term}")
        return jsonify(customers)
    except Exception as e:
        logger.error(f"Error searching customers: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/export-to-rfms', methods=['POST'])
def export_to_rfms():
    """Export customer, job/quote, and order data to RFMS API."""
    try:
        # Get the data from the request
        data = request.json
        
        if not data:
            logger.warning("No data provided for RFMS export")
            return jsonify({"error": "No data provided for export"}), 400
        
        # Convert RFMS-related fields to uppercase
        data = uppercase_rfms_fields(data)
        
        logger.info(f"Starting RFMS export with data: {data.keys()}")
        
        # Use the internal export function
        return export_to_rfms_internal(data)
        
    except Exception as e:
        logger.error(f"Error during RFMS export: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error during RFMS export: {str(e)}"}), 500


def get_contract_type_id(contract_type_name):
    """Map contract type name to RFMS ID."""
    key = _normalize_choice(contract_type_name, None)
    if key not in CONTRACT_TYPE_IDS:
        key = CONTRACT_TYPE_DEFAULT
    return CONTRACT_TYPE_IDS[key]


def get_order_type_id(order_type_name):
    """Map order type name to RFMS ID."""
    key = _normalize_choice(order_type_name, ORDER_TYPE_ALIASES)
    if key not in ORDER_TYPE_IDS:
        key = ORDER_TYPE_DEFAULT
    return ORDER_TYPE_IDS[key]


def get_ad_source_id(ad_source_name):
    """Map ad source name to RFMS ID."""
    key = _normalize_choice(ad_source_name, AD_SOURCE_ALIASES)
    if key not in AD_SOURCE_IDS:
        key = AD_SOURCE_DEFAULT
    return AD_SOURCE_IDS[key]


def get_labour_service_type_id(labour_service_type_name):
    """Map labour/service type name to RFMS ID."""
    key = _normalize_choice(labour_service_type_name, LABOUR_SERVICE_TYPE_ALIASES)
    if key not in LABOUR_SERVICE_TYPE_IDS:
        key = LABOUR_SERVICE_TYPE_DEFAULT
    return LABOUR_SERVICE_TYPE_IDS[key]

def format_contacts_html(contacts, po_value=None):
    """Format contacts as HTML for RFMS notes"""
    html = "<html><head></head><body>"
    
    if po_value:
        html += f"<b>PO Value</b><br>${po_value}<br>"
    
    for contact in contacts:
        html += f"<b>{contact.get('title', 'Contact')}</b><br>"
        
        name_parts = []
        if contact.get('first_name'):
            name_parts.append(contact['first_name'])
        if contact.get('last_name'):
            name_parts.append(contact['last_name'])
        if name_parts:
            html += f"Name: {' '.join(name_parts)}<br>"
        
        if contact.get('mobile'):
            html += f"Mobile: {contact['mobile']}<br>"
        if contact.get('phone'):
            html += f"Phone: {contact['phone']}<br>"
        if contact.get('emails'):
            html += f"Email: {contact['emails']}<br>"
    
    html += "</body></html>"
    return html

@app.route('/clear_data', methods=['POST'])
def clear_data():
    """Clear current extracted data for next upload."""
    session.pop('extracted_data', None)
    return redirect(url_for('index'))

@app.route('/api/delete-upload/<int:pdf_id>', methods=['DELETE'])
def delete_upload(pdf_id):
    """Delete an upload from the queue."""
    try:
        pdf_data = PdfData.query.get_or_404(pdf_id)
        
        # Delete the file if it exists
        if pdf_data.filename:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_data.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Delete from database
        db.session.delete(pdf_data)
        db.session.commit()
        
        logger.info(f"Deleted upload {pdf_id}: {pdf_data.filename}")
        return jsonify({'success': True, 'message': 'Upload deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting upload {pdf_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Cache RFMS status check results to reduce API calls
_rfms_status_cache = {
    'result': None,
    'timestamp': None,
    'cache_duration': timedelta(minutes=5)  # Cache for 5 minutes
}

@app.route('/api/rfms-status', methods=['GET'])
def rfms_status():
    """Check RFMS API connection status. Uses caching to reduce authentication calls."""
    try:
        global _rfms_status_cache
        
        # Check if we have a cached result that's still valid
        now = datetime.now()
        if (_rfms_status_cache['result'] and 
            _rfms_status_cache['timestamp'] and 
            (now - _rfms_status_cache['timestamp']) < _rfms_status_cache['cache_duration']):
            logger.debug("Returning cached RFMS status")
            return jsonify(_rfms_status_cache['result'])
        
        # Check if RFMS credentials are configured
        store_code = os.getenv('RFMS_STORE_CODE')
        api_key = os.getenv('RFMS_API_KEY')
        
        if not store_code or not api_key:
            logger.warning("RFMS credentials not found in environment variables")
            result = {
                'online': False,
                'message': 'RFMS credentials not configured. Please set RFMS_STORE_CODE and RFMS_API_KEY environment variables.',
                'configured': False
            }
            _rfms_status_cache['result'] = result
            _rfms_status_cache['timestamp'] = now
            return jsonify(result)
        
        # Test RFMS connection - reuse existing session if valid (don't force new session)
        test_result = rfms_client.test_connection(force_new_session=False)
        logger.debug(f"RFMS connection test result: {test_result}")
        
        result = {
            'online': test_result.get('success', False),
            'message': test_result.get('message', 'Unknown status'),
            'configured': True
        }
        
        # Cache the result
        _rfms_status_cache['result'] = result
        _rfms_status_cache['timestamp'] = now
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error checking RFMS status: {str(e)}")
        return jsonify({
            'online': False,
            'message': f'Connection error: {str(e)}',
            'configured': True
        })


@app.route('/api/salespersons', methods=['GET'])
def get_salespersons():
    """Get list of salespersons from RFMS."""
    try:
        # This would typically call RFMS API to get salespersons
        # For now, return a static list with the correct names
        salespersons = [
            {'id': 'ZORAN VEKIC', 'name': 'ZORAN VEKIC'},
            {'id': 'STEVE WHYTE', 'name': 'STEVE WHYTE'},
            {'id': 'ADRIAN SIMPSON', 'name': 'ADRIAN SIMPSON'},
            {'id': 'EMILY VEKIC', 'name': 'EMILY VEKIC'},
            {'id': 'SHAR VEKIC', 'name': 'SHAR VEKIC'}
        ]
        return jsonify({'success': True, 'salespersons': salespersons})
    except Exception as e:
        logger.error(f"Error getting salespersons: {str(e)}")
        return jsonify({'error': f'Error getting salespersons: {str(e)}'}), 500


@app.route('/api/contract-types', methods=['GET'])
def get_contract_types():
    """Get list of contract types from RFMS."""
    try:
        contract_types = _build_choice_list(CONTRACT_TYPE_IDS)
        return jsonify({'success': True, 'contract_types': contract_types})
    except Exception as e:
        logger.error(f"Error getting contract types: {str(e)}")
        return jsonify({'error': f'Error getting contract types: {str(e)}'}), 500


@app.route('/api/order-types', methods=['GET'])
def get_order_types():
    """Get list of order types from RFMS."""
    try:
        order_types = _build_choice_list(ORDER_TYPE_IDS, ORDER_TYPE_DISPLAY_OVERRIDES)
        return jsonify({'success': True, 'order_types': order_types})
    except Exception as e:
        logger.error(f"Error getting order types: {str(e)}")
        return jsonify({'error': f'Error getting order types: {str(e)}'}), 500


@app.route('/api/ad-sources', methods=['GET'])
def get_ad_sources():
    """Get list of ad sources from RFMS."""
    try:
        ad_sources = _build_choice_list(AD_SOURCE_IDS)
        return jsonify({'success': True, 'ad_sources': ad_sources})
    except Exception as e:
        logger.error(f"Error getting ad sources: {str(e)}")
        return jsonify({'error': f'Error getting ad sources: {str(e)}'}), 500


@app.route('/api/suburbs/search', methods=['GET'])
def search_suburbs_api():
    """API endpoint to search for suburbs by name."""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query or len(query) < 2:
            return jsonify({'suburbs': []})
        
        results = search_suburbs(query, limit=limit)
        return jsonify({'suburbs': results})
    
    except Exception as e:
        logger.error(f"Error searching suburbs: {str(e)}")
        return jsonify({'error': str(e), 'suburbs': []}), 500


@app.route('/manual-enquiry')
def manual_enquiry():
    """Customer enquiry form page."""
    return render_template('manual_enquiry.html')


@app.route('/receive-stock')
def receive_stock():
    """Stock receiving page for consignment notes."""
    return render_template('receive_stock.html')


@app.route('/submit-manual-enquiry', methods=['POST'])
def submit_manual_enquiry():
    """Handle customer enquiry form submission."""
    try:
        if request.is_json:
            form_data = request.get_json()
        else:
            form_data = request.form.to_dict()
        
        # Convert RFMS-related fields to uppercase
        form_data = uppercase_rfms_fields(form_data)

        # Extract form fields (already uppercase)
        first_name = form_data.get('first_name', '').strip()
        surname = form_data.get('surname', '').strip()
        business_name = form_data.get('business_name', '').strip()
        phone = form_data.get('phone', '').strip()
        phone2 = form_data.get('phone2', '').strip()
        email = form_data.get('email', '').strip()
        address1 = form_data.get('address1', '').strip()
        address2 = form_data.get('address2', '').strip()
        suburb = form_data.get('suburb', '').strip()
        state = form_data.get('state', '').strip()
        postal_code = form_data.get('postal_code', '').strip()
        enquiry_number = form_data.get('enquiry_number', '').strip()
        scope_of_work = form_data.get('scope_of_work', '').strip()

        # Parse dollar value and strip GST (10%) for RFMS
        dollar_value_raw = form_data.get('dollar_value', '1.0') or '1.0'
        try:
            dollar_value = float(dollar_value_raw)
        except ValueError:
            dollar_value = 1.0
        dollar_value = dollar_value / 1.1

        notes = form_data.get('notes', '').strip()
        document_type_input = (
            form_data.get('document_type')
            or form_data.get('documentTypeSelection')
            or 'quotation'
        )
        document_type = (document_type_input or '').strip().lower()
        if document_type in ['order', 'sales_order', 'sales-order', 'purchase order']:
            document_type = 'purchase_order'
        elif document_type not in ['quotation', 'customer_enquiry', 'purchase_order']:
            document_type = 'quotation'

        # Configuration settings (already uppercase from uppercase_rfms_fields)
        salesperson = form_data.get('salesperson', 'STEVE WHYTE')
        contract_type = form_data.get('contractType', 'DEPOSIT & COD')
        order_type = form_data.get('orderType', 'RESIDENTIAL HOME')
        labour_service_type = form_data.get('labourServiceType', 'SUPPLY & INSTALL')
        ad_source = form_data.get('adSource', 'PHONE ENQUIRY') or 'PHONE ENQUIRY'
        measure_date = form_data.get('measureDate', '')
        date_status = form_data.get('dateStatus', 'Sales Rep to Call')
        appointment_time = form_data.get('appointmentTime', '')
        install_date = form_data.get('installDate', '')

        # Log the configuration values received
        logger.info(
            "Manual entry submission - salesperson=%s, contract_type=%s, order_type=%s, labour_service_type=%s, ad_source=%s",
            salesperson,
            contract_type,
            order_type,
            labour_service_type,
            ad_source
        )

        # Validate required fields
        if not first_name or not surname:
            return jsonify({'success': False, 'error': 'Both first name and surname are required'}), 400

        # Note: Appointment info will be added to public notes in the export function
        # For now, keep notes as is
        combined_notes = notes

        # Combine first name and surname
        customer_name = f"{first_name} {surname}".strip()

        # Generate enquiry number if not provided
        if not enquiry_number:
            now = datetime.now()
            enquiry_number = f"ENQ-{now.strftime('%Y%m%d-%H%M')}"

        # Handle file attachments (if any)
        saved_attachments = []
        if request.files:
            attachments = request.files.getlist('attachments')
        else:
            attachments = []

        if attachments:
            storage_subdir = os.path.join(
                app.config['UPLOAD_FOLDER'],
                'customer_enquiries',
                enquiry_number
            )
            os.makedirs(storage_subdir, exist_ok=True)

            for file in attachments:
                if not file or not file.filename:
                    continue
                if not allowed_attachment(file.filename):
                    logger.warning("Rejected attachment %s due to unsupported type", file.filename)
                    return jsonify({'success': False, 'error': f'Unsupported attachment type for {file.filename}'}), 400

                original_filename = secure_filename(file.filename)
                stored_filename = f"{uuid.uuid4()}_{original_filename}"
                storage_path = os.path.join(storage_subdir, stored_filename)
                file.save(storage_path)

                saved_attachments.append({
                    'original_filename': original_filename,
                    'stored_filename': stored_filename,
                    'path': os.path.relpath(storage_path, app.root_path)
                })

        # Create customer data for RFMS (proper payload structure)
        customer_data = {
            "customerType": "RESIDENTIAL",
            "entryType": "Customer",
            "customerAddress": {
                "firstName": first_name,
                "lastName": surname,
                "address1": address1,
                "address2": address2,
                "city": suburb,
                "state": state,
                "postalCode": postal_code
            },
            "shipToAddress": {
                "firstName": first_name,
                "lastName": surname,
                "address1": address1,
                "address2": address2,
                "city": suburb,
                "state": state,
                "postalCode": postal_code
            },
            "phone1": phone,
            "phone2": phone2,
            "email": email,
            "businessName": business_name,
            "taxStatus": "Tax",
            "taxMethod": "SalesTax",
            "preferredSalesperson1": salesperson,
            "preferredSalesperson2": ""
        }

        # Create extracted data structure (similar to PDF extraction)
        extracted_data = {
            'document_type': document_type,
            'customer_name': customer_name,
            'business_name': business_name,
            'phone': phone,
            'phone2': phone2,
            'email': email,
            'address1': address1,
            'address2': address2,
            'city': suburb,
            'state': state,
            'postal_code': postal_code,
            'po_number': enquiry_number,
            'scope_of_work': scope_of_work,
            'dollar_value': dollar_value,
            'notes': combined_notes,
            'salesperson': salesperson,
            'contract_type': contract_type,
            'order_type': order_type,
            'labour_service_type': labour_service_type,
            'ad_source': ad_source,
            'customer_type': 'RESIDENTIAL',
            'required_date': measure_date,  # Keep for backwards compatibility
            'measure_date': measure_date,
            'install_date': install_date,
            'date_status': date_status,
            'appointment_time': appointment_time,
            'source': 'manual_enquiry',
            'customer_data': customer_data,
            'attachments': saved_attachments,
            'attachment_summary': [att['original_filename'] for att in saved_attachments],
            # Map to expected field names for export function
            'contact_first_name': first_name,
            'contact_last_name': surname,
            'contact_mobile': phone2,
            'contact_phone': phone,
            'contact_email': email,
            'supervisor_name': '',
            'supervisor_phone': '',
            'supervisor_mobile': '',
            'job_summary': scope_of_work,
            'estimated_delivery_date': install_date if install_date else measure_date,
            'measure_date': measure_date,
            'install_date': install_date,
            'all_contacts': []
        }

        # Save to database
        pdf_data = PdfData(
            filename=f"Customer Enquiry - {customer_name}",
            customer_name=customer_name,
            business_name=business_name,
            po_number=enquiry_number,
            scope_of_work=scope_of_work,
            dollar_value=dollar_value,
            extracted_data=extracted_data,
            notes=notes,
            created_at=datetime.now()
        )

        db.session.add(pdf_data)
        db.session.commit()

        logger.info("Customer enquiry created for %s (ID: %s)", customer_name, pdf_data.id)

        return jsonify({
            'success': True,
            'message': f'Customer enquiry created successfully for {customer_name}. Attachments saved: {len(saved_attachments)}',
            'pdf_id': pdf_data.id,
            'data': extracted_data,
            'next_steps': [
                '1. Customer data will be created in RFMS when you process this enquiry',
                '2. A new QUOTE will be generated with the enquiry details',
                '3. Attachments will be uploaded to RFMS with the quote'
            ]
        })

    except Exception as e:
        logger.error("Error creating manual enquiry: %s", str(e), exc_info=True)
        return jsonify({'success': False, 'error': f'Error creating manual enquiry: {str(e)}'}), 500


@app.route('/api/order/<order_number>', methods=['GET'])
def get_order_details_api(order_number):
    """API endpoint to get order details for stock receiving."""
    try:
        order_details = rfms_client.get_order(order_number, locked=False, include_attachments=False)
        
        if order_details and order_details.get('status') == 'success':
            result = order_details.get('result', {})
            return jsonify({
                'success': True,
                'order_details': result
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Order {order_number} not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting order details for {order_number}: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/receive-stock/upload', methods=['POST'])
def upload_consignment_note():
    """Handle consignment note photo upload and extract information."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload a PDF or image file.'}), 400
        
        # Save the file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Analyze the document using AI - try invoice first, then consignment note
        if not document_analyzer:
            return jsonify({'success': False, 'error': 'AI analyzer not available. Please configure GEMINI_API_KEY.'}), 500
        
        try:
            # First, try to analyze as supplier invoice (if PDF or image)
            invoice_data = None
            is_invoice = False
            
            try:
                invoice_data = document_analyzer.analyze_supplier_invoice(file_path)
                # Check if it looks like a full invoice (has invoice_number, total, and line_items)
                if invoice_data and invoice_data.get('invoice_number') and invoice_data.get('total') and invoice_data.get('line_items'):
                    is_invoice = True
                    logger.info(f"Detected full supplier invoice: {invoice_data.get('invoice_number')}")
            except Exception as e:
                logger.debug(f"Document is not an invoice or invoice analysis failed: {str(e)}")
                # Continue to try consignment note analysis
            
            if is_invoice:
                # It's a full invoice - return invoice data
                return jsonify({
                    'success': True,
                    'extracted_data': None,  # No consignment note data
                    'invoice_data': invoice_data,  # Full invoice data
                    'is_invoice': True,
                    'file_path': file_path
                })
            else:
                # Analyze as consignment note
                extracted_data = document_analyzer.analyze_consignment_note(file_path)
                logger.info(f"Extracted consignment note data: {extracted_data}")
                
                return jsonify({
                    'success': True,
                    'extracted_data': extracted_data,
                    'invoice_data': None,
                    'is_invoice': False,
                    'file_path': file_path
                })
        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': f'Failed to analyze document: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Error uploading consignment note: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/receive-stock/search', methods=['POST'])
def search_orders_for_receiving():
    """Search for orders and purchase orders based on extracted consignment note data."""
    try:
        from utils.order_utils import normalize_order_number, get_order_number_variations
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Convert RFMS-related fields to uppercase
        data = uppercase_rfms_fields(data)
        
        order_number = data.get('order_number')
        purchase_order_number = data.get('purchase_order_number')
        supplier_name = data.get('supplier_name')
        stock_items = data.get('stock_items', [])
        
        logger.info(f"Starting search - Order: {order_number}, PO: {purchase_order_number}, Supplier: {supplier_name}")
        
        results = {
            'orders': [],
            'purchase_orders': [],
            'products': []
        }
        
        # If no order number or PO number provided, log warning
        if not order_number and not purchase_order_number:
            logger.warning("No order number or purchase order number provided for search")
            return jsonify({
                'success': False,
                'error': 'Either order_number or purchase_order_number is required for search'
            }), 400
        
        # Normalize and get variations for order number
        order_variations = []
        if order_number:
            normalized = normalize_order_number(order_number)
            order_variations = get_order_number_variations(order_number)
            logger.info(f"Order number '{order_number}' normalized to: {normalized}, variations: {order_variations}")
        
        # Normalize and get variations for purchase order number
        po_variations = []
        if purchase_order_number:
            normalized_po = normalize_order_number(purchase_order_number)
            po_variations = get_order_number_variations(purchase_order_number)
            logger.info(f"PO number '{purchase_order_number}' normalized to: {normalized_po}, variations: {po_variations}")
            
            # If order_number and purchase_order_number are the same or similar, merge variations
            if order_number and purchase_order_number:
                # Check if they normalize to the same base
                if normalized.get('base') == normalized_po.get('base'):
                    # Merge variations, removing duplicates
                    all_variations = list(set(order_variations + po_variations))
                    order_variations = all_variations
                    po_variations = all_variations
        
        # Check if this is a #ST or ST order (General Warehouse stock)
        is_st_order = False
        st_search_terms = []
        if order_number:
            order_upper = order_number.upper().strip()
            if order_upper.startswith('#ST') or order_upper.startswith('ST'):
                is_st_order = True
                # Create search variations for #ST orders
                # Remove # if present, try both with and without
                st_base = order_upper.replace('#', '').strip()
                st_search_terms = [order_upper, st_base, f"#{st_base}"]
                logger.info(f"Detected #ST order, search terms: {st_search_terms}")
        
        if purchase_order_number:
            po_upper = purchase_order_number.upper().strip()
            if po_upper.startswith('#ST') or po_upper.startswith('ST'):
                is_st_order = True
                # Create search variations for #ST orders
                st_base = po_upper.replace('#', '').strip()
                st_search_terms.extend([po_upper, st_base, f"#{st_base}"])
                logger.info(f"Detected #ST PO, search terms: {st_search_terms}")
        
        # Search for #ST orders specifically using dedicated method
        if is_st_order and st_search_terms:
            logger.info(f"Searching for #ST order with terms: {st_search_terms}")
            for st_term in st_search_terms:
                # Use the dedicated find_st_order method
                try:
                    st_order = rfms_client.find_st_order(st_term)
                    if st_order:
                        logger.info(f"Found #ST order using find_st_order: {st_term}")
                        # Format the result
                        order_num = st_order.get('number') or st_order.get('documentNumber') or st_term
                        st_order['documentNumber'] = order_num
                        st_order['number'] = order_num
                        st_order['customerName'] = 'General Warehouse Stock'
                        st_order['is_st_order'] = True
                        
                        # Check if already in results
                        existing = next((o for o in results['orders'] 
                                       if (o.get('documentNumber') or o.get('number')) == order_num), None)
                        if not existing:
                            results['orders'].append(st_order)
                except Exception as e:
                    logger.warning(f"Error in find_st_order for '{st_term}': {e}")
                
                # Also try regular order search as fallback
                try:
                    orders = rfms_client.find_orders_by_search(st_term)
                    logger.info(f"Regular search for '{st_term}' found {len(orders)} orders")
                    for order in orders:
                        order_num = order.get('documentNumber') or order.get('number', '')
                        if order_num and (order_num.upper().startswith('#ST') or order_num.upper().startswith('ST')):
                            order['is_st_order'] = True
                            order['customerName'] = 'General Warehouse Stock'
                            existing = next((o for o in results['orders'] 
                                           if (o.get('documentNumber') or o.get('number')) == order_num), None)
                            if not existing:
                                results['orders'].append(order)
                        elif order_num:  # Also add non-ST orders that match (might be related)
                            existing = next((o for o in results['orders'] 
                                           if (o.get('documentNumber') or o.get('number')) == order_num), None)
                            if not existing:
                                results['orders'].append(order)
                except Exception as e:
                    logger.warning(f"Error in regular search for '{st_term}': {e}")
                
                # Try purchase order search (try only line 1 first, then others if needed)
                # Limit to avoid excessive API calls that return 500 errors
                for line_num in [1]:  # Only try line 1 for #ST orders to avoid 500 errors
                    try:
                        po_result = rfms_client.find_purchase_order(st_term, line_num)
                        if po_result:
                            po_num = po_result.get('number') or po_result.get('orderNumber', '')
                            if po_num and (po_num.upper().startswith('#ST') or po_num.upper().startswith('ST')):
                                # Format as purchase order result
                                po_result['orderNumber'] = po_num
                                po_result['customerName'] = 'General Warehouse Stock'
                                po_result['is_st_order'] = True
                                existing = next((po for po in results['purchase_orders'] 
                                               if po.get('orderNumber') == po_num), None)
                                if not existing:
                                    results['purchase_orders'].append(po_result)
                                break  # Found it, no need to try more line numbers
                    except Exception as e:
                        # Don't log debug for expected 500 errors from RFMS API
                        if '500' not in str(e):
                            logger.debug(f"Error finding #ST purchase order {st_term} line {line_num}: {e}")
                        # Stop trying more line numbers if we get a 500 error
                        if '500' in str(e) or 'error has occurred' in str(e).lower():
                            break
        
        # Search by order number variations (skip if already handled as #ST)
        if order_variations and not is_st_order:
            logger.info(f"Searching for orders with variations: {order_variations}")
            for variation in order_variations:
                try:
                    orders = rfms_client.find_orders_by_search(variation)
                    logger.info(f"Found {len(orders)} orders for variation '{variation}'")
                    if orders:
                        results['orders'].extend(orders)
                except Exception as e:
                    logger.warning(f"Error searching for orders with variation '{variation}': {e}")
        
        # Search by purchase order number variations (skip if already handled as #ST)
        if po_variations and not is_st_order:
            logger.info(f"Searching for purchase orders with variations: {po_variations}")
            for variation in po_variations:
                # Try to find purchase order in inventory section
                try:
                    # Try line 1 first
                    po_result = rfms_client.find_purchase_order(variation, 1)
                    if po_result:
                        logger.info(f"Found purchase order for variation '{variation}': {po_result.get('number') or po_result.get('orderNumber')}")
                        # Check if already in results
                        existing = next((po for po in results['purchase_orders'] 
                                       if po.get('orderNumber') == po_result.get('orderNumber')), None)
                        if not existing:
                            results['purchase_orders'].append(po_result)
                except Exception as e:
                    # Only log if it's not a 500 error (expected for non-existent orders)
                    error_str = str(e)
                    if '500' not in error_str and 'error has occurred' not in error_str.lower():
                        logger.warning(f"Error finding purchase order {variation}: {e}")
                
                # Also search orders by PO number variation
                try:
                    orders = rfms_client.find_orders_by_search(variation)
                    logger.info(f"Found {len(orders)} orders when searching by PO variation '{variation}'")
                    if orders:
                        results['orders'].extend(orders)
                except Exception as e:
                    logger.warning(f"Error searching orders by PO variation '{variation}': {e}")
        
        # If we have a normalized base number, also search by base only
        if order_number and not is_st_order:
            normalized = normalize_order_number(order_number)
            base = normalized.get('base')
            if base and base not in order_variations:
                logger.info(f"Also searching by base order number: {base}")
                try:
                    orders = rfms_client.find_orders_by_search(base)
                    logger.info(f"Found {len(orders)} orders for base '{base}'")
                    if orders:
                        results['orders'].extend(orders)
                except Exception as e:
                    logger.warning(f"Error searching by base '{base}': {e}")
        
        if purchase_order_number and not is_st_order:
            normalized_po = normalize_order_number(purchase_order_number)
            base_po = normalized_po.get('base')
            if base_po and base_po not in po_variations:
                logger.info(f"Also searching purchase orders by base: {base_po}")
                # Search purchase orders by base
                try:
                    po_result = rfms_client.find_purchase_order(base_po, 1)
                    if po_result:
                        logger.info(f"Found purchase order for base '{base_po}': {po_result.get('number') or po_result.get('orderNumber')}")
                        existing = next((po for po in results['purchase_orders'] 
                                       if po.get('orderNumber') == po_result.get('orderNumber')), None)
                        if not existing:
                            results['purchase_orders'].append(po_result)
                except Exception as e:
                    error_str = str(e)
                    if '500' not in error_str and 'error has occurred' not in error_str.lower():
                        logger.warning(f"Error finding purchase order by base {base_po}: {e}")
                
                try:
                    orders = rfms_client.find_orders_by_search(base_po)
                    logger.info(f"Found {len(orders)} orders for PO base '{base_po}'")
                    if orders:
                        results['orders'].extend(orders)
                except Exception as e:
                    logger.warning(f"Error searching orders by PO base '{base_po}': {e}")
        
        # Search for products/stock items
        for stock_item in stock_items[:5]:  # Limit to first 5 items
            if stock_item:
                try:
                    products = rfms_client.find_products(stock_item)
                    logger.info(f"Found {len(products)} products for stock item '{stock_item}'")
                    if products:
                        results['products'].extend(products)
                except Exception as e:
                    logger.warning(f"Error searching for product '{stock_item}': {e}")
        
        # Log summary before deduplication
        logger.info(f"Search summary - Orders found: {len(results['orders'])}, Purchase Orders found: {len(results['purchase_orders'])}, Products found: {len(results['products'])}")
        
        # Remove duplicates from orders and enrich with full order details
        seen_order_numbers = set()
        unique_orders = []
        for order in results['orders']:
            order_num = order.get('documentNumber') or order.get('number')
            if order_num and order_num not in seen_order_numbers:
                seen_order_numbers.add(order_num)
                
                # Normalize order data structure
                # Extract PO number from various possible locations
                if not order.get('poNumber') and order.get('description'):
                    # Sometimes PO number is in description like "PO number: 12345"
                    import re
                    po_match = re.search(r'PO\s*(?:number|#|:)?\s*:?\s*([A-Z0-9\-]+)', order.get('description', ''), re.IGNORECASE)
                    if po_match:
                        order['poNumber'] = po_match.group(1)
                
                # Build customer name from various possible fields
                customer_name_parts = []
                if order.get('customerFirst'):
                    customer_name_parts.append(order.get('customerFirst'))
                if order.get('customerLast'):
                    customer_name_parts.append(order.get('customerLast'))
                if customer_name_parts:
                    order['customerName'] = ' '.join(customer_name_parts).strip()
                
                # Check if this is a #ST order
                is_st_order = order_num.upper().startswith('#ST') or order_num.upper().startswith('ST')
                
                # Try to get full order details to include product information
                try:
                    full_order = rfms_client.get_order(order_num)
                    if full_order and full_order.get('status') == 'success':
                        order_details = full_order.get('result', {})
                        # Merge full order details with search result
                        if not order.get('poNumber') and order_details.get('poNumber'):
                            order['poNumber'] = order_details.get('poNumber')
                        
                        # For #ST orders, set customer name to "General Warehouse Stock"
                        if is_st_order:
                            order['customerName'] = 'General Warehouse Stock'
                            order['is_st_order'] = True
                        elif not order.get('customerName'):
                            sold_to = order_details.get('soldTo', {})
                            if isinstance(sold_to, dict):
                                if sold_to.get('businessName'):
                                    order['customerName'] = sold_to.get('businessName')
                                elif sold_to.get('lastName') or sold_to.get('firstName'):
                                    name_parts = [sold_to.get('firstName', ''), sold_to.get('lastName', '')]
                                    order['customerName'] = ' '.join(name_parts).strip()
                        
                        # Add product lines
                        order['lines'] = order_details.get('lines', [])
                        order['full_details'] = order_details
                        order['soldTo'] = order_details.get('soldTo', {})
                        order['shipTo'] = order_details.get('shipTo', {})
                except Exception as e:
                    logger.warning(f"Could not fetch full details for order {order_num}: {e}")
                    # If it's a #ST order and we can't get details, still mark it
                    if is_st_order:
                        order['customerName'] = 'General Warehouse Stock'
                        order['is_st_order'] = True
                    # Continue with basic order info from search results
                
                unique_orders.append(order)
        results['orders'] = unique_orders
        
        # Remove duplicates from purchase orders and enrich with details
        seen_po_numbers = set()
        unique_pos = []
        for po in results['purchase_orders']:
            po_num = po.get('orderNumber') or po.get('number')
            if po_num and po_num not in seen_po_numbers:
                seen_po_numbers.add(po_num)
                
                # Check if this is a #ST order
                is_st_order = po_num.upper().startswith('#ST') or po_num.upper().startswith('ST')
                
                # Try to get full order details for purchase orders
                try:
                    full_order = rfms_client.get_order(po_num)
                    if full_order and full_order.get('status') == 'success':
                        order_details = full_order.get('result', {})
                        
                        # For #ST orders, set customer name to "General Warehouse Stock"
                        if is_st_order:
                            po['customerName'] = 'General Warehouse Stock'
                            po['is_st_order'] = True
                        else:
                            # Extract customer name
                            sold_to = order_details.get('soldTo', {})
                            if isinstance(sold_to, dict):
                                if sold_to.get('businessName'):
                                    po['customerName'] = sold_to.get('businessName')
                                elif sold_to.get('lastName') or sold_to.get('firstName'):
                                    name_parts = [sold_to.get('firstName', ''), sold_to.get('lastName', '')]
                                    po['customerName'] = ' '.join(name_parts).strip()
                        
                        # Add product lines
                        po['lines'] = order_details.get('lines', [])
                        po['full_details'] = order_details
                except Exception as e:
                    logger.warning(f"Could not fetch full details for purchase order {po_num}: {e}")
                    # If it's a #ST order and we can't get details, still mark it
                    if is_st_order:
                        po['customerName'] = 'General Warehouse Stock'
                        po['is_st_order'] = True
                
                unique_pos.append(po)
        results['purchase_orders'] = unique_pos
        
        # Final summary
        final_summary = {
            'orders_count': len(results['orders']),
            'purchase_orders_count': len(results['purchase_orders']),
            'products_count': len(results['products']),
            'searched_order_number': order_number,
            'searched_po_number': purchase_order_number,
            'searched_supplier': supplier_name
        }
        logger.info(f"Search complete. Final results: {final_summary}")
        
        return jsonify({
            'success': True,
            'results': results,
            'normalized': {
                'order_number': normalize_order_number(order_number) if order_number else None,
                'purchase_order_number': normalize_order_number(purchase_order_number) if purchase_order_number else None
            },
            'search_summary': final_summary
        })
        
    except Exception as e:
        logger.error(f"Error searching orders: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/receive-stock/receive', methods=['POST'])
def receive_inventory():
    """Receive inventory for an order."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Convert RFMS-related fields to uppercase
        data = uppercase_rfms_fields(data)
        
        order_number = data.get('order_number')
        order_date = data.get('order_date')
        line_numbers = data.get('line_numbers', [])
        line_data = data.get('line_data', [])  # Detailed line data with boxes, square meters, etc.
        
        if not order_number:
            return jsonify({'success': False, 'error': 'Order number is required'}), 400
        
        # If line_data is provided, extract line_numbers from it
        if line_data and not line_numbers:
            line_numbers = [line.get('line_number') for line in line_data if line.get('line_number')]
        
        # Validate order_date - must be present and in valid format
        if not order_date or not isinstance(order_date, str):
            return jsonify({'success': False, 'error': 'Order date is required'}), 400
        
        # Check for invalid date strings
        order_date = order_date.strip()
        if not order_date or order_date.upper() in ['N/A', 'NULL', 'NONE', '']:
            return jsonify({'success': False, 'error': 'Order date is required and must be a valid date'}), 400
        
        # Validate date format - must be in YYYY-MM-DD or MM-DD-YYYY format
        import re
        date_pattern_yyyy_mm_dd = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        date_pattern_mm_dd_yyyy = re.compile(r'^\d{2}-\d{2}-\d{4}$')
        
        if not (date_pattern_yyyy_mm_dd.match(order_date) or date_pattern_mm_dd_yyyy.match(order_date)):
            return jsonify({'success': False, 'error': 'Order date must be in YYYY-MM-DD or MM-DD-YYYY format'}), 400
        
        # Try to parse the date to ensure it's valid
        try:
            from datetime import datetime
            if date_pattern_yyyy_mm_dd.match(order_date):
                # YYYY-MM-DD format
                datetime.strptime(order_date, '%Y-%m-%d')
            else:
                # MM-DD-YYYY format
                datetime.strptime(order_date, '%m-%d-%Y')
        except ValueError:
            return jsonify({'success': False, 'error': 'Order date is not a valid date'}), 400
        
        if not line_numbers:
            return jsonify({'success': False, 'error': 'At least one line number is required'}), 400
        
        # Get order details first to verify it exists and check if it's a purchase order
        is_purchase_order = False
        try:
            order_details = rfms_client.get_order(order_number)
            if not order_details or order_details.get('status') != 'success':
                return jsonify({'success': False, 'error': f'Order {order_number} not found'}), 404
            
            # Check if this is a purchase order (might be in the order details)
            order_result = order_details.get('result', {})
            # Purchase orders might have different structure - check if it's a PO
            # We'll log this for debugging
            logger.info(f"Order {order_number} details - checking if purchase order...")
            
        except Exception as e:
            logger.error(f"Error getting order {order_number}: {e}")
            return jsonify({'success': False, 'error': f'Failed to retrieve order: {str(e)}'}), 500
        
        # Format order date to MM-DD-YYYY if needed (RFMS API expects MM-DD-YYYY)
        try:
            if date_pattern_yyyy_mm_dd.match(order_date):
                # Convert YYYY-MM-DD to MM-DD-YYYY
                parts = order_date.split('-')
                if len(parts) == 3 and len(parts[0]) == 4:
                    order_date = f"{parts[1]}-{parts[2]}-{parts[0]}"
        except Exception as e:
            logger.error(f"Error formatting date {order_date}: {e}")
            return jsonify({'success': False, 'error': f'Failed to format order date: {str(e)}'}), 500
        
        # Receive inventory using the passthrough method which can close purchase orders
        logger.info(f"Receiving inventory for order {order_number}, date {order_date}, lines {line_numbers}")
        try:
            # Use the new passthrough method that can satisfy/close purchase orders
            # Get supplier name from order details if available
            supplier_name = None
            if order_details and order_details.get('status') == 'success':
                order_result = order_details.get('result', {})
                supplier_name = order_result.get('supplierName')
                if not supplier_name and order_result.get('lines'):
                    supplier_name = order_result.get('lines', [{}])[0].get('supplierName')
            
            # Ensure we have a valid session before receiving inventory
            # Test connection and force new session if needed
            try:
                connection_test = rfms_client.test_connection(force_new_session=False)
                if not connection_test.get('success'):
                    logger.warning("RFMS connection test failed, forcing new session...")
                    rfms_client.start_session(force=True)
                else:
                    logger.info("RFMS connection verified before receiving inventory")
            except Exception as e:
                logger.warning(f"Failed to verify RFMS session, forcing new session: {e}")
                try:
                    rfms_client.start_session(force=True)
                except Exception as session_error:
                    logger.error(f"Failed to start new RFMS session: {session_error}")
                    return jsonify({
                        'success': False,
                        'error': f'RFMS authentication failed. Please check RFMS credentials and try again.'
                    }), 500
            
            # Use receive_inventory_from_invoice with satisfy_po=True to close the PO
            result = rfms_client.receive_inventory_from_invoice(
                order_number=order_number,
                order_date=order_date,
                line_numbers=line_numbers,
                supplier_name=supplier_name,
                satisfy_po=True,  # This should close the purchase order!
                line_data=line_data
            )
            logger.info(f"receive_inventory_from_invoice API response status: {result.get('status')}")
            
            # Check if the API actually succeeded
            if result.get('status') != 'success':
                logger.error(f"receive_inventory_from_invoice returned non-success status: {result}")
                return jsonify({
                    'success': False,
                    'error': f"RFMS API returned: {result.get('result', 'Unknown error')}",
                    'api_response': result
                }), 500
            
            # Extract receiving results from detail
            detail = result.get('detail', {})
            receiving_results = detail.get('ReceivingResults', {})
            result_message = receiving_results.get('Message', result.get('result', 'Unknown'))
            logger.info(f"Inventory receiving result: {result_message}")
            
            if receiving_results.get('IsError'):
                logger.error(f"Receiving error: {receiving_results}")
                return jsonify({
                    'success': False,
                    'error': f"Receiving failed: {receiving_results.get('Message', 'Unknown error')}",
                    'api_response': result
                }), 500
            
            logger.info(f"Purchase order {order_number} should now be closed in RFMS (satisfy_po=True was used)")
            
        except Exception as e:
            logger.error(f"Error calling receive_inventory_from_invoice: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': f'Failed to receive inventory: {str(e)}'}), 500
        
        # Import product category utilities
        from utils.product_categories import get_category_description, get_product_type
        
        # Log detailed receiving information
        if line_data:
            logger.info(f"Receiving inventory for order {order_number} with detailed line data:")
            roll_stock_lines = []
            item_lines = []
            
            for line in line_data:
                line_num = line.get('line_number')
                boxes = line.get('boxes', 0)
                units_mtrs = line.get('units_mtrs', 0) or line.get('linear_meters', 0) or line.get('square_meters', 0)  # Support new and old field names
                product_code = line.get('product_code', '')
                is_roll_stock = line.get('is_roll_stock', False)
                is_scotia = line.get('is_scotia_trim', False)
                category_desc = get_category_description(product_code)
                
                if is_roll_stock:
                    logger.info(f"  Line {line_num} (Roll Stock - {category_desc}): {boxes} rolls, "
                              f"{units_mtrs} units/metres, Product: {product_code}")
                    roll_stock_lines.append(line)
                else:
                    item_type = "Scotia/Trim" if is_scotia else "Item"
                    logger.info(f"  Line {line_num} ({item_type} - {category_desc}): {boxes} boxes, "
                              f"{units_mtrs} units/metres, Product: {product_code}")
                    item_lines.append(line)
            
            # Summary logging
            if roll_stock_lines:
                total_rolls = sum(l.get('boxes', 0) for l in roll_stock_lines)
                total_units_mtrs = sum(l.get('units_mtrs', 0) or l.get('linear_meters', 0) for l in roll_stock_lines)
                logger.info(f"Roll Stock Summary: {len(roll_stock_lines)} line(s), {total_rolls} rolls, {total_units_mtrs:.2f} units/metres")
            
            if item_lines:
                total_boxes = sum(l.get('boxes', 0) for l in item_lines)
                total_units_mtrs = sum(l.get('units_mtrs', 0) or l.get('square_meters', 0) for l in item_lines)
                scotia_count = len([l for l in item_lines if l.get('is_scotia_trim')])
                logger.info(f"Items Summary: {len(item_lines)} line(s), {total_boxes} boxes, {total_sqm:.2f} m²")
                if scotia_count > 0:
                    logger.info(f"  Note: {scotia_count} scotia/trim lines detected - may require dual line assessment (costing and receiving)")
        
        # TODO: Future Enhancement - Dual Line Assessment for Scotias/Trims
        # If line_data contains scotia/trim items, may need to:
        # 1. Cost the items (create costing records)
        # 2. Receive the items (already done above)
        # This would require additional RFMS API endpoints for costing
        # See utils/FUTURE_ENHANCEMENTS.md for implementation details
        
        # Optional: Search for matching invoice in email and create AP record
        create_ap_record = data.get('create_ap_record', False)
        search_email_for_invoice = data.get('search_email_for_invoice', False)
        packing_slip_number = data.get('packing_slip_number')  # From extracted con note data
        uploaded_invoice_data = data.get('invoice_data')  # Full invoice if uploaded by user
        
        invoice_data = None
        ap_record_created = False
        no_invoice_notification_sent = False
        
        # If user uploaded a full invoice, use it directly (skip email search)
        if uploaded_invoice_data:
            logger.info(f"Using uploaded invoice data for order {order_number}, invoice {uploaded_invoice_data.get('invoice_number')}")
            # Validate order number matches
            invoice_order_num = uploaded_invoice_data.get('order_number')
            if invoice_order_num:
                from utils.order_utils import normalize_order_number
                invoice_norm = normalize_order_number(invoice_order_num)
                order_norm = normalize_order_number(order_number)
                if invoice_norm.get('full_joined') != order_norm.get('full_joined'):
                    logger.warning(f"Order number mismatch: entered={order_number}, invoice={invoice_order_num}")
                    # Still proceed but log warning
            invoice_data = uploaded_invoice_data
            # Create AP record directly from uploaded invoice
            if create_ap_record:
                ap_record_created = create_ap_record_from_invoice(
                    rfms_client, invoice_data, order_number, supplier_name, order_date, line_data
                )
        elif search_email_for_invoice or create_ap_record:
            try:
                logger.info(f"Searching email for invoice matching order {order_number}, supplier {supplier_name}, packing slip {packing_slip_number}")
                email_scraper = EmailScraper()
                emails = email_scraper.search_invoices(
                    supplier_name=supplier_name,
                    order_number=order_number,
                    packing_slip_number=packing_slip_number,
                    date_from=datetime.now() - timedelta(days=60),  # Search last 60 days
                    date_to=datetime.now()
                )
                
                # Try to find matching invoice
                analyzer = DocumentAnalyzer()
                for email_data in emails:
                    if email_data.get('is_invoice') and email_data.get('attachments'):
                        # Download and analyze first PDF attachment
                        attachment_data = email_scraper.download_invoice_attachment(email_data, 0)
                        if attachment_data:
                            # Save to temp file for analysis
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                                tmp_file.write(attachment_data)
                                tmp_path = tmp_file.name
                            
                            try:
                                invoice_data = analyzer.analyze_supplier_invoice(tmp_path)
                                
                                # Check if invoice matches order (using order number, supplier, and packing slip)
                                if email_scraper.match_invoice_to_order(
                                    invoice_data, 
                                    order_number=order_number, 
                                    supplier_name=supplier_name,
                                    packing_slip_number=packing_slip_number
                                ):
                                    logger.info(f"Found matching invoice: {invoice_data.get('invoice_number')}")
                                    break
                            except Exception as e:
                                logger.warning(f"Error analyzing invoice: {e}")
                            finally:
                                # Clean up temp file
                                try:
                                    os.unlink(tmp_path)
                                except:
                                    pass
                
                # If no invoice found and email search was requested, send notification
                if search_email_for_invoice and not invoice_data:
                    logger.warning(f"No matching invoice found for order {order_number}, supplier {supplier_name}")
                    try:
                        no_invoice_notification_sent = send_no_invoice_notification(
                            order_number=order_number,
                            supplier_name=supplier_name or 'Unknown',
                            packing_slip_number=packing_slip_number,
                            order_date=order_date
                        )
                        if no_invoice_notification_sent:
                            logger.info(f"Sent notification email to accounts about missing invoice for order {order_number}")
                    except Exception as e:
                        logger.error(f"Failed to send no-invoice notification: {e}", exc_info=True)
                
                # Create AP record if invoice found and requested
                if create_ap_record and invoice_data:
                    ap_record_created = create_ap_record_from_invoice(
                        rfms_client, invoice_data, order_number, supplier_name, order_date, line_data
                    )
                
            except Exception as e:
                logger.warning(f"Error searching email for invoice: {e}", exc_info=True)
                # Don't fail the receiving process if email search fails
        
        # Calculate summary statistics
        summary = {}
        if line_data:
            roll_stock_lines = [l for l in line_data if l.get('is_roll_stock')]
            item_lines = [l for l in line_data if not l.get('is_roll_stock')]
            scotia_lines = [l for l in line_data if l.get('is_scotia_trim')]
            
            summary = {
                'total_lines': len(line_data),
                'roll_stock': {
                    'count': len(roll_stock_lines),
                    'total_rolls': sum(l.get('boxes', 0) for l in roll_stock_lines),
                    'total_units_mtrs': round(sum(l.get('units_mtrs', 0) or l.get('linear_meters', 0) for l in roll_stock_lines), 2)
                },
                'items': {
                    'count': len(item_lines),
                    'total_boxes': sum(l.get('boxes', 0) for l in item_lines),
                    'total_units_mtrs': round(sum(l.get('units_mtrs', 0) or l.get('square_meters', 0) for l in item_lines), 2)
                },
                'scotia_trim_count': len(scotia_lines)
            }
        
        # Build response message
        message = f'Successfully received inventory for order {order_number}'
        notification_message = None
        
        if search_email_for_invoice and not invoice_data:
            notification_message = (
                "⚠️ No matching supplier invoice found. "
                "Please express receive the stock on RFMS Desktop and place the consignment note in the costings tray. "
                "An email has been sent to accounts advising that stock has arrived but hasn't been costed due to no matching invoice."
            )
            if no_invoice_notification_sent:
                notification_message += " Notification email sent successfully."
            else:
                notification_message += " (Note: Failed to send notification email - please manually notify accounts.)"
        
        # Log stock receiving to database for daily reporting
        try:
            from models import db, StockReceiving
            
            # Get order details for customer information
            if order_details and order_details.get('status') == 'success':
                order_result = order_details.get('result', {})
                sold_to = order_result.get('soldTo', {})
                sold_to_name = ''
                if sold_to:
                    if sold_to.get('businessName'):
                        sold_to_name = sold_to.get('businessName')
                    else:
                        first_name = sold_to.get('firstName', '')
                        last_name = sold_to.get('lastName', '')
                        sold_to_name = f"{first_name} {last_name}".strip()
                
                city_suburb = sold_to.get('city', '') if sold_to else ''
                
                # Check if this is a #ST order
                is_st_order = order_number.startswith('#ST')
                if is_st_order:
                    sold_to_name = 'General Warehouse Stock'
                    city_suburb = None
                
                # Get lines from order
                order_lines = order_result.get('lines', [])
                
                # Create database records for each line received
                with app.app_context():
                    for line in line_data:
                        line_num = line.get('line_number')
                        # Find matching line in order
                        order_line = next((l for l in order_lines if l.get('lineNumber') == line_num), None)
                        
                        if order_line:
                            stock_receiving = StockReceiving(
                                order_number=order_number,
                                sold_to_name=sold_to_name,
                                city_suburb=city_suburb,
                                supplier_name=order_line.get('supplierName') or supplier_name or 'Unknown',
                                stock_received=f"{order_line.get('styleName', '')} {order_line.get('colorName', '')}".strip(),
                                quantity=line.get('units_mtrs', 0) or line.get('boxes', 0) or line.get('square_meters', 0) or line.get('linear_meters', 0),
                                unit=order_line.get('saleUnits', ''),
                                is_st_order=is_st_order,
                                received_date=datetime.now().date(),
                                line_number=line_num,
                                product_code=line.get('product_code', '')
                            )
                            db.session.add(stock_receiving)
                    
                    db.session.commit()
                    logger.info(f"Logged {len(line_data)} stock receiving records to database")
        except Exception as e:
            logger.warning(f"Error logging stock receiving to database: {e}", exc_info=True)
            # Don't fail the receiving process if logging fails
        
        # Prepare invoice information for response
        invoice_info = None
        if invoice_data:
            invoice_info = {
                'invoice_number': invoice_data.get('invoice_number'),
                'supplier_name': invoice_data.get('supplier_name'),
                'invoice_date': invoice_data.get('invoice_date'),
                'total': invoice_data.get('total'),
                'freight': invoice_data.get('freight') or 0,
                'baling_handling': invoice_data.get('baling_handling') or 0,
                'supplier_discount': invoice_data.get('supplier_discount') or 0,
                'tax': invoice_data.get('tax') or 0,
                'line_items_count': len(invoice_data.get('line_items', []))
            }
        
        return jsonify({
            'success': True,
            'result': result,
            'message': message,
            'notification_message': notification_message,
            'line_data': line_data if line_data else None,
            'summary': summary,
            'invoice_found': invoice_data is not None,
            'invoice_info': invoice_info,
            'ap_record_created': ap_record_created
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error receiving inventory: {error_msg}", exc_info=True)
        
        # Provide more helpful error message for authentication errors
        if '401' in error_msg or 'Unauthorized' in error_msg or 'authentication' in error_msg.lower():
            return jsonify({
                'success': False,
                'error': 'RFMS authentication failed. The session may have expired. Please try again - the system will automatically refresh the session.',
                'technical_error': error_msg
            }), 401
        else:
            return jsonify({'success': False, 'error': error_msg}), 500


def create_ap_record_from_invoice(rfms_client: RFMSClient, invoice_data: Dict, 
                                  order_number: str, supplier_name: str, order_date: str,
                                  line_data: List[Dict] = None) -> bool:
    """
    Helper function to create AP record from invoice data using order line data with unitPrice.
    
    Args:
        rfms_client: RFMS client instance
        invoice_data: Invoice data from AI analyzer
        order_number: Order number
        supplier_name: Supplier name
        order_date: Order date
        line_data: List of line data with unitPrice, productCode, etc. from order
        
    Returns:
        True if AP record was created successfully
    """
    try:
        from utils.product_categories import get_category_description
        
        # Extract charges from invoice
        charges = extract_invoice_charges(invoice_data)
        freight = invoice_data.get('freight') or charges.get('freight', 0) or 0
        baling_handling = invoice_data.get('baling_handling') or charges.get('baling_handling', 0) or 0
        supplier_discount = invoice_data.get('supplier_discount') or charges.get('supplier_discount', 0) or 0
        tax = invoice_data.get('tax') or 0
        
        # Log invoice details and charges found
        logger.info(f"Processing invoice {invoice_data.get('invoice_number')} for order {order_number}")
        logger.info(f"Invoice charges found - Freight: ${freight:.2f}, Baling/Handling: ${baling_handling:.2f}, Discount: ${supplier_discount:.2f}, Tax: ${tax:.2f}")
        logger.info(f"Invoice total: ${invoice_data.get('total', 0):.2f}")
        
        # Get store number from environment variable (defaults to 49)
        store_number = int(os.environ.get('RFMS_STORE_NUMBER', '49'))
        
        # Build detail lines for AP record
        detail_lines = []
        
        # Group order lines by product category code (01-12) for subAccountCode
        # Use unitPrice from order lines (these are cost prices, typically ex-GST)
        if line_data:
            # Group lines by product category
            category_totals = {}  # {product_code: total_amount_ex_gst}
            
            for line in line_data:
                product_code = str(line.get('product_code', '')).strip()
                unit_price = float(line.get('unit_price', 0) or 0)
                quantity = float(line.get('quantity', 0) or 0)
                boxes = float(line.get('boxes', 0) or 0)
                
                # Normalize product code (01-12)
                if len(product_code) == 1:
                    product_code = '0' + product_code
                
                # Only process valid product category codes (01-12)
                try:
                    code_num = int(product_code)
                    if not (1 <= code_num <= 12):
                        continue
                except:
                    continue
                
                # Calculate line amount: use unitPrice * quantity (or boxes if quantity not available)
                # unitPrice from RFMS is typically ex-GST (cost price)
                if unit_price > 0:
                    # Use quantity if available, otherwise use boxes
                    qty = quantity if quantity > 0 else boxes
                    if qty > 0:
                        line_amount = unit_price * qty
                        
                        # Group by product category (amounts are ex-GST)
                        if product_code not in category_totals:
                            category_totals[product_code] = 0
                        category_totals[product_code] += line_amount
            
            # Create detail lines for each product category
            # unitPrice from RFMS is already ex-GST (cost prices are ex-GST)
            for product_code, total_amount in category_totals.items():
                detail_lines.append({
                    "storeNumber": store_number,
                    "accountCode": "1630",  # Cost of Goods Sold
                    "subAccountCode": product_code,  # Product category code (01-12)
                    "amount": round(total_amount, 2),  # Already ex-GST
                    "comment": f"Stock received for order {order_number}",
                    "gstCode": "GST"
                })
        
        # Add freight charge (only if present on invoice)
        # Invoice amounts are typically inc-GST, so convert to ex-GST
        if freight > 0:
            # Assume invoice amount is inc-GST, convert to ex-GST
            freight_ex_gst = freight / 1.1
            logger.info(f"Adding freight charge: ${freight:.2f} inc-GST = ${freight_ex_gst:.2f} ex-GST")
            detail_lines.append({
                "storeNumber": store_number,
                "accountCode": "5315",  # Freight
                "subAccountCode": "00",  # No sub account for freight
                "amount": round(freight_ex_gst, 2),
                "comment": f"Freight for order {order_number}",
                "gstCode": "GST"
            })
        else:
            logger.info("No freight charge found on invoice - skipping")
        
        # Add baling/handling charge (only if present on invoice)
        # Invoice amounts are typically inc-GST, so convert to ex-GST
        if baling_handling > 0:
            # Assume invoice amount is inc-GST, convert to ex-GST
            baling_ex_gst = baling_handling / 1.1
            logger.info(f"Adding baling/handling charge: ${baling_handling:.2f} inc-GST = ${baling_ex_gst:.2f} ex-GST")
            detail_lines.append({
                "storeNumber": store_number,
                "accountCode": "6406",  # Baling & Handling
                "subAccountCode": "00",  # No sub account for baling
                "amount": round(baling_ex_gst, 2),
                "comment": f"Baling/Handling for order {order_number}",
                "gstCode": "GST"
            })
        else:
            logger.info("No baling/handling charge found on invoice - skipping")
        
        if not detail_lines:
            logger.warning("No detail lines to create AP record")
            return False
        
        # Calculate total ex-GST amount (sum of all lines with gstCode "GST")
        total_ex_gst = sum(line['amount'] for line in detail_lines if line.get('gstCode') == 'GST')
        
        # Calculate GST (10% of ex-GST total)
        gst_amount = round(total_ex_gst * 0.1, 2)
        
        # Add GST payable line
        if gst_amount > 0:
            detail_lines.append({
                "storeNumber": store_number,
                "accountCode": "2820",  # GST Payable
                "subAccountCode": "00",  # No sub account for GST
                "amount": round(gst_amount, 2),
                "comment": f"GST for order {order_number}",
                "gstCode": "TAXPD"
            })
        
        # Calculate total inc-GST
        calculated_total_inc_gst = total_ex_gst + gst_amount
        
        # Get invoice total from invoice data
        invoice_total = float(invoice_data.get('total', 0) or 0)
        
        # Validate invoice total matches calculated total (allow $2.00 variance)
        if invoice_total > 0:
            variance = abs(invoice_total - calculated_total_inc_gst)
            if variance > 2.00:
                logger.warning(f"Invoice total variance exceeds $2.00: Invoice=${invoice_total}, Calculated=${calculated_total_inc_gst}, Variance=${variance:.2f}")
                # Use invoice total if variance is too large (invoice is source of truth)
                calculated_total_inc_gst = invoice_total
        else:
            # If no invoice total, use calculated
            invoice_total = calculated_total_inc_gst
        
        # Calculate dates
        invoice_date = invoice_data.get('invoice_date', order_date)
        due_date = invoice_data.get('due_date')
        if not due_date and invoice_date:
            # Default due date: 30 days from invoice date
            try:
                inv_date = datetime.strptime(invoice_date, '%Y-%m-%d')
                due_date = (inv_date + timedelta(days=30)).strftime('%Y-%m-%d')
            except:
                due_date = None
        
        # Format dates for RFMS (MM/DD/YYYY)
        if invoice_date:
            try:
                inv_dt = datetime.strptime(invoice_date, '%Y-%m-%d')
                invoice_date_formatted = inv_dt.strftime('%m/%d/%Y')
            except:
                invoice_date_formatted = invoice_date
        else:
            invoice_date_formatted = order_date
        
        if due_date:
            try:
                due_dt = datetime.strptime(due_date, '%Y-%m-%d')
                due_date_formatted = due_dt.strftime('%m/%d/%Y')
            except:
                due_date_formatted = invoice_date_formatted
        else:
            due_date_formatted = invoice_date_formatted
        
        # Log summary of detail lines being created
        logger.info(f"AP Record Detail Lines Summary for invoice {invoice_data.get('invoice_number')}:")
        for idx, line in enumerate(detail_lines, 1):
            logger.info(f"  Line {idx}: Account {line.get('accountCode')}, SubAccount {line.get('subAccountCode')}, "
                       f"Amount ${line.get('amount'):.2f}, GST Code: {line.get('gstCode')}, "
                       f"Comment: {line.get('comment')}")
        
        # Calculate amounts for payable
        # nonDiscountableAmount = invoice total including GST
        discountable_amount = 0  # All amounts are non-discountable for stock purchases
        non_discountable_amount = round(calculated_total_inc_gst, 2)
        
        logger.info(f"Creating AP record: Total ${non_discountable_amount:.2f} (ex-GST: ${total_ex_gst:.2f}, GST: ${gst_amount:.2f})")
        
        # Create AP record
        ap_result = rfms_client.create_payable(
            supplier_name=supplier_name,
            invoice_number=invoice_data.get('invoice_number') or f"INV-{order_number}",
            invoice_date=invoice_date_formatted,
            due_date=due_date_formatted,
            discountable_amount=discountable_amount,
            non_discountable_amount=non_discountable_amount,
            discount_rate=0.0,
            linked_document_number=order_number,
            internal_notes=f"Stock received for order {order_number}",
            remittance_advice_notes="",
            detail_lines=detail_lines
        )
        
        if ap_result.get('status') == 'success':
            logger.info(f"AP record created: {ap_result.get('result')}")
            return True
        else:
            logger.error(f"AP record creation failed: {ap_result}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating AP record from invoice: {e}", exc_info=True)
        return False


@app.route('/api/receive-stock/search-invoice', methods=['POST'])
def search_email_for_invoice():
    """Search email for supplier invoice matching an order."""
    try:
        data = request.get_json()
        order_number = data.get('order_number')
        supplier_name = data.get('supplier_name')
        
        if not order_number or not supplier_name:
            return jsonify({
                'success': False,
                'error': 'Order number and supplier name are required'
            }), 400
        
        logger.info(f"Searching email for invoice: order {order_number}, supplier {supplier_name}")
        
        email_scraper = EmailScraper()
        emails = email_scraper.search_invoices(
            supplier_name=supplier_name,
            order_number=order_number,
            date_from=datetime.now() - timedelta(days=60),
            date_to=datetime.now()
        )
        
        # Try to analyze invoice attachments
        analyzer = DocumentAnalyzer()
        matched_invoices = []
        
        for email_data in emails:
            if email_data.get('is_invoice') and email_data.get('attachments'):
                # Download and analyze first PDF attachment
                attachment_data = email_scraper.download_invoice_attachment(email_data, 0)
                if attachment_data:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(attachment_data)
                        tmp_path = tmp_file.name
                    
                    try:
                        invoice_data = analyzer.analyze_supplier_invoice(tmp_path)
                        
                        # Check if invoice matches order
                        if email_scraper.match_invoice_to_order(invoice_data, order_number, supplier_name):
                            matched_invoices.append({
                                'email_subject': email_data.get('subject'),
                                'email_from': email_data.get('from'),
                                'email_date': email_data.get('date'),
                                'invoice_number': invoice_data.get('invoice_number'),
                                'invoice_date': invoice_data.get('invoice_date'),
                                'due_date': invoice_data.get('due_date'),
                                'total': invoice_data.get('total'),
                                'freight': invoice_data.get('freight'),
                                'baling_handling': invoice_data.get('baling_handling'),
                                'supplier_discount': invoice_data.get('supplier_discount'),
                                'line_items': invoice_data.get('line_items', [])
                            })
                    except Exception as e:
                        logger.warning(f"Error analyzing invoice: {e}")
                    finally:
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass
        
        return jsonify({
            'success': True,
            'matched_invoices': matched_invoices,
            'count': len(matched_invoices)
        })
        
    except Exception as e:
        logger.error(f"Error searching email for invoice: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/export/<int:pdf_id>', methods=['POST'])
def export_pdf_data(pdf_id):
    """Export PDF data directly to RFMS (used by manual enquiries)."""
    try:
        # Get the PDF data from database
        pdf_data = PdfData.query.get_or_404(pdf_id)
        
        if not pdf_data.extracted_data:
            return jsonify({'success': False, 'error': 'No extracted data found'}), 400
        
        # Prepare the data for the export-to-rfms endpoint
        extracted_data = pdf_data.extracted_data
        
        # Determine document type
        document_type_raw = extracted_data.get('document_type', 'quotation')
        logger.info(f"Export PDF Data - Raw document_type from extracted_data: '{document_type_raw}'")
        
        # Normalize document_type
        document_type = document_type_raw.strip().lower() if document_type_raw else 'quotation'
        # Map email types to their base types
        if document_type == 'email_quotation':
            document_type = 'quotation'
        elif document_type == 'email_order':
            document_type = 'purchase_order'
        elif document_type in ['order', 'sales_order', 'sales-order', 'purchase order']:
            document_type = 'purchase_order'
        elif document_type not in ['quotation', 'customer_enquiry', 'purchase_order']:
            logger.warning(f"Invalid document_type '{document_type_raw}', defaulting to 'quotation'")
            document_type = 'quotation'
        
        is_quote = document_type in ['quotation', 'customer_enquiry']
        logger.info(f"Export PDF Data - Normalized document_type: '{document_type}', is_quote: {is_quote}")
        
        # Prepare form data
        form_data = {
            'pdf_id': pdf_id,
            'po_number': extracted_data.get('po_number', ''),
            'dollar_value': extracted_data.get('dollar_value', 1.0),
            'measure_date': extracted_data.get('measure_date', ''),
            'estimated_delivery_date': extracted_data.get('estimated_delivery_date', ''),
            'install_date': extracted_data.get('install_date', ''),
            'is_provisional': extracted_data.get('is_provisional', False),
            'supervisor_name': extracted_data.get('supervisor_name', ''),
            'supervisor_phone': extracted_data.get('supervisor_phone', ''),
            'supervisor_mobile': extracted_data.get('supervisor_mobile', ''),
            'address1': extracted_data.get('address1', ''),
            'address2': extracted_data.get('address2', ''),
            'city': extracted_data.get('city', ''),
            'state': extracted_data.get('state', ''),
            'postal_code': extracted_data.get('postal_code', ''),
            'contact_first_name': extracted_data.get('contact_first_name', ''),
            'contact_last_name': extracted_data.get('contact_last_name', ''),
            'contact_mobile': extracted_data.get('contact_mobile', ''),
            'contact_phone': extracted_data.get('contact_phone', ''),
            'contact_email': extracted_data.get('contact_email', ''),
            'job_summary': extracted_data.get('job_summary', ''),
            'scope_of_work': extracted_data.get('scope_of_work', ''),
            'notes': extracted_data.get('notes', ''),  # Include notes/comments from manual entry
            'all_contacts': extracted_data.get('all_contacts', []),
            'date_status': extracted_data.get('date_status', ''),
            'appointment_time': extracted_data.get('appointment_time', ''),
            'use_sold_to_details': False
        }
        
        # For manual enquiries, create new customer (no existing builder)
        # Extract first and last name from customer name or use contact fields
        customer_name = extracted_data.get('customer_name', '')
        contact_first = extracted_data.get('contact_first_name', '')
        contact_last = extracted_data.get('contact_last_name', '')
        
        # If contact fields are empty, try to split customer name
        if not contact_first and not contact_last and customer_name:
            name_parts = customer_name.split(' ', 1)
            contact_first = name_parts[0] if name_parts else ''
            contact_last = name_parts[1] if len(name_parts) > 1 else ''
        
        sold_to_data = {
            'create_new': True,
            'first_name': contact_first,
            'last_name': contact_last,
            'business_name': extracted_data.get('business_name', ''),
            'phone': extracted_data.get('phone', ''),
            'mobile': extracted_data.get('phone2', ''),
            'email': extracted_data.get('email', ''),
            'address1': extracted_data.get('address1', ''),
            'address2': extracted_data.get('address2', ''),
            'city': extracted_data.get('city', ''),
            'state': extracted_data.get('state', ''),
            'postal_code': extracted_data.get('postal_code', '')
        }
        
        # Ship To data (use same as customer for manual enquiries)
        # For manual enquiries, Sold To and Ship To are always the same customer
        # So we should use the Sold To customer ID instead of creating a duplicate
        source = extracted_data.get('source', '')
        is_manual_enquiry = (source == 'manual_enquiry')
        
        ship_to_data = {
            'use_sold_to': is_manual_enquiry  # True for manual enquiries, False for PDF extractions (which may have different addresses)
        }
        
        logger.info(f"Manual enquiry detected: {is_manual_enquiry}, using Sold To as Ship To: {is_manual_enquiry}")
        
        # Prepare export data
        export_data = {
            'document_type': document_type,
            'form_data': form_data,
            'sold_to': sold_to_data,
            'ship_to': ship_to_data,
            'pdf_id': pdf_id
        }
        
        logger.info(f"Exporting manual enquiry {pdf_id} to RFMS")
        
        # Call the existing export-to-rfms logic
        # We'll reuse the logic from the export_to_rfms function
        return export_to_rfms_internal(export_data)
        
    except Exception as e:
        logger.error(f"Error exporting PDF data {pdf_id}: {str(e)}")
        return jsonify({'success': False, 'error': f'Error exporting data: {str(e)}'}), 500


def export_to_rfms_internal(data):
    """Internal function to handle RFMS export (extracted from export_to_rfms for reuse)."""
    try:
        # Get the data from the request
        if not data:
            logger.warning("No data provided for RFMS export")
            return jsonify({"error": "No data provided for export"}), 400
        
        logger.info(f"Starting RFMS export with data: {data.keys()}")
        
        # Determine document type (quote or purchase_order/work_order)
        document_type_raw = data.get('document_type') or 'purchase_order'
        logger.info(f"Export to RFMS Internal - Raw document_type from data: '{document_type_raw}'")
        
        document_type = (document_type_raw or 'purchase_order').strip().lower()
        if document_type in ['order', 'sales_order', 'sales-order', 'purchase order']:
            document_type = 'purchase_order'
        elif document_type not in ['quotation', 'customer_enquiry', 'purchase_order']:
            logger.warning(f"Invalid document_type '{document_type_raw}', defaulting to 'purchase_order'")
            document_type = 'purchase_order'
        is_quote = document_type in ['quotation', 'customer_enquiry']  # Both quotation and customer_enquiry create quotes
        
        logger.info(f"Export to RFMS Internal - Normalized document_type: '{document_type}', is_quote: {is_quote}")
        
        # Extract key data
        form_data = data.get('form_data', {})
        sold_to_data = data.get('sold_to', {})
        ship_to_data = data.get('ship_to', {})
        
        # Get configuration from pdf_data extracted_data if available
        pdf_data_config = PdfData.query.get(data.get('pdf_id'))
        config = pdf_data_config.extracted_data if pdf_data_config and pdf_data_config.extracted_data else {}

        # Determine extracted data payload for downstream use (attachments, defaults, etc.)
        extracted_data = data.get('extracted_data') or config or {}
        
        # Get configuration settings with fallback defaults
        salesperson = config.get('salesperson', 'ZORAN VEKIC')
        contract_type = config.get('contract_type', 'DEPOSIT & COD')
        order_type = config.get('order_type', 'RESIDENTIAL HOME')
        ad_source = config.get('ad_source', 'BUILDER CLIENT')
        labour_service_type = config.get('labour_service_type', 'SUPPLY & INSTALL')
        # Determine customer type: RESIDENTIAL for manual enquiries, BUILDERS for PDF extractions
        source = extracted_data.get('source', '')
        is_manual_enquiry = (source == 'manual_enquiry')
        customer_type = config.get('customer_type', 'RESIDENTIAL' if is_manual_enquiry else 'BUILDERS')
        logger.info(f"Configuration settings: salesperson={salesperson}, contract_type={contract_type}, order_type={order_type}, ad_source={ad_source}, labour_service_type={labour_service_type}, customer_type={customer_type}, is_manual_enquiry={is_manual_enquiry}")
        
        # Handle Sold To Customer (either existing builder or new customer)
        sold_to_customer_id = None
        
        if sold_to_data.get('create_new'):
            # Create new Sold To customer from form data
            logger.info("Creating new Sold To customer from form data")
            logger.info(f"Customer data - first_name: {sold_to_data.get('first_name', '')}, last_name: {sold_to_data.get('last_name', '')}, address1: {sold_to_data.get('address1', '')}")
            sold_to_customer_payload = {
                "customerType": customer_type,
                "entryType": "Customer",
                "customerAddress": {
                    "firstName": sold_to_data.get('first_name', ''),
                    "lastName": sold_to_data.get('last_name', ''),
                    "address1": sold_to_data.get('address1', ''),
                    "address2": sold_to_data.get('address2', ''),
                    "city": sold_to_data.get('city', ''),
                    "state": sold_to_data.get('state', ''),
                    "postalCode": sold_to_data.get('postal_code', '')
                },
                "shipToAddress": {
                    "firstName": sold_to_data.get('first_name', ''),
                    "lastName": sold_to_data.get('last_name', ''),
                    "address1": sold_to_data.get('address1', ''),
                    "address2": sold_to_data.get('address2', ''),
                    "city": sold_to_data.get('city', ''),
                    "state": sold_to_data.get('state', ''),
                    "postalCode": sold_to_data.get('postal_code', '')
                },
                "phone1": sold_to_data.get('phone', ''),
                "phone2": sold_to_data.get('mobile', ''),
                "email": sold_to_data.get('email', ''),
                "taxStatus": "Tax",
                "taxMethod": "SalesTax",
                "preferredSalesperson1": salesperson,
                "preferredSalesperson2": ""
            }
            # API will create or return existing customer ID
            logger.info(f"Sending customer creation payload to RFMS")
            sold_to_customer_id = rfms_client.create_client(sold_to_customer_payload)
            logger.info(f"RFMS response - customer ID: {sold_to_customer_id}")
            if sold_to_customer_id == 0:
                logger.error(f"RFMS returned customer ID 0. This may indicate a duplicate customer or validation issue.")
        else:
            # Use existing builder ID from search
            sold_to_customer_id = sold_to_data.get('id')
            logger.info(f"Using existing Sold To builder ID: {sold_to_customer_id}")
        
        if not sold_to_customer_id:
            logger.error("Failed to get Sold To customer ID")
            return jsonify({"error": "Failed to get Sold To customer ID"}), 400
        
        # Handle Ship To Customer
        ship_to_customer_id = None
        
        # Check if we should use Sold To as Ship To
        use_sold_to_as_ship_to = ship_to_data.get('use_sold_to', False)
        
        # Also check if addresses are the same (prevents creating duplicate customers)
        # Compare address, city, postal code, and name to determine if it's the same customer
        sold_to_key = f"{sold_to_data.get('address1', '').strip().upper()}|{sold_to_data.get('city', '').strip().upper()}|{sold_to_data.get('postal_code', '').strip()}|{sold_to_data.get('first_name', '').strip().upper()}|{sold_to_data.get('last_name', '').strip().upper()}"
        ship_to_key = f"{form_data.get('address1', '').strip().upper()}|{form_data.get('city', '').strip().upper()}|{form_data.get('postal_code', '').strip()}|{form_data.get('contact_first_name', '').strip().upper()}|{form_data.get('contact_last_name', '').strip().upper()}"
        addresses_match = sold_to_key == ship_to_key and sold_to_key.strip('|') != ''
        
        # Use Sold To as Ship To if explicitly set OR if addresses match (prevents duplicates)
        if use_sold_to_as_ship_to or addresses_match:
            # Use Sold To as Ship To - reuse the same customer ID to prevent duplicate
            ship_to_customer_id = sold_to_customer_id
            if addresses_match and not use_sold_to_as_ship_to:
                logger.info(f"Addresses match - reusing Sold To customer ID as Ship To to prevent duplicate: {ship_to_customer_id}")
            else:
                logger.info(f"Using Sold To as Ship To (use_sold_to=True or manual enquiry): {ship_to_customer_id}")
        else:
            # Create new Ship To customer from form data (only when addresses are genuinely different)
            logger.info("Creating new Ship To customer from form data (different address from Sold To)")
            customer_payload = {
                "customerType": "RESIDENTIAL",
                "entryType": "Customer",
                "customerAddress": {
                    "firstName": form_data.get('contact_first_name', ''),
                    "lastName": form_data.get('contact_last_name', ''),
                    "address1": form_data.get('address1', ''),
                    "address2": form_data.get('address2', ''),
                    "city": form_data.get('city', ''),
                    "state": form_data.get('state', ''),
                    "postalCode": form_data.get('postal_code', '')
                },
                "shipToAddress": {
                    "firstName": form_data.get('contact_first_name', ''),
                    "lastName": form_data.get('contact_last_name', ''),
                    "address1": form_data.get('address1', ''),
                    "address2": form_data.get('address2', ''),
                    "city": form_data.get('city', ''),
                    "state": form_data.get('state', ''),
                    "postalCode": form_data.get('postal_code', '')
                },
                "phone1": form_data.get('contact_mobile', ''),
                "phone2": form_data.get('contact_phone', ''),
                "email": form_data.get('contact_email', ''),
                "taxStatus": "Tax",
                "taxMethod": "SalesTax",
                "preferredSalesperson1": salesperson,
                "preferredSalesperson2": ""
            }
            # API will create or return existing customer ID
            ship_to_customer_id = rfms_client.create_client(customer_payload)
            logger.info(f"Ship To customer ID: {ship_to_customer_id}")
        
        if not ship_to_customer_id:
            logger.error("Failed to get Ship To customer ID")
            return jsonify({"error": "Failed to get Ship To customer ID"}), 400
        
        # Build job number from supervisor or contact info
        supervisor_name = form_data.get('supervisor_name', '')
        supervisor_phone = form_data.get('supervisor_phone', '')
        contact_name = f"{form_data.get('contact_first_name', '')} {form_data.get('contact_last_name', '')}".strip()
        
        if supervisor_name and supervisor_phone:
            job_number = f"{supervisor_name} {supervisor_phone}"
        elif contact_name:
            job_number = contact_name
        else:
            job_number = "Manual Enquiry"
        
        # Build addresses
        ship_to_address = {
            "firstName": form_data.get('contact_first_name', ''),
            "lastName": form_data.get('contact_last_name', ''),
            "address1": form_data.get('address1', ''),
            "address2": form_data.get('address2', ''),
            "city": form_data.get('city', ''),
            "state": form_data.get('state', ''),
            "postalCode": form_data.get('postal_code', '')
        }
        
        # Build notes
        po_number = form_data.get('po_number', '')
        scope_of_work = form_data.get('scope_of_work', '')
        job_summary = form_data.get('job_summary', '')
        notes = form_data.get('notes', '')  # Get notes/comments from manual entry
        all_contacts = form_data.get('all_contacts', [])
        
        # Get appointment information for public notes
        date_status = form_data.get('date_status', '')
        appointment_time = form_data.get('appointment_time', '')
        
        # Build private notes - include notes/comments if present
        private_notes = f"PO: {po_number}\nJob Summary: {job_summary}"
        if notes:
            private_notes += f"\n\nNotes & Comments:\n{notes}"
        if all_contacts:
            private_notes += f"\nAdditional Contacts: {len(all_contacts)} contacts found"
        
        # Build public notes - include scope of work, date status, and appointment time
        public_notes = scope_of_work
        if date_status:
            public_notes += f"\n\nDate Status: {date_status}"
        if appointment_time:
            public_notes += f"\nAppointment Time: {appointment_time}"
        
        work_order_notes = f"Manual Enquiry - {po_number}"
        
        # Handle dates
        delivery_date = form_data.get('estimated_delivery_date', '')
        measure_date = form_data.get('measure_date', '')
        install_date = form_data.get('install_date', '')
        
        # Use install_date for delivery_date if provided, otherwise use measure_date, otherwise default
        if install_date:
            delivery_date = install_date
        elif measure_date:
            delivery_date = measure_date
        elif not delivery_date:
            delivery_date = '2024-12-31'  # Default date
        
        # Get amount
        amount = float(form_data.get('dollar_value', 1))
        
        # Map configuration values to RFMS IDs
        contract_type_id = get_contract_type_id(contract_type)
        order_type_id = get_order_type_id(order_type)
        ad_source_id = get_ad_source_id(ad_source)
        labour_service_type_id = get_labour_service_type_id(labour_service_type) if labour_service_type else 9  # Default to SUPPLY & INSTALL
        
        logger.info(f"Mapped configuration IDs: contract_type_id={contract_type_id}, order_type_id={order_type_id}, ad_source_id={ad_source_id}, labour_service_type_id={labour_service_type_id}")
        
        rfms_payload = {
            "category": "Quote" if is_quote else "Order",
            "jobNumber": job_number,
            "poNumber": po_number,
            "estimatedDeliveryDate": delivery_date,
            "measureDate": measure_date,
            "soldTo": {
                "customerType": customer_type,
                "customerId": sold_to_customer_id,
                "phone1": form_data.get('contact_mobile', ''),
                "phone2": form_data.get('contact_phone', '')
            },
            "lines": [
                {
                    "productId": "1265",
                    "productCode": "38",
                    "styleName": "PURCHASE ORDER VALUE EX GST",
                    "styleNumber": "PO$VALUE",
                    "colorId": "3072",
                    "colorName": "PO$VALUE",
                    "colorNumber": "$$XGST",
                    "quantity": amount,
                    "priceLevel": "Price10",
                    "lineGroupId": "4"
                }
            ],
            "products": [
                {
                    "productId": "1265",
                    "colorId": "3072",
                    "quantity": amount,
                    "priceLevel": "10",
                    "lineGroupId": "4"
                }
            ],
            "shipTo": ship_to_address,
            "storeNumber": "49",
            "privateNotes": private_notes,
            "publicNotes": public_notes,
            "workOrderNotes": work_order_notes,
            "salesperson1": salesperson,
            "userOrderTypeId": order_type_id,
            "serviceTypeId": labour_service_type_id,
            "contractTypeId": contract_type_id,
            "adSource": ad_source,
            "priceLevel": "3",
            # "adSourceId": str(ad_source_id)
        }
        
        logger.info(f"Processing {'QUOTE' if is_quote else 'ORDER'} for PO: {po_number}, category in payload: {rfms_payload.get('category')}")
        rfms_result = rfms_client.process_quote(po_number, rfms_payload) if is_quote else rfms_client.process_po_order(po_number, rfms_payload)
        logger.info(f"RFMS Result: {rfms_result}")

        if not rfms_result:
            logger.error("RFMS returned an empty response")
            return jsonify({"error": "No response from RFMS"}), 500

        doc_details = extract_rfms_document_details(rfms_result, is_quote)
        status = doc_details['status']
        raw_doc_number = doc_details['raw_document_number']
        display_doc_number = doc_details['display_document_number'] or raw_doc_number
        parent_document = doc_details['parent_document']
        logger.info(f"RFMS status={status}, document_number={display_doc_number}, parent_document={parent_document}")

        # Collect attachments (PDF, email attachments, and manual enquiry uploads)
        attachments_to_upload = []

        file_path = session.get('file_path')
        if file_path and os.path.exists(file_path):
            # Only attach PDF/image files, not .msg email files (we'll attach email attachments instead)
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext != '.msg':
                attachments_to_upload.append({
                    'path': file_path,
                    'description': os.path.basename(file_path)
                })

        # Add email attachments (extracted from .msg files)
        email_attachments = session.get('email_attachments', []) or extracted_data.get('email_attachments', [])
        for attachment in email_attachments:
            stored_path = attachment.get('path')
            if not stored_path:
                continue
            absolute_path = stored_path if os.path.isabs(stored_path) else os.path.join(app.root_path, stored_path)
            if not os.path.exists(absolute_path):
                logger.warning("Email attachment path not found: %s", absolute_path)
                continue
            attachments_to_upload.append({
                'path': absolute_path,
                'description': attachment.get('original_filename') or os.path.basename(absolute_path)
            })

        manual_attachments = extracted_data.get('attachments', []) if extracted_data else []
        for attachment in manual_attachments:
            stored_path = attachment.get('path')
            if not stored_path:
                continue
            absolute_path = stored_path if os.path.isabs(stored_path) else os.path.join(app.root_path, stored_path)
            if not os.path.exists(absolute_path):
                logger.warning("Attachment path not found: %s", absolute_path)
                continue
            attachments_to_upload.append({
                'path': absolute_path,
                'description': attachment.get('original_filename') or os.path.basename(absolute_path)
            })

        if attachments_to_upload and raw_doc_number:
            try:
                for attachment in attachments_to_upload:
                    rfms_client.add_attachment(
                        document_number=raw_doc_number,
                        file_path=attachment['path'],
                        document_type='Quote' if is_quote else 'Order',
                        description=attachment['description']
                    )
                    logger.info("Attached %s to document %s", attachment['description'], raw_doc_number)
            except Exception as e:
                logger.error(f"Failed to attach supplementary files: {str(e)}")

        # Update database tracking
        document_type_response = 'quote' if is_quote else 'order'
        pdf_id = data.get('pdf_id')
        if pdf_id:
            pdf_record = PdfData.query.get(pdf_id)
            if pdf_record:
                if status in ['new_order', 'billing_group_added', 'new_quote']:
                    pdf_record.processed = True
                pdf_record.rfms_status = status
                if display_doc_number:
                    pdf_record.rfms_document_number = display_doc_number
                db.session.commit()

                if display_doc_number and status in ['new_quote']:
                    quote_record = Quote(
                        quote_number=display_doc_number,
                        customer_name=f"{form_data.get('contact_first_name', '')} {form_data.get('contact_last_name', '')}".strip(),
                        amount=amount,
                        created_at=datetime.now()
                    )
                    db.session.add(quote_record)
                    db.session.commit()
                    logger.info(f"Created Quote record for {display_doc_number}")
                elif display_doc_number and status in ['new_order', 'billing_group_added']:
                    job_record = Job(
                        job_number=display_doc_number,
                        customer_name=f"{form_data.get('contact_first_name', '')} {form_data.get('contact_last_name', '')}".strip(),
                        amount=amount,
                        created_at=datetime.now()
                    )
                    db.session.add(job_record)
                    db.session.commit()
                    logger.info(f"Created Job record for {display_doc_number}")

        additional_info = None
        if status == 'existing_order':
            additional_info = (
                f"Purchase order already exists. The uploaded document was attached to order {display_doc_number}."
                if display_doc_number else
                "Purchase order already exists. The uploaded document was attached to the existing order."
            )
        elif status == 'existing_quote':
            additional_info = (
                f"Quote already exists. The uploaded document was attached to quote {display_doc_number}."
                if display_doc_number else
                "Quote already exists. The uploaded document was attached to the existing quote."
            )
        elif status == 'billing_group_added' and parent_document:
            additional_info = (
                f"Order {display_doc_number or raw_doc_number} created and linked to billing group on parent order {parent_document}."
            )

        if not status:
            logger.warning("RFMS response missing status")

        success_message = 'Corresponding document successfully created in RFMS'
        if display_doc_number:
            success_message = f'{success_message} with reference # {display_doc_number}'
        elif raw_doc_number:
            success_message = f'{success_message} with reference # {raw_doc_number}'

        return jsonify({
            'success': True,
            'status': status,
            'document_type': document_type_response,
            'document_number': display_doc_number or raw_doc_number,
            'raw_document_number': raw_doc_number,
            'additional_info': additional_info,
            'parent_document': parent_document,
            'message': success_message,
            'rfms_result': rfms_result,
            'sold_to_customer_id': sold_to_customer_id,
            'ship_to_customer_id': ship_to_customer_id,
            'customers_created': 1 if (ship_to_customer_id == sold_to_customer_id) else 2
        })
                
    except Exception as e:
        logger.error(f"Error in RFMS export: {str(e)}")
        return jsonify({"error": f"Export failed: {str(e)}"}), 500


# Installer Photos Utility Functions
def is_installer_photo(attachment: Dict) -> bool:
    """Check if an attachment is tagged as an installer photo."""
    description = str(attachment.get('description', '') or '').upper()
    tag = str(attachment.get('tag', '') or '').upper()
    attachment_type = str(attachment.get('type', '') or '').upper()
    name = str(attachment.get('name', '') or '').upper()
    title = str(attachment.get('title', '') or '').upper()
    
    search_fields = [description, tag, attachment_type, name, title]
    for field in search_fields:
        if 'INSTALLER PHOTOS' in field or 'INSTALLER PHOTO' in field:
            return True
    return False


def download_rfms_attachment(rfms_client: RFMSClient, attachment: Dict, output_dir: Path) -> Path:
    """Download an attachment from RFMS and save it to disk."""
    attachment_id = (attachment.get('id') or 
                    attachment.get('attachmentId') or 
                    attachment.get('attachment_id'))
    if not attachment_id:
        raise ValueError(f"Attachment missing ID: {attachment}")
    
    logger.info(f"Downloading attachment {attachment_id}...")
    attachment_data = rfms_client.get_attachment(attachment_id)
    
    # Handle different response structures
    file_data_b64 = None
    
    if isinstance(attachment_data, dict):
        detail = attachment_data.get('detail')
        if isinstance(detail, str):
            file_data_b64 = detail
        elif isinstance(detail, dict):
            file_data_b64 = detail.get('fileData') or detail.get('data') or detail.get('file')
        
        if not file_data_b64:
            file_data_b64 = (attachment_data.get('fileData') or 
                            attachment_data.get('data') or
                            attachment_data.get('file'))
        
        if not file_data_b64:
            result = attachment_data.get('result')
            if isinstance(result, str) and result != 'OK':
                file_data_b64 = result
            elif isinstance(result, dict):
                file_data_b64 = result.get('fileData') or result.get('data') or result.get('file')
    
    elif isinstance(attachment_data, str):
        file_data_b64 = attachment_data
    
    if not file_data_b64:
        raise ValueError(f"Attachment {attachment_id} has no file data")
    
    # Decode base64 data
    try:
        file_bytes = base64.b64decode(file_data_b64)
    except Exception as e:
        logger.error(f"Failed to decode attachment {attachment_id}: {e}")
        raise
    
    # Determine file extension
    file_extension = None
    if isinstance(attachment_data, dict):
        file_extension = attachment_data.get('fileExtension') or attachment_data.get('extension')
    if not file_extension:
        file_extension = attachment.get('fileExtension') or 'jpg'
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
    """Compress an image file."""
    try:
        from PIL import Image
    except ImportError:
        logger.warning("Pillow not available, skipping compression")
        return image_path
    
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
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
            logger.info(f"Compressed {image_path.name}: {original_size:,} bytes -> {compressed_size:,} bytes")
            
            return compressed_path
    except Exception as e:
        logger.error(f"Failed to compress {image_path}: {e}")
        return image_path


def create_pdf_from_images(image_paths: List[Path], output_pdf_path: Path, order_details: Dict = None) -> Path:
    """Create a PDF file from a list of image paths with optional order details header."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open()
        
        # Calculate header height if order details provided
        header_height = 0
        if order_details:
            header_height = 80  # Height for header with order details
        
        for img_path in image_paths:
            try:
                from PIL import Image
                img = Image.open(img_path)
                img_width, img_height = img.size
                
                # Create page with space for header
                page_height = img_height + header_height
                page = doc.new_page(width=img_width, height=page_height)
                
                # Add header if order details provided
                if order_details and header_height > 0:
                    add_pdf_header(page, order_details, img_width, header_height)
                
                # Insert image below header
                image_rect = fitz.Rect(0, header_height, img_width, page_height)
                page.insert_image(image_rect, filename=str(img_path))
            except Exception as e:
                logger.error(f"Failed to add image {img_path} to PDF: {e}")
                continue
        
        doc.save(str(output_pdf_path))
        doc.close()
        logger.info(f"Created PDF with {len(image_paths)} images: {output_pdf_path}")
        return output_pdf_path
    except ImportError:
        raise ImportError("PyMuPDF (pymupdf) is required for PDF creation")


def add_pdf_header(page, order_details: Dict, page_width: float, header_height: float):
    """Add order details header to a PDF page."""
    try:
        margin = 10
        y_pos = 8
        
        # Draw header background
        header_rect = fitz.Rect(0, 0, page_width, header_height)
        page.draw_rect(header_rect, color=(0.94, 0.94, 0.94), fill=(0.94, 0.94, 0.94))
        
        # Get order information
        order_number = order_details.get('order_number', 'N/A')
        po_number = order_details.get('po_number', '')
        sold_to_name = order_details.get('sold_to_name', '')
        ship_to_name = order_details.get('ship_to_name', '')
        address = order_details.get('address', '')
        city = order_details.get('city', '')
        
        # Order Number (left side, bold)
        page.insert_text(
            (margin, y_pos),
            f"Order: {order_number}",
            fontsize=10,
            color=(0, 0, 0),
            fontname="helv",
            render_mode=3  # Bold
        )
        
        # PO Number (right side, if available)
        if po_number:
            po_text = f"PO: {po_number}"
            text_width = page.get_text_length(po_text, fontsize=10, fontname="helv")
            page.insert_text(
                (page_width - margin - text_width, y_pos),
                po_text,
                fontsize=10,
                color=(0, 0, 0)
            )
        
        y_pos += 15
        
        # Builder/Customer Name (left side, bold)
        if sold_to_name:
            page.insert_text(
                (margin, y_pos),
                f"Builder/Customer: {sold_to_name}",
                fontsize=10,
                color=(0, 0, 0),
                fontname="helv",
                render_mode=3  # Bold
            )
        
        y_pos += 15
        
        # Ship To Customer (if different from sold to)
        if ship_to_name and ship_to_name != sold_to_name:
            page.insert_text(
                (margin, y_pos),
                f"Ship To: {ship_to_name}",
                fontsize=10,
                color=(0, 0, 0)
            )
            y_pos += 15
        
        # Address (if available)
        if address or city:
            address_text = f"{address}, {city}".strip(', ')
            if address_text:
                # Truncate if too long
                max_width = page_width - (2 * margin)
                if page.get_text_length(address_text, fontsize=10) > max_width:
                    while page.get_text_length(address_text + '...', fontsize=10) > max_width and len(address_text) > 0:
                        address_text = address_text[:-1]
                    address_text += '...'
                page.insert_text(
                    (margin, y_pos),
                    f"Address: {address_text}",
                    fontsize=10,
                    color=(0, 0, 0)
                )
        
        # Draw line under header
        line_y = header_height - 5
        page.draw_line(
            (margin, line_y),
            (page_width - margin, line_y),
            color=(0.78, 0.78, 0.78),
            width=1
        )
    except Exception as e:
        logger.error(f"Failed to add PDF header: {e}")


# Installer Photos Routes
@app.route('/installer-photos')
def installer_photos():
    """Render installer photos page with cache-busting headers"""
    response = make_response(render_template('installer_photos.html'))
    # Add cache-busting headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
    """Installer photos extraction page."""
    return render_template('installer_photos.html')


@app.route('/api/fetch-order-attachments', methods=['POST'])
def fetch_order_attachments():
    """API endpoint to fetch attachments for an order."""
    try:
        data = request.get_json()
        # Convert RFMS-related fields to uppercase
        data = uppercase_rfms_fields(data)
        order_number = data.get('order_number', '').strip()
        
        if not order_number:
            return jsonify({'success': False, 'error': 'Order number is required'}), 400
        
        logger.info(f"Fetching attachments for order {order_number}...")
        
        # Get order details
        order_data = rfms_client.get_order(order_number, locked=False, include_attachments=True)
        
        # Extract attachments - USE ORIGINAL WORKING LOGIC (don't change this!)
        attachments = []
        if isinstance(order_data, dict):
            # Check various possible locations for attachments (ORIGINAL WORKING CODE)
            detail = order_data.get('detail')
            data_obj = order_data.get('data')  # Fixed: renamed to avoid collision with request 'data' variable
            result = order_data.get('result')
            
            attachments = (order_data.get('attachments') or 
                          (result.get('attachments') if isinstance(result, dict) else None) or
                          (detail.get('attachments') if isinstance(detail, dict) else None) or
                          (data_obj.get('attachments') if isinstance(data_obj, dict) else None) or
                          [])
            
            # Also try checking nested structures (ORIGINAL WORKING CODE)
            if not attachments and isinstance(result, dict):
                attachments = result.get('attachments') or result.get('order', {}).get('attachments') or []
            if not attachments and isinstance(detail, dict):
                attachments = detail.get('attachments') or detail.get('order', {}).get('attachments') or []
        
        # Extract order details for the card (NEW - only add this, don't change attachments above)
        order_details = {}
        if isinstance(order_data, dict):
            # Try multiple possible locations for order detail
            order_detail = None
            detail = order_data.get('detail')
            result = order_data.get('result')
            data_obj = order_data.get('data')
            
            # Find the actual order data - try multiple locations
            if isinstance(result, dict):
                order_detail = result
            elif isinstance(detail, dict):
                order_detail = detail
            elif isinstance(data_obj, dict):
                order_detail = data_obj
            elif order_data.get('number') or order_data.get('orderNumber'):  # Order data might be at root level
                order_detail = order_data
            
            # Extract order information from order_detail
            # Using exact field names from RFMS API documentation:
            # result.number, result.poNumber, result.soldTo, result.shipTo, result.estimatedDeliveryDate, result.measureDate
            if isinstance(order_detail, dict):
                # Get soldTo and shipTo objects (exact API field names: soldTo, shipTo)
                sold_to = order_detail.get('soldTo') or {}
                ship_to = order_detail.get('shipTo') or {}
                
                # Format sold to name (API fields: businessName, firstName, lastName)
                sold_to_name = ''
                if sold_to.get('businessName'):
                    sold_to_name = sold_to.get('businessName')
                elif sold_to.get('firstName') or sold_to.get('lastName'):
                    sold_to_name = f"{sold_to.get('firstName', '')} {sold_to.get('lastName', '')}".strip()
                
                # Format ship to name (API fields: businessName, firstName, lastName)
                ship_to_name = ''
                if ship_to.get('businessName'):
                    ship_to_name = ship_to.get('businessName')
                elif ship_to.get('firstName') or ship_to.get('lastName'):
                    ship_to_name = f"{ship_to.get('firstName', '')} {ship_to.get('lastName', '')}".strip()
                
                # Build order_details dict with correct API field names
                order_details = {
                    'order_number': order_detail.get('number') or order_number,  # API: result.number
                    'po_number': order_detail.get('poNumber') or '',  # API: result.poNumber
                    'sold_to_name': sold_to_name,  # From result.soldTo.businessName or firstName+lastName
                    'ship_to_name': ship_to_name,  # From result.shipTo.businessName or firstName+lastName
                    'address': ship_to.get('address1') or sold_to.get('address1') or '',  # API: result.shipTo.address1
                    'address2': ship_to.get('address2') or sold_to.get('address2') or '',  # API: result.shipTo.address2
                    'city': ship_to.get('city') or sold_to.get('city') or '',  # API: result.shipTo.city
                    'state': ship_to.get('state') or sold_to.get('state') or '',  # API: result.shipTo.state
                    'postal_code': ship_to.get('postalCode') or sold_to.get('postalCode') or '',  # API: result.shipTo.postalCode
                    'estimated_delivery_date': order_detail.get('estimatedDeliveryDate') or '',  # API: result.estimatedDeliveryDate
                    'measure_date': order_detail.get('measureDate') or '',  # API: result.measureDate
                }
                
                # Installation date: prefer measureDate (scheduled lay date), then estimatedDeliveryDate
                installation_date = order_details.get('measure_date') or order_details.get('estimated_delivery_date') or ''
                order_details['installation_date'] = installation_date
        
        # Mark installer photos
        for attachment in attachments:
            attachment['is_installer_photo'] = is_installer_photo(attachment)
        
        # Add file type information for thumbnails
        for attachment in attachments:
            attachment_id = attachment.get('id') or attachment.get('attachmentId') or attachment.get('attachment_id')
            description = attachment.get('description', '') or attachment.get('name', '') or attachment.get('title', '') or ''
            
            # Try multiple sources for file extension
            # 1. Check fileExtension field from RFMS API
            file_extension = attachment.get('fileExtension') or attachment.get('extension') or attachment.get('file_extension') or ''
            
            # 2. If not found, try to extract from description/name
            if not file_extension and '.' in description:
                file_extension = description.lower().split('.')[-1]
            
            # 3. Check contentType/mimeType if available
            if not file_extension:
                content_type = attachment.get('contentType') or attachment.get('mimeType') or attachment.get('content_type') or ''
                if 'image' in content_type.lower():
                    # Extract extension from content type (e.g., "image/jpeg" -> "jpeg")
                    if '/' in content_type:
                        file_extension = content_type.split('/')[-1].split(';')[0].strip()
            
            # Clean up extension (remove leading dot if present)
            if file_extension:
                file_extension = file_extension.lstrip('.').lower()
            
            attachment['file_type'] = file_extension
            attachment['is_image'] = file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'heic', 'heif']
            
            # Log for debugging
            if attachment_id:
                logger.debug(f"Attachment {attachment_id}: file_type={file_extension}, is_image={attachment['is_image']}, description={description[:50]}")
        
        # Log attachment breakdown
        installer_photos_count = sum(1 for a in attachments if a.get('is_installer_photo'))
        image_count = sum(1 for a in attachments if a.get('is_image'))
        logger.info(f"Found {len(attachments)} total attachments for order {order_number}")
        logger.info(f"  - Installer photos: {installer_photos_count}")
        logger.info(f"  - Images: {image_count}")
        logger.info(f"  - Other files: {len(attachments) - image_count}")
        logger.info(f"Order details extracted: {bool(order_details)}, keys: {list(order_details.keys()) if order_details else 'empty'}")
        
        return jsonify({
            'success': True,
            'order_number': order_number,
            'attachments': attachments,  # ALL attachments, not filtered
            'total': len(attachments),
            'installer_photos_count': installer_photos_count,
            'image_count': image_count,
            'order_details': order_details if order_details else {}
        })
    
    except Exception as e:
        logger.error(f"Error fetching order attachments: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/attachment-thumbnail/<int:attachment_id>')
def get_attachment_thumbnail(attachment_id):
    """API endpoint to get a thumbnail preview of an attachment."""
    try:
        # Get attachment data
        attachment_data = rfms_client.get_attachment(attachment_id)
        
        # Handle different response structures to get file data
        file_data_b64 = None
        
        if isinstance(attachment_data, dict):
            detail = attachment_data.get('detail')
            if isinstance(detail, str):
                file_data_b64 = detail
            elif isinstance(detail, dict):
                file_data_b64 = detail.get('fileData') or detail.get('data') or detail.get('file')
            
            if not file_data_b64:
                file_data_b64 = (attachment_data.get('fileData') or 
                                attachment_data.get('data') or
                                attachment_data.get('file'))
        
        if not file_data_b64:
            return jsonify({'success': False, 'error': 'No file data found'}), 404
        
        # Decode base64 data
        try:
            file_bytes = base64.b64decode(file_data_b64)
        except Exception as e:
            logger.error(f"Failed to decode attachment {attachment_id}: {e}")
            return jsonify({'success': False, 'error': 'Failed to decode attachment'}), 500
        
        # Determine if it's an image - try multiple sources
        file_extension = None
        if isinstance(attachment_data, dict):
            file_extension = (attachment_data.get('fileExtension') or 
                            attachment_data.get('extension') or 
                            attachment_data.get('file_extension'))
            
            # If not found, try content type
            if not file_extension:
                content_type = attachment_data.get('contentType') or attachment_data.get('mimeType') or attachment_data.get('content_type') or ''
                if 'image' in content_type.lower() and '/' in content_type:
                    file_extension = content_type.split('/')[-1].split(';')[0].strip()
        
        # Default to jpg if still not found (common for installer photos)
        if not file_extension:
            file_extension = 'jpg'
        
        # Clean up extension (remove leading dot if present)
        file_extension = file_extension.lstrip('.').lower()
        
        is_image = file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'heic', 'heif']
        
        # For images, create a thumbnail
        if is_image:
            try:
                from PIL import Image as PILImage
                import io
                
                # Open image
                img = PILImage.open(io.BytesIO(file_bytes))
                
                # Create thumbnail (max 200x200)
                img.thumbnail((200, 200), PILImage.Resampling.LANCZOS)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = PILImage.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save to bytes
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85)
                thumbnail_bytes = output.getvalue()
                
                # Return as image response
                from flask import Response
                return Response(thumbnail_bytes, mimetype='image/jpeg')
                
            except Exception as e:
                logger.error(f"Failed to create thumbnail for attachment {attachment_id}: {e}")
                # Return original image if thumbnail fails
                return Response(file_bytes, mimetype=f'image/{file_extension.replace(".", "")}')
        else:
            # For non-images, return a generic file icon or 404
            # Could create a PDF thumbnail here in the future
            return jsonify({'success': False, 'error': 'Preview not available for this file type'}), 404
    
    except Exception as e:
        logger.error(f"Error getting attachment thumbnail {attachment_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/attachment-file/<int:attachment_id>')
def get_attachment_file(attachment_id):
    """API endpoint to get the full attachment file."""
    try:
        # Check if thumbnail is requested
        thumbnail = request.args.get('thumbnail', 'false').lower() == 'true'
        
        # Get attachment data
        attachment_data = rfms_client.get_attachment(attachment_id)
        
        # Handle different response structures to get file data
        file_data_b64 = None
        
        if isinstance(attachment_data, dict):
            detail = attachment_data.get('detail')
            if isinstance(detail, str):
                file_data_b64 = detail
            elif isinstance(detail, dict):
                file_data_b64 = detail.get('fileData') or detail.get('data') or detail.get('file')
            
            if not file_data_b64:
                file_data_b64 = (attachment_data.get('fileData') or 
                                attachment_data.get('data') or
                                attachment_data.get('file'))
        
        if not file_data_b64:
            return jsonify({'success': False, 'error': 'No file data found'}), 404
        
        # Decode base64 data
        try:
            file_bytes = base64.b64decode(file_data_b64)
        except Exception as e:
            logger.error(f"Failed to decode attachment {attachment_id}: {e}")
            return jsonify({'success': False, 'error': 'Failed to decode attachment'}), 500
        
        # Get content type
        file_extension = None
        if isinstance(attachment_data, dict):
            file_extension = (attachment_data.get('fileExtension') or 
                            attachment_data.get('extension') or 
                            attachment_data.get('file_extension'))
            
            if not file_extension:
                content_type = attachment_data.get('contentType') or attachment_data.get('mimeType') or ''
                if 'image' in content_type.lower() and '/' in content_type:
                    file_extension = content_type.split('/')[-1].split(';')[0].strip()
        
        if not file_extension:
            file_extension = 'jpg'  # Default for images
        
        file_extension = file_extension.lstrip('.').lower()
        
        # Determine MIME type
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
            'webp': 'image/webp',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }
        content_type = mime_types.get(file_extension, 'application/octet-stream')
        
        # If thumbnail requested and it's an image, create thumbnail
        if thumbnail and file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
            try:
                from PIL import Image as PILImage
                import io
                
                img = PILImage.open(io.BytesIO(file_bytes))
                img.thumbnail((200, 200), PILImage.Resampling.LANCZOS)
                
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = PILImage.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85)
                file_bytes = output.getvalue()
                content_type = 'image/jpeg'
            except Exception as e:
                logger.warning(f"Failed to create thumbnail for attachment {attachment_id}: {e}")
                # Return original image if thumbnail fails
        
        # Return as file response
        from flask import Response
        return Response(file_bytes, mimetype=content_type)
    
    except Exception as e:
        logger.error(f"Error getting attachment file {attachment_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/create-installer-pdf', methods=['POST'])
def create_installer_pdf():
    """API endpoint to create PDF from selected attachments."""
    try:
        data = request.get_json()
        order_number = data.get('order_number', '').strip().upper()
        attachment_ids = data.get('attachment_ids', [])
        
        if not order_number:
            return jsonify({'success': False, 'error': 'Order number is required'}), 400
        
        if not attachment_ids:
            return jsonify({'success': False, 'error': 'At least one attachment must be selected'}), 400
        
        logger.info(f"Creating PDF for order {order_number} with {len(attachment_ids)} attachments...")
        
        # Get order details to find selected attachments
        order_data = rfms_client.get_order(order_number, locked=False, include_attachments=True)
        
        # Extract attachments
        attachments = []
        if isinstance(order_data, dict):
            detail = order_data.get('detail')
            result = order_data.get('result')
            data_obj = order_data.get('data')
            
            attachments = (order_data.get('attachments') or 
                          (result.get('attachments') if isinstance(result, dict) else None) or
                          (detail.get('attachments') if isinstance(detail, dict) else None) or
                          (data_obj.get('attachments') if isinstance(data_obj, dict) else None) or
                          [])
        
        # Filter selected attachments
        # Convert attachment_ids to strings for comparison (handles both int and str types)
        attachment_ids_set = {str(aid) for aid in attachment_ids}
        selected_attachments = []
        for attachment in attachments:
            attachment_id = (attachment.get('id') or 
                           attachment.get('attachmentId') or 
                           attachment.get('attachment_id'))
            # Convert attachment_id to string for comparison
            if attachment_id and str(attachment_id) in attachment_ids_set:
                selected_attachments.append(attachment)
        
        if not selected_attachments:
            logger.warning(f"No matching attachments found for IDs: {attachment_ids}")
            logger.warning(f"Available attachments: {[att.get('id') or att.get('attachmentId') for att in attachments]}")
            return jsonify({'success': False, 'error': f'No matching attachments found for the selected IDs. Found {len(attachments)} total attachments for this order.'}), 400
        
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix=f"installer_photos_{order_number}_"))
        logger.info(f"Working directory: {temp_dir}")
        
        try:
            # Download attachments and keep track of which are installer photos
            downloaded_files = []
            attachment_file_map = []  # List of tuples: (attachment, file_path, is_installer_photo)
            
            for attachment in selected_attachments:
                try:
                    file_path = download_rfms_attachment(rfms_client, attachment, temp_dir)
                    is_installer = is_installer_photo(attachment)
                    downloaded_files.append(file_path)
                    attachment_file_map.append((attachment, file_path, is_installer))
                except Exception as e:
                    logger.error(f"Failed to download attachment {attachment.get('id')}: {e}")
                    continue
            
            if not downloaded_files:
                return jsonify({'success': False, 'error': 'No attachments were successfully downloaded'}), 500
            
            # Compress images
            compressed_files = []
            compressed_attachment_map = []  # Updated map with compressed paths
            for attachment, file_path, is_installer in attachment_file_map:
                try:
                    if not file_path.exists():
                        logger.error(f"Downloaded file does not exist: {file_path}")
                        continue
                    
                    compressed_path = compress_image(file_path)
                    if compressed_path.exists():
                        compressed_files.append(compressed_path)
                        compressed_attachment_map.append((attachment, compressed_path, is_installer))
                    else:
                        logger.warning(f"Compressed file was not created, using original: {file_path}")
                        compressed_files.append(file_path)
                        compressed_attachment_map.append((attachment, file_path, is_installer))
                except Exception as e:
                    logger.warning(f"Failed to compress {file_path}: {e}, using original")
                    if file_path.exists():
                        compressed_files.append(file_path)
                        compressed_attachment_map.append((attachment, file_path, is_installer))
            
            if not compressed_files:
                logger.error("No files available for PDF creation after compression step")
                return jsonify({'success': False, 'error': 'No valid image files available for PDF creation'}), 500
            
            # Set network folder to shared server location
            network_folder = r'\\AtozServer\AtoZ ShareDrive\BUILDERS INVOICE PICTURES'
            try:
                os.makedirs(network_folder, exist_ok=True)
                logger.info(f"Network folder: {network_folder}")
            except Exception as e:
                logger.error(f"Failed to access network folder {network_folder}: {e}")
                # Fallback to local folder if network is unavailable
                network_folder = os.getenv('INSTALLER_PHOTOS_FOLDER', os.path.join(app.config['UPLOAD_FOLDER'], 'installer_photos'))
                os.makedirs(network_folder, exist_ok=True)
                logger.warning(f"Using fallback folder: {network_folder}")
            
            # Save individual installer photos to network folder
            installer_photo_count = 0
            for attachment, file_path, is_installer in compressed_attachment_map:
                if is_installer:
                    installer_photo_count += 1
                    # Get file extension from original attachment or file
                    file_extension = attachment.get('fileExtension', '')
                    if not file_extension:
                        # Try to get from file path
                        file_extension = Path(file_path).suffix
                    if not file_extension or file_extension == '':
                        file_extension = '.jpg'  # Default to jpg
                    if not file_extension.startswith('.'):
                        file_extension = '.' + file_extension
                    
                    # Create filename: {ORDER_NUMBER}_install_Photo_{NUMBER}
                    individual_filename = f"{order_number}_install_Photo_{installer_photo_count}{file_extension}"
                    individual_path = Path(network_folder) / individual_filename
                    
                    try:
                        # Copy the file to network location
                        shutil.copy2(file_path, individual_path)
                        logger.info(f"Saved installer photo to network folder: {individual_path}")
                    except Exception as e:
                        logger.error(f"Failed to save installer photo {individual_filename} to network folder: {e}")
            
            # Create PDF
            pdf_filename = f"{order_number}_installer_photos.pdf"
            
            # Get order details for PDF header
            pdf_order_details = {}
            if isinstance(order_data, dict):
                result = order_data.get('result', {})
                if result:
                    sold_to = result.get('soldTo', {})
                    ship_to = result.get('shipTo', {})
                    
                    # Build customer names
                    sold_to_name = (sold_to.get('businessName') or 
                                   f"{sold_to.get('firstName', '')} {sold_to.get('lastName', '')}".strip() or 'N/A')
                    ship_to_name = (ship_to.get('businessName') or 
                                   f"{ship_to.get('firstName', '')} {ship_to.get('lastName', '')}".strip() or '')
                    
                    # Build address
                    address_parts = []
                    if sold_to.get('address1'):
                        address_parts.append(sold_to.get('address1'))
                    if sold_to.get('address2'):
                        address_parts.append(sold_to.get('address2'))
                    address = ', '.join(address_parts)
                    city = sold_to.get('city', '')
                    
                    pdf_order_details = {
                        'order_number': order_number,
                        'po_number': result.get('poNumber', ''),
                        'sold_to_name': sold_to_name,
                        'ship_to_name': ship_to_name,
                        'address': address,
                        'city': city,
                        'order_date': result.get('orderDate') or result.get('date') or 'N/A'
                    }
                    logger.info(f"PDF header details: {pdf_order_details}")
            
            # Save PDF to network folder
            network_pdf_path = Path(network_folder) / pdf_filename
            
            try:
                create_pdf_from_images(compressed_files, network_pdf_path, pdf_order_details)
                logger.info(f"Saved PDF to network folder: {network_pdf_path}")
                if installer_photo_count > 0:
                    logger.info(f"Saved {installer_photo_count} individual installer photos to network folder")
            except Exception as pdf_error:
                logger.error(f"Error creating PDF: {pdf_error}", exc_info=True)
                return jsonify({'success': False, 'error': f'Failed to create PDF: {str(pdf_error)}'}), 500
            
            # Verify PDF file exists before sending
            if not network_pdf_path.exists():
                logger.error(f"PDF file not found after creation: {network_pdf_path}")
                return jsonify({'success': False, 'error': 'PDF file was not created successfully'}), 500
            
            # Verify PDF file size
            pdf_size = network_pdf_path.stat().st_size
            if pdf_size == 0:
                logger.error(f"PDF file is empty: {network_pdf_path}")
                return jsonify({'success': False, 'error': 'PDF file was created but is empty'}), 500
            logger.info(f"PDF file size: {pdf_size:,} bytes")
            
            # Return PDF for download
            try:
                return send_file(
                    str(network_pdf_path),
                    as_attachment=True,
                    download_name=pdf_filename,
                    mimetype='application/pdf'
                )
            except Exception as send_error:
                logger.error(f"Error sending PDF file: {send_error}")
                return jsonify({'success': False, 'error': f'Failed to send PDF file: {str(send_error)}'}), 500
        
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory: {e}")
    
    except Exception as e:
        logger.error(f"Error creating installer PDF: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/fetch-scheduled-jobs', methods=['POST'])
def fetch_scheduled_jobs():
    """API endpoint to fetch scheduled jobs by date range."""
    try:
        data = request.get_json()
        start_date = data.get('start_date', '').strip()
        end_date = data.get('end_date', '').strip()
        
        if not start_date or not end_date:
            return jsonify({'success': False, 'error': 'Start date and end date are required'}), 400
        
        logger.info(f"Fetching scheduled jobs from {start_date} to {end_date}...")
        
        # Convert dates to MM-DD-YYYY format for RFMS API (US format)
        # Handle multiple input formats: YYYY-MM-DD (HTML date input), DD/MM/YYYY (manual entry), etc.
        start_dt = None
        end_dt = None
        
        # Try different date formats
        date_formats = [
            ('%Y-%m-%d', 'YYYY-MM-DD'),      # ISO format (HTML date input)
            ('%d/%m/%Y', 'DD/MM/YYYY'),      # Australian/UK format
            ('%m/%d/%Y', 'MM/DD/YYYY'),      # US format
            ('%d-%m-%Y', 'DD-MM-YYYY'),      # Australian/UK with dashes
            ('%m-%d-%Y', 'MM-DD-YYYY'),      # US format with dashes
        ]
        
        for fmt, fmt_name in date_formats:
            try:
                start_dt = datetime.strptime(start_date, fmt)
                end_dt = datetime.strptime(end_date, fmt)
                logger.debug(f"Parsed dates as {fmt_name} format: {start_date}, {end_date}")
                break
            except ValueError:
                continue
        
        if not start_dt or not end_dt:
            return jsonify({
                'success': False, 
                'error': f'Invalid date format. Expected formats: YYYY-MM-DD, DD/MM/YYYY, or MM/DD/YYYY. Got: {start_date}, {end_date}'
            }), 400
        
        # Convert to MM-DD-YYYY for RFMS API (US format required by API)
        start_date_formatted = start_dt.strftime('%m-%d-%Y')
        end_date_formatted = end_dt.strftime('%m-%d-%Y')
        
        logger.info(f"Converted dates to US format for API: {start_date_formatted} to {end_date_formatted}")
        
        # Find jobs by date range using 2-prong approach
        logger.info(f"Fetching jobs with date range: {start_date_formatted} to {end_date_formatted}")
        jobs_data = rfms_client.find_jobs_by_date_range(
            start_date=start_date_formatted,
            end_date=end_date_formatted,
            record_status="Both"
        )
        
        logger.debug(f"Jobs API response keys: {list(jobs_data.keys()) if isinstance(jobs_data, dict) else 'Not a dict'}")
        
        # Extract jobs from response
        # API returns jobs in both 'detail' (list) and 'result' (list) fields
        jobs = []
        if isinstance(jobs_data, dict):
            detail = jobs_data.get('detail')
            result = jobs_data.get('result')
            
            # Handle both 'detail' (list) and 'result' (list) - API returns lists, not dicts
            if isinstance(detail, list):
                jobs.extend(detail)
            elif isinstance(result, list):
                jobs.extend(result)
            elif isinstance(detail, dict) and 'jobs' in detail:
                jobs.extend(detail.get('jobs', []))
            elif isinstance(result, dict) and 'jobs' in result:
                jobs.extend(result.get('jobs', []))
            elif jobs_data.get('jobs'):
                jobs.extend(jobs_data.get('jobs', []))
        
        logger.info(f"Extracted {len(jobs)} jobs from API response (detail: {len(detail) if isinstance(detail, list) else 'N/A'}, result: {len(result) if isinstance(result, list) else 'N/A'})")
        
        # Get store number from environment for filtering
        store_code = os.getenv('RFMS_STORE_CODE')
        store_number = None
        if store_code:
            try:
                # Try to extract numeric store number from store code (if it's a number string)
                store_number = int(store_code)
            except (ValueError, TypeError):
                # If store_code is not numeric, we'll filter by document number prefix or skip filtering
                pass
        
        # Process each job to get order details and installer photo counts
        processed_jobs = []
        for job in jobs:
            try:
                # Extract order number - API uses 'documentNumber' field
                order_number = (job.get('documentNumber') or 
                               job.get('orderNumber') or 
                               job.get('order_number') or 
                               job.get('poNumber'))
                
                if not order_number:
                    logger.warning(f"Job {job.get('jobId')} has no documentNumber/orderNumber, skipping")
                    continue
                
                # Filter by store number if we have it (storeNumber: 0 means not set/unknown)
                job_store_number = job.get('storeNumber', 0)
                if store_number and job_store_number and job_store_number != store_number:
                    logger.debug(f"Skipping job {order_number} - store number {job_store_number} doesn't match {store_number}")
                    continue
                
                # Get order details including attachments
                try:
                    order_data = rfms_client.get_order(str(order_number).upper(), locked=False, include_attachments=True)
                    
                    # Extract order info - handle nested response structures
                    order_detail = None
                    if isinstance(order_data, dict):
                        # Try multiple possible locations for order detail
                        order_detail = (order_data.get('detail') or 
                                       order_data.get('result') or 
                                       order_data.get('data') or
                                       order_data)
                    
                    # If detail is a dict, use it directly; if result is a dict with nested data, use that
                    if isinstance(order_detail, dict):
                        # Check if result/detail contains the actual order data nested
                        if 'detail' in order_data and isinstance(order_data['detail'], dict):
                            order_detail = order_data['detail']
                        elif 'result' in order_data and isinstance(order_data['result'], dict):
                            order_detail = order_data['result']
                    
                    if order_detail and isinstance(order_detail, dict):
                        # Count installer photos
                        attachments = []
                        if isinstance(order_data, dict):
                            detail = order_data.get('detail')
                            result = order_data.get('result')
                            data_obj = order_data.get('data')
                            
                            attachments = (order_data.get('attachments') or 
                                          (result.get('attachments') if isinstance(result, dict) else None) or
                                          (detail.get('attachments') if isinstance(detail, dict) else None) or
                                          (data_obj.get('attachments') if isinstance(data_obj, dict) else None) or
                                          [])
                        
                        installer_photo_count = sum(1 for att in attachments if is_installer_photo(att))
                        
                        # Get scheduled date from job - handle various formats
                        # API returns scheduledStart as YYYYMMDD format (e.g., "20201109")
                        scheduled_date = (job.get('scheduledStart') or 
                                         job.get('scheduledDate') or 
                                         job.get('scheduled_date') or 
                                         job.get('date'))
                        
                        # Normalize date format to YYYY-MM-DD
                        if scheduled_date:
                            try:
                                if isinstance(scheduled_date, str):
                                    # Handle YYYYMMDD format (e.g., "20201109")
                                    if len(scheduled_date) == 8 and scheduled_date.isdigit():
                                        date_obj = datetime.strptime(scheduled_date, '%Y%m%d')
                                        scheduled_date = date_obj.strftime('%Y-%m-%d')
                                    # Handle MM-DD-YYYY format
                                    elif '-' in scheduled_date and len(scheduled_date.split('-')) == 3:
                                        parts = scheduled_date.split('-')
                                        if len(parts[0]) <= 2:  # MM-DD-YYYY
                                            date_obj = datetime.strptime(scheduled_date, '%m-%d-%Y')
                                            scheduled_date = date_obj.strftime('%Y-%m-%d')
                                        else:  # Already YYYY-MM-DD
                                            datetime.strptime(scheduled_date, '%Y-%m-%d')  # Validate
                                    # Try YYYY-MM-DD format
                                    else:
                                        try:
                                            date_obj = datetime.strptime(scheduled_date, '%Y-%m-%d')
                                            scheduled_date = date_obj.strftime('%Y-%m-%d')
                                        except:
                                            pass
                            except Exception as e:
                                logger.debug(f"Could not parse scheduled date '{scheduled_date}': {e}")
                                pass  # Keep original if parsing fails
                        
                        # Extract fields with multiple fallbacks for different API response structures
                        # Sold To (builder name) - extract from soldTo nested object
                        sold_to = ''
                        sold_to_obj = order_detail.get('soldTo') or order_detail.get('sold_to') or {}
                        if isinstance(sold_to_obj, dict):
                            # Priority: businessName (for builders/companies), then lastName + firstName
                            business_name = sold_to_obj.get('businessName') or sold_to_obj.get('business_name') or ''
                            last_name = sold_to_obj.get('lastName') or sold_to_obj.get('last_name') or ''
                            first_name = sold_to_obj.get('firstName') or sold_to_obj.get('first_name') or ''
                            
                            if business_name:
                                sold_to = business_name
                            elif last_name or first_name:
                                # Combine first and last name
                                name_parts = [part for part in [first_name, last_name] if part]
                                sold_to = ' '.join(name_parts)
                        
                        # Fallback to top-level fields if soldTo object not found
                        if not sold_to:
                            sold_to = (
                                order_detail.get('soldToName') or 
                                order_detail.get('sold_to_name') or 
                                order_detail.get('customerName') or
                                order_detail.get('customer_name') or
                                ''
                            )
                        
                        # If still empty, log for debugging
                        if not sold_to:
                            logger.debug(f"Could not extract sold_to name for order {order_number}. Order detail keys: {list(order_detail.keys())}")
                            logger.debug(f"soldTo object: {sold_to_obj}")
                        
                        # Ship To Address - check shipTo, shipToAddress, shipToAddress1
                        ship_to_address = (
                            order_detail.get('shipToAddress1') or 
                            order_detail.get('ship_to_address1') or 
                            order_detail.get('shipToAddress') or
                            (order_detail.get('shipToAddress') or {}).get('address1', '') if isinstance(order_detail.get('shipToAddress'), dict) else '' or
                            (order_detail.get('shipTo') or {}).get('address1', '') if isinstance(order_detail.get('shipTo'), dict) else '' or
                            ''
                        )
                        
                        # Ship To Suburb/City - check shipTo, shipToAddress
                        ship_to_suburb = (
                            order_detail.get('shipToSuburb') or 
                            order_detail.get('ship_to_suburb') or 
                            order_detail.get('shipToCity') or
                            order_detail.get('ship_to_city') or
                            (order_detail.get('shipToAddress') or {}).get('city', '') if isinstance(order_detail.get('shipToAddress'), dict) else '' or
                            (order_detail.get('shipToAddress') or {}).get('suburb', '') if isinstance(order_detail.get('shipToAddress'), dict) else '' or
                            (order_detail.get('shipTo') or {}).get('city', '') if isinstance(order_detail.get('shipTo'), dict) else '' or
                            (order_detail.get('shipTo') or {}).get('suburb', '') if isinstance(order_detail.get('shipTo'), dict) else '' or
                            ''
                        )
                        
                        # PO Number
                        po_number = (
                            order_detail.get('poNumber') or 
                            order_detail.get('po_number') or 
                            ''
                        )
                        
                        # Extract crew information from job (crewName and secondaryCrewName are in the job object)
                        # API returns: crewName and secondaryCrewName
                        crew_name = (job.get('crewName') or 
                                    job.get('crew_name') or 
                                    '').strip()
                        secondary_crew_name = (job.get('secondaryCrewName') or 
                                              job.get('secondary_crew_name') or 
                                              '').strip()
                        
                        # Combine crew names if both exist, otherwise use primary crew name
                        crew_display = crew_name
                        if crew_name and secondary_crew_name:
                            crew_display = f"{crew_name} / {secondary_crew_name}"
                        elif secondary_crew_name:
                            crew_display = secondary_crew_name
                        
                        processed_jobs.append({
                            'order_number': str(order_number).upper(),  # This is the AZ order number
                            'po_number': po_number,
                            'sold_to': sold_to or 'N/A',
                            'ship_to_address': ship_to_address or '',
                            'ship_to_suburb': ship_to_suburb or '',
                            'installer_photo_count': installer_photo_count,
                            'scheduled_date': scheduled_date or '',
                            'job_id': job.get('id') or job.get('jobId'),
                            'has_po': bool(po_number),
                            'crew_name': crew_display or 'N/A'
                        })
                except Exception as e:
                    logger.warning(f"Could not get details for order {order_number}: {e}")
                    continue
            except Exception as e:
                logger.warning(f"Error processing job: {e}")
                continue
        
        logger.info(f"Found {len(processed_jobs)} scheduled jobs")
        
        return jsonify({
            'success': True,
            'jobs': processed_jobs,
            'total': len(processed_jobs)
        })
    
    except Exception as e:
        logger.error(f"Error fetching scheduled jobs: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/create-multiple-installer-pdfs', methods=['POST'])
def create_multiple_installer_pdfs():
    """API endpoint to create multiple PDFs from selected orders."""
    import time
    start_time = time.time()
    
    try:
        data = request.get_json()
        order_numbers = data.get('order_numbers', [])
        
        if not order_numbers:
            return jsonify({'success': False, 'error': 'At least one order number is required'}), 400
        
        logger.info(f"Creating PDFs for {len(order_numbers)} orders...")
        
        # Limit the number of orders to prevent timeouts (adjust as needed)
        max_orders = int(os.getenv('MAX_PDF_ORDERS', 50))
        if len(order_numbers) > max_orders:
            return jsonify({
                'success': False, 
                'error': f'Too many orders selected ({len(order_numbers)}). Maximum is {max_orders}. Please select fewer orders.'
            }), 400
        
        # Generate PDFs for each order
        pdf_results = []
        temp_dir = Path(tempfile.mkdtemp(prefix="multiple_installer_photos_"))
        
        try:
            for idx, order_number in enumerate(order_numbers, 1):
                order_start_time = time.time()
                order_number = str(order_number).strip().upper()
                logger.info(f"Processing order {idx}/{len(order_numbers)}: {order_number}")
                
                try:
                    # Get order attachments
                    logger.debug(f"Fetching order data for {order_number}...")
                    order_data = rfms_client.get_order(order_number, locked=False, include_attachments=True)
                    
                    # Extract attachments
                    attachments = []
                    if isinstance(order_data, dict):
                        detail = order_data.get('detail')
                        result = order_data.get('result')
                        data_obj = order_data.get('data')
                        
                        attachments = (order_data.get('attachments') or 
                                      (result.get('attachments') if isinstance(result, dict) else None) or
                                      (detail.get('attachments') if isinstance(detail, dict) else None) or
                                      (data_obj.get('attachments') if isinstance(data_obj, dict) else None) or
                                      [])
                    
                    # Filter for installer photos only
                    installer_photos = [att for att in attachments if is_installer_photo(att)]
                    
                    if not installer_photos:
                        pdf_results.append({
                            'order_number': order_number,
                            'success': False,
                            'error': 'No installer photos found'
                        })
                        continue
                    
                    # Download attachments
                    downloaded_files = []
                    for attachment in installer_photos:
                        try:
                            file_path = download_rfms_attachment(rfms_client, attachment, temp_dir)
                            downloaded_files.append(file_path)
                        except Exception as e:
                            logger.error(f"Failed to download attachment for {order_number}: {e}")
                            continue
                    
                    if not downloaded_files:
                        pdf_results.append({
                            'order_number': order_number,
                            'success': False,
                            'error': 'No attachments were successfully downloaded'
                        })
                        continue
                    
                    # Compress images
                    compressed_files = []
                    for file_path in downloaded_files:
                        try:
                            compressed_path = compress_image(file_path)
                            compressed_files.append(compressed_path)
                        except Exception as e:
                            logger.warning(f"Failed to compress {file_path}: {e}, using original")
                            compressed_files.append(file_path)
                    
                    # Create PDF with proper naming: AZ######_Pics_DDMMYY
                    today = datetime.now()
                    date_str = today.strftime('%d%m%y')  # DDMMYY format (Australian short date)
                    pdf_filename = f"{order_number}_Pics_{date_str}.pdf"
                    
                    # Save to network folder
                    network_folder = os.getenv('INSTALLER_PHOTOS_FOLDER', os.path.join(app.config['UPLOAD_FOLDER'], 'installer_photos'))
                    os.makedirs(network_folder, exist_ok=True)
                    network_pdf_path = Path(network_folder) / pdf_filename
                    
                    # Extract order details for PDF header
                    pdf_order_details = {}
                    if isinstance(order_data, dict):
                        result = order_data.get('result')
                        if isinstance(result, dict):
                            sold_to = result.get('soldTo', {})
                            ship_to = result.get('shipTo', {})
                            
                            # Format sold to name
                            sold_to_name = ''
                            if sold_to:
                                if sold_to.get('businessName'):
                                    sold_to_name = sold_to.get('businessName')
                                elif sold_to.get('firstName') or sold_to.get('lastName'):
                                    sold_to_name = f"{sold_to.get('firstName', '')} {sold_to.get('lastName', '')}".strip()
                            
                            # Format ship to name
                            ship_to_name = ''
                            if ship_to:
                                if ship_to.get('businessName'):
                                    ship_to_name = ship_to.get('businessName')
                                elif ship_to.get('firstName') or ship_to.get('lastName'):
                                    ship_to_name = f"{ship_to.get('firstName', '')} {ship_to.get('lastName', '')}".strip()
                            
                            pdf_order_details = {
                                'order_number': result.get('number') or order_number,
                                'po_number': result.get('poNumber') or result.get('po_number') or '',
                                'sold_to_name': sold_to_name,
                                'ship_to_name': ship_to_name,
                                'address': ship_to.get('address1') or '',
                                'city': ship_to.get('city') or '',
                            }
                    
                    # Create PDF - function saves to output_pdf_path and returns the path
                    pdf_path = create_pdf_from_images(compressed_files, network_pdf_path, pdf_order_details)
                    
                    # Get PDF size for response
                    pdf_size = pdf_path.stat().st_size if pdf_path.exists() else 0
                    
                    order_duration = time.time() - order_start_time
                    logger.info(f"Created PDF for {order_number}: {network_pdf_path} ({pdf_size} bytes) in {order_duration:.2f}s")
                    
                    pdf_results.append({
                        'order_number': order_number,
                        'success': True,
                        'filename': pdf_filename,
                        'path': str(network_pdf_path),
                        'size': pdf_size
                    })
                
                except Exception as e:
                    order_duration = time.time() - order_start_time
                    logger.error(f"Error creating PDF for {order_number} after {order_duration:.2f}s: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    pdf_results.append({
                        'order_number': order_number,
                        'success': False,
                        'error': str(e)
                    })
            
            total_duration = time.time() - start_time
            logger.info(f"Completed processing {len(order_numbers)} orders in {total_duration:.2f}s. Success: {sum(1 for r in pdf_results if r.get('success'))}, Failed: {sum(1 for r in pdf_results if not r.get('success'))}")
            
            # Return ZIP file with all PDFs, or individual results
            successful_pdfs = [r for r in pdf_results if r.get('success')]
            
            if successful_pdfs:
                # Create ZIP file with all PDFs
                import zipfile
                zip_filename = f"installer_photos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                # Create ZIP in a separate location so it doesn't get deleted with temp_dir
                # Save ZIP to network folder or temp location that won't be immediately cleaned
                zip_temp_dir = Path(tempfile.mkdtemp(prefix="zip_installer_photos_"))
                zip_path = zip_temp_dir / zip_filename
                
                try:
                    logger.info(f"Creating ZIP file at {zip_path} with {len(successful_pdfs)} PDFs")
                    
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        zip_count = 0
                        for pdf_result in successful_pdfs:
                            if pdf_result.get('success'):
                                pdf_path = Path(pdf_result['path'])
                                if pdf_path.exists():
                                    try:
                                        zipf.write(pdf_path, pdf_result['filename'])
                                        zip_count += 1
                                        logger.debug(f"Added {pdf_result['filename']} to ZIP")
                                    except Exception as e:
                                        logger.error(f"Failed to add {pdf_result['filename']} to ZIP: {e}")
                                else:
                                    logger.warning(f"PDF file does not exist: {pdf_path}")
                    
                    if zip_count == 0:
                        logger.warning("ZIP file created but no PDFs were added to it")
                        raise Exception("No PDFs were successfully added to ZIP file")
                    
                    zip_size = zip_path.stat().st_size if zip_path.exists() else 0
                    logger.info(f"Created ZIP file with {zip_count} PDFs: {zip_path} ({zip_size} bytes)")
                    
                    # Return ZIP file - Flask's send_file will read the file before returning
                    # Note: We don't clean up zip_temp_dir here as Flask needs it during send
                    # The OS temp cleaner will eventually remove it, or we could add delayed cleanup
                    return send_file(
                        str(zip_path),
                        mimetype='application/zip',
                        as_attachment=True,
                        download_name=zip_filename
                    )
                except Exception as e:
                    logger.error(f"Error creating ZIP file: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # Clean up zip temp dir on error
                    try:
                        if zip_path and zip_path.exists():
                            zip_path.unlink()
                        if zip_temp_dir and zip_temp_dir.exists():
                            shutil.rmtree(zip_temp_dir, ignore_errors=True)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up ZIP temp directory: {cleanup_error}")
                    raise
            else:
                # No successful PDFs - return error with results
                return jsonify({
                    'success': False,
                    'error': 'No PDFs were successfully created',
                    'results': pdf_results
                }), 500
        
        finally:
            # Clean up temporary directory (this only contains downloaded images, not the ZIP)
            # ZIP is in a separate directory that Flask will handle
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory {temp_dir}: {e}")
    
    except Exception as e:
        logger.error(f"Error creating multiple PDFs: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("RFMS Uploader - Starting Server")
    print("=" * 60)
    
    with app.app_context():
        # Create database tables
        db.create_all()
        print("[OK] Database initialized")
    
    # Start daily stock report scheduler
    try:
        from utils.daily_stock_report import schedule_daily_report
        scheduler = schedule_daily_report()
        print("[OK] Daily stock report scheduler initialized (runs at 3:45 PM AEST on weekdays)")
    except Exception as e:
        logger.error(f"Failed to start daily stock report scheduler: {e}", exc_info=True)
        print(f"[WARNING] Failed to start daily stock report scheduler: {e}")
    
    # Get configuration
    debug_mode = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
    port = int(os.getenv('PORT', 5003))  # Default to port 5003 for local testing
    host = os.getenv('HOST', '127.0.0.1')  # Listen on localhost for local testing
    
    print(f"Server starting on: http://localhost:{port}")
    print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(debug=debug_mode, host=host, port=port)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"\nError starting server: {e}")
        print("Try running: python app.py") 
