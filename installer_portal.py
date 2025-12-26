import os
import io
from datetime import datetime, timedelta
from functools import wraps
from typing import List, Dict, Any

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    send_file,
    jsonify,
)
from werkzeug.utils import secure_filename

# Product codes for installer invoicing: 38-49 and 51
INSTALLER_INVOICE_PRODUCT_CODES = [str(i) for i in range(38, 50)] + ['51']

from models import (
    db,
    Installer,
    WorkOrder,
    WorkOrderLine,
    InstallerInvoice,
    InvoiceLine,
    InvoiceAttachment,
)
from sqlalchemy import func
from utils.rfms_client import RFMSClient
from utils.email_sender import EmailSender

portal_bp = Blueprint('portal', __name__, url_prefix='/portal')
rfms_client = RFMSClient()
email_sender = EmailSender()


def ensure_default_installer_account(app):
    """Seed a default installer account from environment variables if configured."""
    default_email = os.getenv('INSTALLER_PORTAL_ADMIN_EMAIL')
    default_password = os.getenv('INSTALLER_PORTAL_ADMIN_PASSWORD')
    default_name = os.getenv('INSTALLER_PORTAL_ADMIN_NAME', 'Portal Admin')
    default_crew = os.getenv('INSTALLER_PORTAL_CREW_CODE')

    if not default_email or not default_password:
        return

    with app.app_context():
        existing = Installer.query.filter_by(email=default_email.lower()).first()
        if existing:
            return

        installer = Installer(
            name=default_name,
            email=default_email.lower(),
            crew_code=default_crew,
            is_admin=True,  # Default admin account
            approved=True,  # Auto-approve default admin
            active=True,
        )
        installer.set_password(default_password)
        db.session.add(installer)
        db.session.commit()
        current_app.logger.info("Default installer portal admin created")


def current_installer():
    installer_id = session.get('installer_id')
    if not installer_id:
        return None
    return Installer.query.get(installer_id)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_installer():
            flash('Please log in to access the installer portal.', 'warning')
            return redirect(url_for('portal.login'))
        return view_func(*args, **kwargs)

    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        installer = current_installer()
        if not installer:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('portal.login'))
        if not installer.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('portal.dashboard'))
        return view_func(*args, **kwargs)

    return wrapper


def _normalize_jobs_response(jobs_payload: Any) -> List[Dict[str, Any]]:
    if isinstance(jobs_payload, list):
        return jobs_payload

    if not isinstance(jobs_payload, dict):
        return []

    detail = jobs_payload.get('detail') or jobs_payload.get('jobs')
    if isinstance(detail, dict):
        detail = detail.get('jobs') or detail.get('detail')
    return detail if isinstance(detail, list) else []


def _is_installer_invoice_line(line: Dict[str, Any]) -> bool:
    """
    Check if a line is an installer invoice line (product codes 38-49 and 51).
    These are the lines that installers invoice for.
    """
    if not line:
        return False
    
    # Check productCode first (primary identifier)
    product_code = (
        line.get('productCode') or 
        line.get('productCategoryCode') or 
        line.get('categoryCode') or 
        line.get('productCategory') or
        ''
    )
    
    if not product_code:
        current_app.logger.debug(f"_is_installer_invoice_line: No product code found in line: {list(line.keys())[:10]}")
        return False
    
    # Normalize product code (remove whitespace, convert to string)
    code_str = str(product_code).strip()
    
    # Check if code matches installer invoice codes (38-49 and 51)
    # Check exact match first
    if code_str in INSTALLER_INVOICE_PRODUCT_CODES:
        current_app.logger.debug(f"_is_installer_invoice_line: Code '{code_str}' matched (exact)")
        return True
    
    # Check if code starts with these numbers (for longer codes like "38123")
    for valid_code in INSTALLER_INVOICE_PRODUCT_CODES:
        if code_str.startswith(valid_code):
            current_app.logger.debug(f"_is_installer_invoice_line: Code '{code_str}' matched (starts with {valid_code})")
            return True
    
    # Also check numeric comparison for codes like 38, 39, etc.
    try:
        code_num = int(code_str)
        if 38 <= code_num <= 49 or code_num == 51:
            current_app.logger.debug(f"_is_installer_invoice_line: Code '{code_str}' matched (numeric: {code_num})")
            return True
    except (ValueError, TypeError):
        pass
    
    current_app.logger.debug(f"_is_installer_invoice_line: Code '{code_str}' did NOT match installer invoice codes")
    return False


def _dates_match_fuzzy(date1_str: str, date2_str: str, tolerance_days: int = 2) -> bool:
    """
    Check if two dates match within a tolerance (fuzzy matching).
    
    Args:
        date1_str: First date string (various formats supported)
        date2_str: Second date string (various formats supported)
        tolerance_days: Number of days tolerance (default: 2)
        
    Returns:
        True if dates are within tolerance_days of each other
    """
    from datetime import datetime, timedelta
    
    def parse_date(date_str):
        """Parse date string in various formats."""
        if not date_str:
            return None
        
        # Try ISO format first
        try:
            return datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
        except:
            pass
        
        # Try MM-DD-YYYY
        try:
            return datetime.strptime(str(date_str), '%m-%d-%Y')
        except:
            pass
        
        # Try YYYY-MM-DD (ISO format from RFMS)
        try:
            return datetime.strptime(str(date_str), '%Y-%m-%d')
        except:
            pass
        
        # Try DD/MM/YYYY (Australian format)
        try:
            return datetime.strptime(str(date_str), '%d/%m/%Y')
        except:
            pass
        
        # Try DD-MM-YYYY (Australian format with dashes)
        try:
            return datetime.strptime(str(date_str), '%d-%m-%Y')
        except:
            pass
        
        return None
    
    date1 = parse_date(date1_str)
    date2 = parse_date(date2_str)
    
    if not date1 or not date2:
        return False
    
    # Normalize to date only (remove time component)
    date1 = date1.date()
    date2 = date2.date()
    
    # Check if dates are within tolerance
    diff = abs((date1 - date2).days)
    return diff <= tolerance_days


def _parse_order_lines(order_details: Dict[str, Any], install_date: str = None) -> List[Dict[str, Any]]:
    """
    Parse order lines from RFMS order details, matching the pattern used in app_origin.py.
    RFMS API returns: {"status": "success", "result": {...}, "detail": {...}}
    Lines are in result.lines (same as stock receiving uses).
    Only includes installer invoice lines (product codes 38-49 and 51).
    Optionally filters by install date with fuzzy matching (±2 days).
    
    Args:
        order_details: RFMS order details dictionary (full response from get_order)
        install_date: Optional install date string to filter lines (fuzzy match ±2 days)
    """
    if not isinstance(order_details, dict):
        current_app.logger.warning("_parse_order_lines: order_details is not a dict")
        return []

    # Log the structure for debugging
    current_app.logger.debug(f"_parse_order_lines: order_details keys: {list(order_details.keys())}")

    # Extract order data following the same pattern as app_origin.py
    # app_origin does: order_details = full_order.get('result', {})
    # Then: order_details.get('lines', [])
    order_result = order_details.get('result', {})
    
    if not isinstance(order_result, dict):
        # Try detail as fallback
        order_result = order_details.get('detail', {})
        if not isinstance(order_result, dict):
            order_result = {}
    
    current_app.logger.debug(f"_parse_order_lines: order_result keys: {list(order_result.keys()) if isinstance(order_result, dict) else 'Not a dict'}")
    
    # Get lines from order_result (same as app_origin.py line 1935 and 2338)
    all_lines = order_result.get('lines', []) or order_result.get('lineItems', [])
    
    # Log the actual lines structure for debugging
    if all_lines and len(all_lines) > 0:
        current_app.logger.debug(f"_parse_order_lines: First line sample: {str(all_lines[0])[:500]}")
        current_app.logger.debug(f"_parse_order_lines: First line productCode: {all_lines[0].get('productCode')}, type: {type(all_lines[0].get('productCode'))}")
    
    # If not found in result, try detail
    if not all_lines:
        detail = order_details.get('detail', {})
        if isinstance(detail, dict):
            all_lines = detail.get('lines', []) or detail.get('lineItems', [])
    
    # If still not found, try top level
    if not all_lines:
        all_lines = order_details.get('lines', []) or order_details.get('lineItems', [])

    if not isinstance(all_lines, list):
        current_app.logger.warning(f"_parse_order_lines: lines is not a list, type: {type(all_lines)}")
        all_lines = []

    if not all_lines:
        # Log the full structure to help debug
        current_app.logger.warning(f"_parse_order_lines: No line items found in order_details.")
        current_app.logger.debug(f"_parse_order_lines: Full order structure: {str(order_details)[:2000]}")
        return []
    
    current_app.logger.info(f"_parse_order_lines: Found {len(all_lines)} total line items from RFMS (from result.lines)")
    
    # Log all product codes found for debugging
    if all_lines:
        product_codes = [str(line.get('productCode', 'N/A')) for line in all_lines[:10]]
        current_app.logger.info(f"_parse_order_lines: Product codes in order: {product_codes}")

    # Filter to only installer invoice lines (38-49 and 51)
    current_app.logger.info(f"_parse_order_lines: Filtering {len(all_lines)} lines for installer invoice codes (38-49, 51)")
    invoice_lines = []
    for line in all_lines:
        line_num = line.get('lineNumber', '?')
        product_code = line.get('productCode', 'N/A')
        current_app.logger.debug(f"_parse_order_lines: Checking line {line_num}, productCode: {product_code}")
        if _is_installer_invoice_line(line):
            invoice_lines.append(line)
            current_app.logger.debug(f"_parse_order_lines: Line {line_num} (productCode: {product_code}) INCLUDED")
        else:
            current_app.logger.debug(f"_parse_order_lines: Line {line_num} (productCode: {product_code}) EXCLUDED")
    
    current_app.logger.info(f"_parse_order_lines: Filtered to {len(invoice_lines)} installer invoice lines (from {len(all_lines)} total lines)")
    
    # Log which lines were included
    if invoice_lines:
        included_lines = [(line.get('lineNumber'), line.get('productCode'), line.get('styleName', '')[:30]) for line in invoice_lines[:10]]
        current_app.logger.info(f"_parse_order_lines: Included lines: {included_lines}")
    else:
        all_product_codes = [str(l.get('productCode', 'N/A')) for l in all_lines[:20]]
        current_app.logger.error(f"_parse_order_lines: No installer invoice lines found! All product codes: {all_product_codes}")
        current_app.logger.error(f"_parse_order_lines: Expected codes: {INSTALLER_INVOICE_PRODUCT_CODES}")
    
    # If install_date is provided, further filter by date (fuzzy match ±2 days)
    if install_date:
        filtered_by_date = []
        for line in invoice_lines:
            line_install_date = (
                line.get('installDate') or 
                line.get('install_date') or 
                line.get('scheduledDate') or
                line.get('scheduled_date') or
                None
            )
            
            if line_install_date and _dates_match_fuzzy(install_date, str(line_install_date), tolerance_days=2):
                filtered_by_date.append(line)
            elif not line_install_date:
                # If line doesn't have install date, include it (might be a manual line)
                filtered_by_date.append(line)
        
        invoice_lines = filtered_by_date
        current_app.logger.info(f"_parse_order_lines: Filtered to {len(invoice_lines)} lines matching install date {install_date} (±2 days)")

    lines: List[Dict[str, Any]] = []
    for index, item in enumerate(invoice_lines):
        if not isinstance(item, dict):
            continue

        qty = float(item.get('quantity') or item.get('qty') or 0)
        # For installer invoices, use unitCost (what installer charges) not unitPrice (customer price)
        unit_price = float(item.get('unitCost') or item.get('unitPrice') or item.get('price') or item.get('unit_price') or 0)
        # Always calculate line total as quantity * unit_price (ignore RFMS retail totals)
        total = qty * unit_price
        # Build description from styleName and colorName (matching RFMS structure)
        style_name = item.get('styleName') or ''
        color_name = item.get('colorName') or ''
        description = item.get('description') or ''
        
        # If no description, build from styleName and colorName
        if not description:
            if style_name and color_name:
                description = f"{style_name} {color_name}".strip()
            elif style_name:
                description = style_name
            elif color_name:
                description = color_name
            else:
                description = item.get('productDescription') or item.get('productName') or 'Service Line'
        line_number = item.get('lineNumber') or item.get('line_number') or (index + 1)
        product_code = item.get('productCode') or item.get('productNumber') or item.get('product_code') or ''
        
        lines.append({
            'source_line_number': int(line_number) if line_number else (index + 1),
            'product_code': product_code,
            'description': description,
            'quantity': qty,
            'unit_price': unit_price,
            'extended_price': total,
            'tax_rate': float(item.get('taxRate') or item.get('tax_rate') or 0.1),
        })

    current_app.logger.info(f"_parse_order_lines: Parsed {len(lines)} service/labour lines for invoice")
    return lines


def _sync_work_order_lines(work_order: WorkOrder, order_details: Dict[str, Any], install_date: str = None):
    lines = _parse_order_lines(order_details, install_date=install_date)
    if not lines:
        return

    existing_by_source = {
        line.source_line_number: line for line in work_order.lines if line.source_line_number is not None
    }

    for line_data in lines:
        source_num = line_data.get('source_line_number')
        line = existing_by_source.get(source_num)
        if not line:
            line = WorkOrderLine(work_order_id=work_order.id)

        line.source_line_number = source_num
        line.product_code = line_data.get('product_code')
        line.description = line_data.get('description')
        line.quantity = line_data.get('quantity') or 0
        line.unit_price = line_data.get('unit_price') or 0
        # Always calculate extended_price as quantity * unit_price (ignore RFMS retail totals)
        line.extended_price = line.quantity * line.unit_price
        line.tax_rate = line_data.get('tax_rate') if line_data.get('tax_rate') is not None else 0.1
        db.session.add(line)


def _hydrate_invoice_from_work_order(invoice: InstallerInvoice, work_order: WorkOrder):
    # Check if invoice already has lines - query directly to avoid relationship caching issues
    from models import InvoiceLine, WorkOrderLine
    existing_lines = InvoiceLine.query.filter_by(invoice_id=invoice.id).all()
    existing_count = len(existing_lines)
    
    if existing_count > 0:
        current_app.logger.info(f"_hydrate_invoice_from_work_order: Invoice {invoice.id} already has {existing_count} lines, skipping")
        return

    # Query work order lines directly to ensure we get them
    work_order_lines = WorkOrderLine.query.filter_by(work_order_id=work_order.id).all()
    
    current_app.logger.info(f"_hydrate_invoice_from_work_order: Creating invoice lines from {len(work_order_lines)} work order lines for invoice {invoice.id}")
    
    if not work_order_lines:
        current_app.logger.warning(f"_hydrate_invoice_from_work_order: No work order lines found for work_order {work_order.id}")
        return
    
    created_count = 0
    subtotal = 0.0
    for wo_line in work_order_lines:
        # Line total is quantity * unit_price (non-tax, non-GST)
        line_total = (wo_line.quantity or 0) * (wo_line.unit_price or 0)
        subtotal += line_total
        
        new_line = InvoiceLine(
            invoice_id=invoice.id,
            work_order_line_id=wo_line.id,
            description=wo_line.description or 'Work order line',
            quantity=wo_line.quantity or 0,
            unit_price=wo_line.unit_price or 0,
            tax_rate=0.0,  # Lines are non-tax, non-GST
            total=line_total,  # Just quantity * unit_price
        )
        db.session.add(new_line)
        created_count += 1
        current_app.logger.info(f"_hydrate_invoice_from_work_order: Created invoice line {created_count}: '{wo_line.description[:40]}' (qty: {wo_line.quantity}, price: {wo_line.unit_price}, total: {line_total})")
    
    # Calculate invoice totals: GST is 10% of subtotal
    invoice.subtotal = round(subtotal, 2)
    invoice.tax_amount = round(subtotal * 0.10, 2)  # 10% GST
    invoice.total = round(subtotal + invoice.tax_amount, 2)
    
    current_app.logger.info(f"_hydrate_invoice_from_work_order: Successfully created {created_count} invoice lines from {len(work_order_lines)} work order lines")
    current_app.logger.info(f"_hydrate_invoice_from_work_order: Invoice totals - Subtotal: ${invoice.subtotal}, GST: ${invoice.tax_amount}, Total: ${invoice.total}")


def _parse_date(value):
    """Parse date from various RFMS API formats."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    # Try ISO format first
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except Exception:
        pass
    # Try MM-DD-YYYY format
    try:
        return datetime.strptime(str(value), '%m-%d-%Y')
    except Exception:
        pass
    # Try YYYYMMDD format (common in RFMS)
    try:
        return datetime.strptime(str(value), '%Y%m%d')
    except Exception:
        pass
    # Try YYYY-MM-DD format
    try:
        return datetime.strptime(str(value), '%Y-%m-%d')
    except Exception:
        pass
    return None


def _send_invoice_submission_email(invoice: InstallerInvoice, installer: Installer, work_order: WorkOrder):
    """Send email notification when installer submits an invoice."""
    from_address = os.getenv('REPORTS_EMAIL_ADDRESS', 'reports@atozflooringsolutions.com.au')
    to_address = os.getenv('ACCOUNTS_EMAIL_ADDRESS', 'accounts@atozflooringsolutions.com.au')
    
    invoice_date = invoice.submitted_at.strftime('%d %B %Y') if invoice.submitted_at else 'N/A'
    
    # Build email body
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #01998e;">New Installer Invoice Submitted</h2>
            
            <p>A new installer invoice has been submitted and requires review.</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Invoice Details</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Invoice Number:</td>
                        <td style="padding: 8px;">{invoice.invoice_number}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Installer:</td>
                        <td style="padding: 8px;">{installer.name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Business:</td>
                        <td style="padding: 8px;">{installer.business_name or installer.name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Order Number:</td>
                        <td style="padding: 8px;">{work_order.order_number or 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Job Number:</td>
                        <td style="padding: 8px;">{work_order.job_number or 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Invoice Date:</td>
                        <td style="padding: 8px;">{invoice_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Total Amount:</td>
                        <td style="padding: 8px; font-size: 18px; color: #01998e; font-weight: bold;">${invoice.total:.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Subtotal:</td>
                        <td style="padding: 8px;">${invoice.subtotal:.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Tax:</td>
                        <td style="padding: 8px;">${invoice.tax_amount:.2f}</td>
                    </tr>
                </table>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>Line Items</h3>
                <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
                    <thead>
                        <tr style="background-color: #01998e; color: white;">
                            <th style="padding: 10px; text-align: left;">Description</th>
                            <th style="padding: 10px; text-align: right;">Qty</th>
                            <th style="padding: 10px; text-align: right;">Unit Price</th>
                            <th style="padding: 10px; text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for line in invoice.lines:
        body += f"""
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px;">{line.description}</td>
                            <td style="padding: 8px; text-align: right;">{line.quantity:.2f}</td>
                            <td style="padding: 8px; text-align: right;">${line.unit_price:.2f}</td>
                            <td style="padding: 8px; text-align: right;">${line.total:.2f}</td>
                        </tr>
        """
    
    body += f"""
                    </tbody>
                </table>
            </div>
            
            {f'<div style="margin: 20px 0;"><strong>Notes:</strong><p style="background-color: #f9f9f9; padding: 10px; border-left: 3px solid #01998e;">{invoice.notes or "No notes provided."}</p></div>' if invoice.notes else ''}
            
            <div style="margin: 30px 0; text-align: center;">
                <p style="background-color: #01998e; color: white; padding: 12px 24px; border-radius: 5px; display: inline-block;">
                    Please review this invoice in the Accounts Dashboard
                </p>
            </div>
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated notification from the Installer Portal system.<br>
                Please review and process this invoice in the Accounts Dashboard.
            </p>
        </div>
    </body>
    </html>
    """
    
    subject = f"New Installer Invoice: {invoice.invoice_number} - {installer.name} - ${invoice.total:.2f}"
    
    email_sender.send_email(from_address, to_address, subject, body, body_type='HTML')
    current_app.logger.info(f"Sent invoice submission email for {invoice.invoice_number} to {to_address}")


def _is_installer_photo(attachment: Dict[str, Any]) -> bool:
    """Check if an attachment is tagged as an installer photo (in brackets or description)."""
    description = str(attachment.get('description', '') or '').upper()
    tag = str(attachment.get('tag', '') or '').upper()
    attachment_type = str(attachment.get('type', '') or '').upper()
    name = str(attachment.get('name', '') or '').upper()
    title = str(attachment.get('title', '') or '').upper()
    
    search_fields = [description, tag, attachment_type, name, title]
    for field in search_fields:
        if 'INSTALLER PHOTOS' in field or 'INSTALLER PHOTO' in field:
            return True
        # Check for brackets pattern like [INSTALLER PHOTOS] or (INSTALLER PHOTOS)
        if '[INSTALLER' in field or '(INSTALLER' in field:
            return True
    return False


def _get_installer_photos_from_order(order_details: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract installer photos from RFMS order attachments."""
    if not isinstance(order_details, dict):
        return []
    
    # Try to find attachments in various locations (comprehensive search)
    attachments = []
    
    # Check top level
    if isinstance(order_details.get('attachments'), list):
        attachments = order_details['attachments']
    
    # Check 'detail' object
    detail = order_details.get('detail')
    if isinstance(detail, dict):
        if isinstance(detail.get('attachments'), list):
            attachments = detail.get('attachments')
        elif isinstance(detail.get('order'), dict):
            order_obj = detail.get('order')
            if isinstance(order_obj.get('attachments'), list):
                attachments = order_obj.get('attachments')
    
    # Check 'result' object
    result = order_details.get('result')
    if not attachments and isinstance(result, dict):
        if isinstance(result.get('attachments'), list):
            attachments = result.get('attachments')
        elif isinstance(result.get('order'), dict):
            order_obj = result.get('order')
            if isinstance(order_obj.get('attachments'), list):
                attachments = order_obj.get('attachments')
    
    # Check 'data' object
    data = order_details.get('data')
    if not attachments and isinstance(data, dict):
        if isinstance(data.get('attachments'), list):
            attachments = data.get('attachments')
    
    if not isinstance(attachments, list):
        current_app.logger.debug(f"_get_installer_photos_from_order: No attachments found in order_details")
        return []
    
    current_app.logger.info(f"_get_installer_photos_from_order: Found {len(attachments)} total attachments")
    
    # Filter for installer photos
    installer_photos = []
    for attachment in attachments:
        if _is_installer_photo(attachment):
            installer_photos.append(attachment)
    
    current_app.logger.info(f"_get_installer_photos_from_order: Filtered to {len(installer_photos)} installer photos")
    return installer_photos


@portal_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').lower().strip()
        password = request.form.get('password') or ''

        current_app.logger.info(f"Login attempt: email={email}")
        installer = Installer.query.filter_by(email=email).first()
        if installer:
            current_app.logger.info(f"Installer found: {installer.email}, active={installer.active}, approved={installer.approved}, is_admin={installer.is_admin}")
            if not installer.active:
                flash('Your account is not active. Please wait for administrator approval.', 'warning')
                return render_template('portal_login.html')
            
            if not installer.approved:
                flash('Your account is pending approval. Please wait for administrator approval.', 'info')
                return render_template('portal_login.html')
            
            if installer.check_password(password):
                session['installer_id'] = installer.id
                installer.updated_at = datetime.utcnow()
                db.session.commit()
                flash('Login successful.', 'success')
                
                # Redirect admin to admin dashboard
                if installer.is_admin:
                    return redirect(url_for('portal.admin_dashboard'))
                return redirect(url_for('portal.dashboard'))

        flash('Invalid email or password.', 'danger')

    return render_template('portal_login.html')


@portal_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        current_app.logger.info(f"Registration form submitted")
        
        email = (request.form.get('email') or '').lower().strip()
        password = request.form.get('password') or ''
        password_confirm = request.form.get('password_confirm') or ''
        name = request.form.get('name') or ''
        
        # Business details
        business_name = request.form.get('business_name') or ''
        address_line1 = request.form.get('address_line1') or ''
        address_line2 = request.form.get('address_line2') or ''
        city = request.form.get('city') or ''
        state = request.form.get('state') or ''
        postal_code = request.form.get('postal_code') or ''
        abn = request.form.get('abn') or ''
        gst_registered = request.form.get('gst_registered') == 'on'
        phone = request.form.get('phone') or ''
        
        current_app.logger.info(f"Registration data: email={email}, name={name}, has_password={bool(password)}")
        
        # Field-specific validation errors
        field_errors = {}
        
        # Validation
        if not name:
            field_errors['name'] = 'Full name is required.'
        if not email:
            field_errors['email'] = 'Email address is required.'
        elif '@' not in email:
            field_errors['email'] = 'Please enter a valid email address.'
        if not password:
            field_errors['password'] = 'Password is required.'
        elif len(password) < 6:
            field_errors['password'] = 'Password must be at least 6 characters long.'
        if not password_confirm:
            field_errors['password_confirm'] = 'Please confirm your password.'
        elif password != password_confirm:
            field_errors['password_confirm'] = 'Passwords do not match.'
        
        if field_errors:
            current_app.logger.warning(f"Registration validation failed: {field_errors}")
            return render_template('portal_register.html', form_data=dict(request.form), field_errors=field_errors)
        
        # Check if email already exists
        existing = Installer.query.filter_by(email=email).first()
        if existing:
            field_errors = {'email': 'An account with this email already exists. Please log in instead.'}
            flash('An account with this email already exists. Please log in instead.', 'warning')
            return render_template('portal_register.html', form_data=dict(request.form), field_errors=field_errors)
        
        # Try to find supplier in RFMS (background search, don't block registration if it fails)
        rfms_supplier_id = None
        if business_name:
            try:
                supplier = rfms_client.find_supplier_by_name(business_name)
                if supplier:
                    rfms_supplier_id = supplier.get('id')
                    current_app.logger.info(f"Found RFMS supplier for {business_name}: ID {rfms_supplier_id}")
                else:
                    current_app.logger.info(f"No RFMS supplier found for {business_name}")
            except Exception as exc:
                current_app.logger.warning(f"Failed to search RFMS suppliers during registration: {exc}")
        
        # Create new installer account (active immediately)
        try:
            installer = Installer(
                name=name,
                email=email,
                phone=phone,
                business_name=business_name,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                postal_code=postal_code,
                abn=abn,
                gst_registered=gst_registered,
                rfms_supplier_id=rfms_supplier_id,  # Save supplier ID if found
                active=True,  # Active immediately
                approved=True,  # Auto-approved - no admin approval needed
                is_admin=False,
            )
            installer.set_password(password)
            db.session.add(installer)
            db.session.commit()
            
            current_app.logger.info(f"New installer account created: {email}")
            flash('Registration successful! You can now log in with your email and password.', 'success')
            return redirect(url_for('portal.login'))
        except Exception as exc:
            current_app.logger.error(f"Failed to create installer account: {exc}", exc_info=True)
            db.session.rollback()
            flash(f'An error occurred during registration: {str(exc)}. Please try again or contact support.', 'danger')
            return render_template('portal_register.html', form_data=dict(request.form), field_errors={})
    
    return render_template('portal_register.html', field_errors={})


@portal_bp.route('/logout')
@login_required
def logout():
    session.pop('installer_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('portal.login'))


@portal_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page where installers can view and update their information."""
    installer = current_installer()
    
    if request.method == 'POST':
        # Update basic information
        installer.name = request.form.get('name') or installer.name
        installer.phone = request.form.get('phone') or installer.phone
        
        # Update business information
        installer.business_name = request.form.get('business_name') or installer.business_name
        installer.address_line1 = request.form.get('address_line1') or installer.address_line1
        installer.address_line2 = request.form.get('address_line2') or installer.address_line2
        installer.city = request.form.get('city') or installer.city
        installer.state = request.form.get('state') or installer.state
        installer.postal_code = request.form.get('postal_code') or installer.postal_code
        installer.abn = request.form.get('abn') or installer.abn
        installer.gst_registered = request.form.get('gst_registered') == 'on'
        
        # Change password if provided
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if new_password:
            # Verify current password
            if not installer.check_password(current_password):
                flash('Current password is incorrect.', 'danger')
                return render_template('portal_profile.html', installer=installer)
            
            # Validate new password
            if len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
                return render_template('portal_profile.html', installer=installer)
            
            if new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
                return render_template('portal_profile.html', installer=installer)
            
            # Update password
            installer.set_password(new_password)
            flash('Password updated successfully.', 'success')
        
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('portal.profile'))
    
    return render_template('portal_profile.html', installer=installer)


@portal_bp.route('/dashboard')
@login_required
def dashboard():
    installer = current_installer()
    
    # Get existing work orders and invoices
    work_orders = WorkOrder.query.filter(
        (WorkOrder.installer_id == installer.id) | (WorkOrder.crew_code == installer.crew_code)
    ).order_by(WorkOrder.created_at.desc()).all()

    invoices = InstallerInvoice.query.filter_by(installer_id=installer.id).order_by(
        InstallerInvoice.updated_at.desc()
    ).all()

    # Find pending orders (delivered/job-costed status) that need invoicing
    pending_orders = []
    if installer.crew_code:
        try:
            # Search for jobs in the last 90 days with delivered/job-costed status
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=90)
            start_str = start_date.strftime('%m-%d-%Y')
            end_str = end_date.strftime('%m-%d-%Y')
            
            # Search for jobs with delivered or job-costed status
            jobs_result = rfms_client.find_jobs_by_date_range(
                start_str, 
                end_str, 
                crews=[installer.crew_code],
                job_status=['DELIVERED', 'JOB-COSTED', 'FINISH']
            )
            jobs = _normalize_jobs_response(jobs_result)
            
            # Filter to orders that don't have submitted invoices
            submitted_order_numbers = {
                inv.work_order.order_number 
                for inv in invoices 
                if inv.status == 'submitted' and inv.work_order and inv.work_order.order_number
            }
            
            for job in jobs:
                order_number = job.get('orderNumber') or job.get('orderNum') or job.get('order') or job.get('documentNumber')
                if order_number and order_number not in submitted_order_numbers:
                    # Check if we already have a draft invoice for this order
                    existing_wo = WorkOrder.query.filter_by(order_number=order_number).first()
                    if existing_wo and existing_wo.invoice and existing_wo.invoice.status == 'submitted':
                        continue
                    
                    pending_orders.append({
                        'order_number': order_number,
                        'job_number': job.get('jobNumber') or job.get('jobNum') or job.get('jobId'),
                        'job_name': job.get('jobName') or job.get('customerName'),
                        'status': job.get('jobStatus') or job.get('status'),
                        'scheduled_start': job.get('scheduledStartDate') or job.get('scheduledStart'),
                    })
        except Exception as exc:
            current_app.logger.warning(f"Failed to find pending orders: {exc}")

    return render_template(
        'portal_dashboard.html',
        installer=installer,
        work_orders=work_orders,
        invoices=invoices,
        pending_orders=pending_orders,
    )


@portal_bp.route('/create-invoice', methods=['POST'])
@login_required
def create_invoice_from_order():
    """Create an invoice from an RFMS order number and install date."""
    installer = current_installer()
    order_number = (request.form.get('order_number') or '').strip().upper()
    install_date = (request.form.get('install_date') or '').strip()
    
    if not order_number:
        flash('Please enter an order number.', 'danger')
        return redirect(url_for('portal.dashboard'))
    
    if not install_date:
        flash('Install date is required.', 'danger')
        return redirect(url_for('portal.dashboard'))
    
    # Validate install_date format
    # HTML date input sends YYYY-MM-DD format, but we'll accept various formats
    try:
        from datetime import datetime
        # Accept various formats
        date_valid = False
        parsed_date = None
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m-%d-%Y', '%m/%d/%Y']:
            try:
                parsed_date = datetime.strptime(install_date, fmt)
                date_valid = True
                # Normalize to YYYY-MM-DD for consistent processing
                install_date = parsed_date.strftime('%Y-%m-%d')
                break
            except ValueError:
                continue
        
        if not date_valid:
            current_app.logger.error(f"Invalid install date format: {install_date}")
            flash('Install date must be in YYYY-MM-DD, DD/MM/YYYY, or DD-MM-YYYY format.', 'danger')
            return redirect(url_for('portal.dashboard'))
        
        current_app.logger.info(f"Install date validated: {install_date} (normalized from user input)")
    except Exception as e:
        current_app.logger.error(f"Error validating install date: {e}", exc_info=True)
        flash('Invalid install date format.', 'danger')
        return redirect(url_for('portal.dashboard'))
    
    try:
        # Fetch order from RFMS with attachments
        current_app.logger.info(f"Fetching order {order_number} from RFMS for installer {installer.id}")
        order_details = rfms_client.get_order(order_number, locked=False, include_attachments=True)
        
        # Log the full response structure for debugging
        current_app.logger.debug(f"Order {order_number} response keys: {list(order_details.keys()) if isinstance(order_details, dict) else 'Not a dict'}")
        if isinstance(order_details, dict):
            # Log the raw structure to help debug line extraction
            current_app.logger.debug(f"Order {order_number} full structure: {str(order_details)[:2000]}")
        
        # Check if order exists
        if not order_details:
            current_app.logger.warning(f"Order {order_number} returned empty response")
            flash(f'Order {order_number} not found in RFMS.', 'danger')
            return redirect(url_for('portal.dashboard'))
        
        # RFMS API might return status='success' or just the data directly
        if isinstance(order_details, dict) and order_details.get('status') == 'error':
            error_msg = order_details.get('result') or order_details.get('detail') or 'Unknown error'
            current_app.logger.error(f"Order {order_number} error: {error_msg}")
            flash(f'Error retrieving order {order_number}: {error_msg}', 'danger')
            return redirect(url_for('portal.dashboard'))
        
        # Get order data - check result first (where RFMS typically stores order details)
        order_result = order_details.get('result', {})
        if not isinstance(order_result, dict):
            order_result = {}
        
        order_data = order_details.get('detail') or order_details.get('data') or order_details
        if isinstance(order_data, dict):
            order_data = order_data.get('order') or order_data
        
        # Check if work order already exists
        work_order = WorkOrder.query.filter_by(order_number=order_number).first()
        if not work_order:
            work_order = WorkOrder(
                order_number=order_number,
                installer_id=installer.id,
                crew_code=installer.crew_code,
                status='pending_invoice',
            )
            db.session.add(work_order)
            db.session.flush()
        
        # Update work order with order details
        work_order.order_payload = order_details
        work_order.installer_id = installer.id
        work_order.crew_code = installer.crew_code
        
        # Extract job ID from multiple possible locations in RFMS payload
        job_number = None
        job_id = None
        
        # Try result.jobNumber first (most common location)
        if isinstance(order_result, dict):
            job_number = order_result.get('jobNumber') or order_result.get('jobNum')
            job_id = order_result.get('jobId')
        
        # Fallback to order_data locations
        if not job_number and isinstance(order_data, dict):
            job_number = order_data.get('jobNumber') or order_data.get('jobNum')
            if not job_id:
                job_id = order_data.get('jobId')
        
        # Fallback to top-level order_details
        if not job_number:
            job_number = order_details.get('jobNumber') or order_details.get('jobNum')
            if not job_id:
                job_id = order_details.get('jobId')
        
        # If job ID not found in order payload, search for jobs by order number
        if not job_id and not job_number:
            current_app.logger.info(f"Job ID not found in order payload, searching scheduler for order {order_number}")
            try:
                # Search for jobs in the last 8 weeks (as per user requirement)
                from datetime import timedelta
                end_date = datetime.utcnow().date()
                start_date = end_date - timedelta(weeks=8)
                start_str = start_date.strftime('%m-%d-%Y')
                end_str = end_date.strftime('%m-%d-%Y')
                
                # Search for jobs with this order number
                jobs_result = rfms_client.find_jobs_by_date_range(
                    start_str,
                    end_str,
                    crews=[installer.crew_code] if installer.crew_code else None
                )
                
                # Extract jobs from response
                jobs = []
                if isinstance(jobs_result, dict):
                    detail = jobs_result.get('detail', [])
                    if isinstance(detail, list):
                        jobs = detail
                    elif isinstance(detail, dict) and 'jobs' in detail:
                        jobs = detail.get('jobs', [])
                
                # Find job matching this order number
                for job in jobs:
                    job_order_number = job.get('documentNumber') or job.get('orderNumber') or job.get('orderNum')
                    if job_order_number and job_order_number.upper() == order_number.upper():
                        job_id = job.get('jobId') or job.get('id')
                        job_number = job.get('jobNumber') or job.get('jobNum')
                        current_app.logger.info(f"Found job ID {job_id} for order {order_number} from scheduler search")
                        break
                
                if not job_id:
                    current_app.logger.warning(f"No job found in scheduler for order {order_number}")
            except Exception as e:
                current_app.logger.warning(f"Failed to search scheduler for job ID: {e}")
        
        # Store job ID or job number (prefer job ID)
        if job_id:
            work_order.job_number = str(job_id)
            current_app.logger.info(f"Stored job ID '{job_id}' for order {order_number}")
        elif job_number:
            work_order.job_number = str(job_number)
            current_app.logger.info(f"Stored job number '{job_number}' for order {order_number}")
        else:
            current_app.logger.warning(f"No job ID or job number found for order {order_number}")
        
        # Sync work order lines (with optional install date filtering)
        current_app.logger.info(f"Syncing work order lines for order {order_number}" + (f" with install date {install_date}" if install_date else ""))
        _sync_work_order_lines(work_order, order_details, install_date=install_date)
        db.session.flush()
        
        # Refresh work_order to ensure lines are loaded
        db.session.refresh(work_order)
        
        # Check if any lines were created
        if not work_order.lines:
            current_app.logger.error(f"No lines found for order {order_number} after parsing.")
            current_app.logger.error(f"Order details structure: status={order_details.get('status')}, has_result={bool(order_details.get('result'))}, has_detail={bool(order_details.get('detail'))}")
            if order_details.get('result'):
                result_lines = order_details.get('result', {}).get('lines', [])
                current_app.logger.error(f"Result has {len(result_lines) if isinstance(result_lines, list) else 0} lines")
            flash(f'Order {order_number} was found but contains no invoiceable line items (product codes 38-49 and 51). Please check the order in RFMS.', 'warning')
        else:
            current_app.logger.info(f"Successfully created {len(work_order.lines)} work order lines for order {order_number}")
        
        # Create invoice if it doesn't exist, or hydrate if it exists but has no lines
        invoice = work_order.invoice
        if not invoice:
            current_app.logger.info(f"Creating new invoice for work order {work_order.id}")
            invoice = InstallerInvoice(
                installer_id=installer.id,
                work_order_id=work_order.id,
                invoice_number=installer.generate_invoice_number(),
                status='draft',
            )
            db.session.add(invoice)
            db.session.flush()
            current_app.logger.info(f"Invoice {invoice.id} created, now hydrating from work order lines")
        else:
            current_app.logger.info(f"Invoice {invoice.id} already exists for work order {work_order.id}")
            # Check if it has lines
            from models import InvoiceLine
            existing_lines = InvoiceLine.query.filter_by(invoice_id=invoice.id).all()
            if existing_lines:
                current_app.logger.info(f"Invoice {invoice.id} already has {len(existing_lines)} lines, skipping hydration")
            else:
                current_app.logger.info(f"Invoice {invoice.id} exists but has no lines, will hydrate now")
        
        # Refresh work_order to ensure lines are available
        db.session.refresh(work_order)
        # Also query directly to ensure we get the lines
        from models import WorkOrderLine
        wo_lines = WorkOrderLine.query.filter_by(work_order_id=work_order.id).all()
        current_app.logger.info(f"Work order has {len(work_order.lines)} lines (relationship), {len(wo_lines)} lines (direct query) before hydrating invoice")
        
        # Always try to hydrate (function will skip if lines already exist)
        _hydrate_invoice_from_work_order(invoice, work_order)
        db.session.flush()
        
        # Refresh invoice to ensure lines are loaded
        db.session.refresh(invoice)
        # Also query directly
        from models import InvoiceLine
        inv_lines = InvoiceLine.query.filter_by(invoice_id=invoice.id).all()
        current_app.logger.info(f"Invoice has {len(invoice.lines)} lines (relationship), {len(inv_lines)} lines (direct query) after hydration")
        
        db.session.commit()
        
        flash(f'Invoice created for order {order_number}.', 'success')
        return redirect(url_for('portal.edit_invoice', work_order_id=work_order.id))
        
    except Exception as exc:
        current_app.logger.error(f"Failed to create invoice from order {order_number}: {exc}", exc_info=True)
        flash(f'Failed to create invoice: {str(exc)}', 'danger')
        return redirect(url_for('portal.dashboard'))


@portal_bp.route('/search-orders', methods=['POST'])
@login_required
def search_orders():
    """Search for orders by installer details (crew code)."""
    installer = current_installer()
    
    if not installer.crew_code:
        flash('Crew code not configured. Please contact administrator.', 'warning')
        return redirect(url_for('portal.dashboard'))
    
    try:
        # Search for jobs in the last 90 days
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=90)
        start_str = start_date.strftime('%m-%d-%Y')
        end_str = end_date.strftime('%m-%d-%Y')
        
        # Search for jobs with delivered or job-costed status
        jobs_result = rfms_client.find_jobs_by_date_range(
            start_str, 
            end_str, 
            crews=[installer.crew_code],
            job_status=['DELIVERED', 'JOB-COSTED', 'FINISH']
        )
        jobs = _normalize_jobs_response(jobs_result)
        
        # Get submitted order numbers
        submitted_order_numbers = {
            inv.work_order.order_number 
            for inv in InstallerInvoice.query.filter_by(installer_id=installer.id, status='submitted').all()
            if inv.work_order and inv.work_order.order_number
        }
        
        found_orders = []
        for job in jobs:
            order_number = job.get('orderNumber') or job.get('orderNum') or job.get('order') or job.get('documentNumber')
            if order_number and order_number not in submitted_order_numbers:
                found_orders.append({
                    'order_number': order_number,
                    'job_number': job.get('jobNumber') or job.get('jobNum') or job.get('jobId'),
                    'job_name': job.get('jobName') or job.get('customerName'),
                    'status': job.get('jobStatus') or job.get('status'),
                })
        
        flash(f'Found {len(found_orders)} order(s) ready for invoicing.', 'info')
        return redirect(url_for('portal.dashboard'))
        
    except Exception as exc:
        current_app.logger.error(f"Failed to search orders: {exc}", exc_info=True)
        flash('Failed to search for orders. Please try again later.', 'danger')
        return redirect(url_for('portal.dashboard'))


@portal_bp.route('/work-orders/<int:work_order_id>/invoice', methods=['GET', 'POST'])
@login_required
def edit_invoice(work_order_id: int):
    installer = current_installer()
    work_order = WorkOrder.query.get_or_404(work_order_id)

    if work_order.installer_id != installer.id and work_order.crew_code != installer.crew_code:
        flash('You do not have permission to view this work order.', 'danger')
        return redirect(url_for('portal.dashboard'))

    invoice = work_order.invoice
    if not invoice:
        invoice = InstallerInvoice(
            installer_id=installer.id,
            work_order_id=work_order.id,
            invoice_number=installer.generate_invoice_number(),
            status='draft',
        )
        db.session.add(invoice)
        db.session.flush()
        _hydrate_invoice_from_work_order(invoice, work_order)
        db.session.commit()

    if request.method == 'POST':
        descriptions = request.form.getlist('description[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        line_ids = request.form.getlist('line_id[]')

        invoice.notes = request.form.get('notes')

        updated_lines: List[InvoiceLine] = []
        subtotal = 0.0
        
        for idx, description in enumerate(descriptions):
            if not description.strip():
                continue

            line = None
            if idx < len(line_ids) and line_ids[idx]:
                try:
                    line = InvoiceLine.query.get(int(line_ids[idx]))
                except (ValueError, TypeError):
                    pass

            if not line:
                line = InvoiceLine(invoice_id=invoice.id)

            quantity = float(quantities[idx] or 0)
            unit_price = float(unit_prices[idx] or 0)
            line_total = quantity * unit_price  # Non-tax, non-GST line total
            subtotal += line_total

            line.description = description
            line.quantity = quantity
            line.unit_price = unit_price
            line.tax_rate = 0.0  # Lines are non-tax, non-GST
            line.total = line_total  # Line total is just quantity * unit_price

            db.session.add(line)
            updated_lines.append(line)
        
        # Remove lines that were not included in the submission
        for existing in list(invoice.lines):
            if existing not in updated_lines:
                db.session.delete(existing)

        # Recalculate totals from updated lines
        final_subtotal = sum(line.quantity * line.unit_price for line in updated_lines)
        invoice.subtotal = round(final_subtotal, 2)
        
        # Check if "Not claiming GST" checkbox is checked
        no_gst = request.form.get('no_gst') == '1'
        
        if no_gst:
            invoice.tax_amount = 0.0
            invoice.total = round(final_subtotal, 2)
        else:
            # Calculate GST as 10% of subtotal
            invoice.tax_amount = round(final_subtotal * 0.10, 2)
            invoice.total = round(final_subtotal + invoice.tax_amount, 2)

        attachments = request.files.getlist('attachments')
        upload_dir = current_app.config.get('INVOICE_UPLOAD_FOLDER') or os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            'invoices',
        )
        os.makedirs(upload_dir, exist_ok=True)

        uploaded_files = []
        for attachment in attachments:
            if not attachment.filename:
                continue
            filename = secure_filename(attachment.filename)
            stored_name = f"{invoice.invoice_number}_{int(datetime.utcnow().timestamp())}_{filename}"
            stored_path = os.path.join(upload_dir, stored_name)
            attachment.save(stored_path)

            invoice_attachment = InvoiceAttachment(
                invoice_id=invoice.id,
                filename=filename,
                stored_path=stored_path,
                mime_type=attachment.mimetype,
            )
            db.session.add(invoice_attachment)
            uploaded_files.append(stored_path)

        action = request.form.get('action')
        if action == 'submit':
            invoice.status = 'submitted'
            invoice.submitted_at = datetime.utcnow()
            
            # Upload photos to RFMS order when invoice is submitted
            if work_order.order_number and uploaded_files:
                try:
                    for file_path in uploaded_files:
                        # Use brackets format so photos are identified as installer photos
                        description = f"[INSTALLER PHOTOS] Installer Invoice Photo - {invoice.invoice_number}"
                        rfms_client.add_attachment(
                            document_number=work_order.order_number,
                            file_path=file_path,
                            document_type="Order",
                            description=description
                        )
                        current_app.logger.info(f"Uploaded photo {file_path} to RFMS order {work_order.order_number}")
                except Exception as exc:
                    current_app.logger.error(f"Failed to upload photos to RFMS: {exc}", exc_info=True)
                    flash('Invoice submitted, but failed to upload some photos to RFMS. Please contact support.', 'warning')
            
            # Send email notification to accounts
            try:
                _send_invoice_submission_email(invoice, installer, work_order)
            except Exception as exc:
                current_app.logger.error(f"Failed to send invoice submission email: {exc}", exc_info=True)
                # Don't fail the submission if email fails
            
            flash('Invoice submitted successfully. Accounts team has been notified.', 'success')
        else:
            flash('Invoice saved as draft.', 'success')

        db.session.commit()
        return redirect(url_for('portal.edit_invoice', work_order_id=work_order.id))

    # Fetch existing installer photos from RFMS order
    existing_installer_photos = []
    if work_order.order_number and work_order.order_payload:
        existing_installer_photos = _get_installer_photos_from_order(work_order.order_payload)
    elif work_order.order_number:
        # Fetch fresh order data if not in payload
        try:
            order_details = rfms_client.get_order(work_order.order_number, include_attachments=True)
            existing_installer_photos = _get_installer_photos_from_order(order_details)
        except Exception as exc:
            current_app.logger.warning(f"Failed to fetch installer photos for order {work_order.order_number}: {exc}")

    return render_template(
        'invoice_editor.html',
        installer=installer,
        work_order=work_order,
        invoice=invoice,
        existing_installer_photos=existing_installer_photos,
    )


@portal_bp.route('/invoices/<int:invoice_id>/export/xero', methods=['GET'])
@login_required
def export_invoice_xero(invoice_id: int):
    """Export invoice as Xero-compatible CSV format."""
    installer = current_installer()
    invoice = InstallerInvoice.query.get_or_404(invoice_id)

    if invoice.installer_id != installer.id:
        flash('You do not have permission to export this invoice.', 'danger')
        return redirect(url_for('portal.dashboard'))

    import csv
    import io
    from datetime import datetime

    output = io.StringIO()
    writer = csv.writer(output)

    # Xero CSV header
    writer.writerow([
        '*ContactName',
        '*InvoiceNumber',
        '*InvoiceDate',
        '*DueDate',
        'InventoryItemCode',
        '*Description',
        '*Quantity',
        '*UnitAmount',
        'AccountCode',
        '*TaxType',
        'TaxAmount',
        'LineAmount',
    ])

    invoice_date = invoice.submitted_at.date() if invoice.submitted_at else datetime.utcnow().date()
    due_date = invoice_date + timedelta(days=30)  # 30 day payment terms

    # Write invoice header line
    writer.writerow([
        installer.name,  # ContactName
        invoice.invoice_number,  # InvoiceNumber
        invoice_date.strftime('%d/%m/%Y'),  # InvoiceDate
        due_date.strftime('%d/%m/%Y'),  # DueDate
        '',  # InventoryItemCode
        f"Invoice {invoice.invoice_number} - {invoice.work_order.order_number if invoice.work_order else 'N/A'}",  # Description
        '',  # Quantity
        '',  # UnitAmount
        '200',  # AccountCode (Sales account - adjust as needed)
        'GST on Income',  # TaxType
        '',  # TaxAmount
        '',  # LineAmount
    ])

    # Write line items
    for line in invoice.lines:
        writer.writerow([
            '',  # ContactName
            '',  # InvoiceNumber
            '',  # InvoiceDate
            '',  # DueDate
            line.product_code or '',  # InventoryItemCode
            line.description,  # Description
            str(line.quantity),  # Quantity
            f"{line.unit_price:.2f}",  # UnitAmount
            '200',  # AccountCode
            'GST on Income' if line.tax_rate > 0 else 'Exempt',  # TaxType
            f"{(line.quantity * line.unit_price * line.tax_rate):.2f}",  # TaxAmount
            f"{(line.quantity * line.unit_price):.2f}",  # LineAmount
        ])

    output.seek(0)
    filename = f"{invoice.invoice_number}_xero_export_{datetime.utcnow().strftime('%Y%m%d')}.csv"

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


@portal_bp.route('/invoices/<int:invoice_id>/export/pdf', methods=['GET'])
@login_required
def export_invoice_pdf(invoice_id: int):
    """Export invoice as PDF."""
    installer = current_installer()
    invoice = InstallerInvoice.query.get_or_404(invoice_id)

    if invoice.installer_id != installer.id:
        flash('You do not have permission to export this invoice.', 'danger')
        return redirect(url_for('portal.dashboard'))

    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_RIGHT, TA_LEFT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#01998e'),
            spaceAfter=30,
        )
        elements.append(Paragraph(f"TAX INVOICE - {invoice.invoice_number}", title_style))
        elements.append(Spacer(1, 0.2*inch))

        # Installer details
        installer_info = [
            ['From:', installer.name],
            ['Email:', installer.email or ''],
            ['Phone:', installer.phone or ''],
        ]
        if installer.crew_code:
            installer_info.append(['Crew:', installer.crew_code])

        installer_table = Table(installer_info, colWidths=[1.5*inch, 4*inch])
        installer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(installer_table)
        elements.append(Spacer(1, 0.3*inch))

        # Invoice details
        invoice_date = invoice.submitted_at.strftime('%d %B %Y') if invoice.submitted_at else 'Draft'
        invoice_info = [
            ['Invoice Number:', invoice.invoice_number],
            ['Invoice Date:', invoice_date],
            ['Order Number:', invoice.work_order.order_number if invoice.work_order else 'N/A'],
        ]
        if invoice.work_order and invoice.work_order.job_number:
            invoice_info.append(['Job Number:', invoice.work_order.job_number])

        invoice_table = Table(invoice_info, colWidths=[1.5*inch, 4*inch])
        invoice_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ]))
        elements.append(invoice_table)
        elements.append(Spacer(1, 0.3*inch))

        # Line items table
        line_data = [['Description', 'Qty', 'Unit Price', 'Tax Rate', 'Total']]
        for line in invoice.lines:
            line_data.append([
                line.description,
                f"{line.quantity:.2f}",
                f"${line.unit_price:.2f}",
                f"{line.tax_rate*100:.1f}%",
                f"${line.total:.2f}",
            ])

        line_table = Table(line_data, colWidths=[3*inch, 0.8*inch, 1*inch, 0.8*inch, 1*inch])
        line_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#01998e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 0.3*inch))

        # Totals
        totals_data = [
            ['Subtotal:', f"${invoice.subtotal:.2f}"],
            ['Tax:', f"${invoice.tax_amount:.2f}"],
            ['Total:', f"${invoice.total:.2f}"],
        ]
        totals_table = Table(totals_data, colWidths=[4.5*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTSIZE', (-1, -1), (-1, -1), 12),  # Total row larger
            ('TEXTCOLOR', (-1, -1), (-1, -1), colors.HexColor('#01998e')),
        ]))
        elements.append(totals_table)

        # Notes
        if invoice.notes:
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph('<b>Notes:</b>', styles['Heading3']))
            elements.append(Paragraph(invoice.notes, styles['Normal']))

        doc.build(elements)
        buffer.seek(0)
        filename = f"{invoice.invoice_number}_invoice_{datetime.utcnow().strftime('%Y%m%d')}.pdf"

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except ImportError:
        flash('PDF generation requires reportlab. Install with: pip install reportlab', 'danger')
        return redirect(url_for('portal.edit_invoice', work_order_id=invoice.work_order_id))
    except Exception as exc:
        current_app.logger.error(f"Failed to generate PDF: {exc}", exc_info=True)
        flash('Failed to generate PDF. Please try again.', 'danger')
        return redirect(url_for('portal.edit_invoice', work_order_id=invoice.work_order_id))


# ==================== ADMIN ROUTES ====================

@portal_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard to manage installer accounts."""
    # Get all installers
    all_installers = Installer.query.order_by(Installer.created_at.desc()).all()
    
    # Statistics
    total_installers = Installer.query.count()
    pending_approval = Installer.query.filter_by(approved=False, active=True).count()
    approved_installers = Installer.query.filter_by(approved=True, active=True).count()
    inactive_installers = Installer.query.filter_by(active=False).count()
    
    return render_template(
        'admin_dashboard.html',
        installers=all_installers,
        total_installers=total_installers,
        pending_approval=pending_approval,
        approved_installers=approved_installers,
        inactive_installers=inactive_installers,
    )


@portal_bp.route('/admin/installers/<int:installer_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_installer(installer_id: int):
    """Approve an installer account and search for RFMS supplier if not already found."""
    installer = Installer.query.get_or_404(installer_id)
    
    # If supplier ID not found, try to search RFMS
    if not installer.rfms_supplier_id and installer.business_name:
        try:
            supplier = rfms_client.find_supplier_by_name(installer.business_name)
            if supplier:
                installer.rfms_supplier_id = supplier.get('id')
                current_app.logger.info(f"Found RFMS supplier for {installer.business_name}: ID {installer.rfms_supplier_id}")
                flash(f'RFMS supplier found: {supplier.get("name")} (ID: {installer.rfms_supplier_id})', 'info')
            else:
                current_app.logger.warning(f"No RFMS supplier found for {installer.business_name}")
                flash(f'No RFMS supplier found for "{installer.business_name}". You can manually set the supplier ID when editing.', 'warning')
        except Exception as exc:
            current_app.logger.error(f"Failed to search RFMS suppliers during approval: {exc}", exc_info=True)
            flash('Failed to search RFMS suppliers. You can manually set the supplier ID when editing.', 'warning')
    
    installer.approved = True
    installer.active = True
    db.session.commit()
    flash(f'Installer {installer.name} has been approved.', 'success')
    return redirect(url_for('portal.admin_dashboard'))


@portal_bp.route('/admin/installers/<int:installer_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_installer(installer_id: int):
    """Edit installer details (admin only)."""
    installer = Installer.query.get_or_404(installer_id)
    
    if request.method == 'POST':
        installer.name = request.form.get('name') or installer.name
        installer.email = (request.form.get('email') or '').lower().strip() or installer.email
        installer.phone = request.form.get('phone') or installer.phone
        installer.crew_code = request.form.get('crew_code') or installer.crew_code
        installer.business_name = request.form.get('business_name') or installer.business_name
        installer.address_line1 = request.form.get('address_line1') or installer.address_line1
        installer.address_line2 = request.form.get('address_line2') or installer.address_line2
        installer.city = request.form.get('city') or installer.city
        installer.state = request.form.get('state') or installer.state
        installer.postal_code = request.form.get('postal_code') or installer.postal_code
        installer.abn = request.form.get('abn') or installer.abn
        installer.gst_registered = request.form.get('gst_registered') == 'on'
        installer.rfms_installer_id = request.form.get('rfms_installer_id') or installer.rfms_installer_id
        
        # Handle RFMS supplier ID
        rfms_supplier_id_str = request.form.get('rfms_supplier_id', '').strip()
        if rfms_supplier_id_str:
            try:
                installer.rfms_supplier_id = int(rfms_supplier_id_str)
            except ValueError:
                flash('RFMS Supplier ID must be a number.', 'warning')
        
        # Search for supplier if business name changed and supplier ID not set
        search_supplier = request.form.get('search_supplier') == 'on'
        if search_supplier and installer.business_name and not installer.rfms_supplier_id:
            try:
                supplier = rfms_client.find_supplier_by_name(installer.business_name)
                if supplier:
                    installer.rfms_supplier_id = supplier.get('id')
                    flash(f'RFMS supplier found: {supplier.get("name")} (ID: {installer.rfms_supplier_id})', 'success')
                else:
                    flash(f'No RFMS supplier found for "{installer.business_name}".', 'warning')
            except Exception as exc:
                current_app.logger.error(f"Failed to search RFMS suppliers: {exc}", exc_info=True)
                flash('Failed to search RFMS suppliers.', 'danger')
        
        installer.active = request.form.get('active') == 'on'
        installer.approved = request.form.get('approved') == 'on'
        installer.is_admin = request.form.get('is_admin') == 'on'
        
        # Update password if provided
        new_password = request.form.get('password')
        if new_password:
            installer.set_password(new_password)
        
        db.session.commit()
        flash(f'Installer {installer.name} has been updated.', 'success')
        return redirect(url_for('portal.admin_dashboard'))
    
    return render_template('admin_edit_installer.html', installer=installer)


@portal_bp.route('/admin/installers/export', methods=['GET'])
@login_required
@admin_required
def export_installers():
    """Export installer data to CSV for Xero/RFMS."""
    import csv
    
    installers = Installer.query.filter_by(approved=True, active=True).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # CSV header
    writer.writerow([
        'ID',
        'Name',
        'Email',
        'Phone',
        'Business Name',
        'Address Line 1',
        'Address Line 2',
        'City',
        'State',
        'Postal Code',
        'ABN',
        'GST Registered',
        'RFMS Installer ID',
        'Crew Code',
        'Invoice Prefix',
        'Created At',
        'Status'
    ])
    
    # Write installer data
    for installer in installers:
        writer.writerow([
            installer.id,
            installer.name,
            installer.email,
            installer.phone or '',
            installer.business_name or '',
            installer.address_line1 or '',
            installer.address_line2 or '',
            installer.city or '',
            installer.state or '',
            installer.postal_code or '',
            installer.abn or '',
            'Yes' if installer.gst_registered else 'No',
            installer.rfms_installer_id or '',
            installer.crew_code or '',
            installer.invoice_prefix or 'INV',
            installer.created_at.strftime('%Y-%m-%d %H:%M:%S') if installer.created_at else '',
            'Active' if installer.active and installer.approved else 'Pending',
        ])
    
    output.seek(0)
    filename = f"installers_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


# ==================== ACCOUNTS DASHBOARD ROUTES ====================

@portal_bp.route('/accounts')
@login_required
@admin_required
def accounts_dashboard():
    """Accounts dashboard to view and manage submitted installer invoices."""
    # Get all submitted invoices
    submitted_invoices = InstallerInvoice.query.filter_by(status='submitted').order_by(
        InstallerInvoice.submitted_at.desc()
    ).all()
    
    # Get draft invoices for reference
    draft_invoices = InstallerInvoice.query.filter_by(status='draft').order_by(
        InstallerInvoice.updated_at.desc()
    ).limit(10).all()
    
    # Statistics
    total_submitted = InstallerInvoice.query.filter_by(status='submitted').count()
    total_draft = InstallerInvoice.query.filter_by(status='draft').count()
    total_amount = db.session.query(func.sum(InstallerInvoice.total)).filter_by(status='submitted').scalar() or 0
    
    # Filter options
    filter_status = request.args.get('status', 'submitted')
    filter_installer = request.args.get('installer_id', type=int)
    
    if filter_status == 'all':
        invoices = InstallerInvoice.query.order_by(InstallerInvoice.submitted_at.desc().nulls_last()).all()
    elif filter_status == 'draft':
        invoices = InstallerInvoice.query.filter_by(status='draft').order_by(InstallerInvoice.updated_at.desc()).all()
    else:
        invoices = submitted_invoices
    
    if filter_installer:
        invoices = [inv for inv in invoices if inv.installer_id == filter_installer]
    
    return render_template(
        'accounts_dashboard.html',
        invoices=invoices,
        submitted_invoices=submitted_invoices,
        draft_invoices=draft_invoices,
        total_submitted=total_submitted,
        total_draft=total_draft,
        total_amount=total_amount,
        filter_status=filter_status,
        filter_installer=filter_installer,
        all_installers=Installer.query.filter_by(approved=True, active=True).all(),
    )


@portal_bp.route('/accounts/invoices/<int:invoice_id>')
@login_required
@admin_required
def view_invoice_accounts(invoice_id: int):
    """View invoice details in accounts dashboard."""
    invoice = InstallerInvoice.query.get_or_404(invoice_id)
    
    return render_template(
        'accounts_invoice_view.html',
        invoice=invoice,
        installer=invoice.installer,
        work_order=invoice.work_order,
    )


@portal_bp.route('/accounts/invoices/<int:invoice_id>/post-provider-record', methods=['POST'])
@login_required
@admin_required
def post_provider_record(invoice_id: int):
    """Post provider record to RFMS order from installer invoice."""
    invoice = InstallerInvoice.query.get_or_404(invoice_id)
    installer = invoice.installer
    work_order = invoice.work_order
    
    if not work_order or not work_order.order_number:
        flash('Order number is required to post provider record.', 'danger')
        return redirect(url_for('portal.view_invoice_accounts', invoice_id=invoice.id))
    
    if not installer.rfms_supplier_id:
        flash('RFMS Supplier ID is required. Please set it in the installer profile.', 'danger')
        return redirect(url_for('portal.view_invoice_accounts', invoice_id=invoice.id))
    
    try:
        # Get install date from work order scheduled date or invoice submitted date
        if work_order.scheduled_start:
            install_date = work_order.scheduled_start.date()
        elif invoice.submitted_at:
            install_date = invoice.submitted_at.date()
        else:
            install_date = datetime.utcnow().date()
        
        install_date_str = install_date.strftime('%Y-%m-%d')
        
        # Get line number from work order lines (use first line if available)
        line_number = 1  # Default to line 1
        if work_order.lines:
            # Try to get the line number from the first work order line
            first_line = work_order.lines[0]
            if first_line.source_line_number:
                line_number = first_line.source_line_number
            elif first_line.id:
                line_number = first_line.id
        
        # Post provider record to RFMS
        result = rfms_client.post_provider_record(
            document_number=work_order.order_number,
            line_number=line_number,
            install_date=install_date_str,
            supplier_id=installer.rfms_supplier_id
        )
        
        if result.get('status') == 'success':
            invoice.exported_at = datetime.utcnow()
            db.session.commit()
            flash(f'Provider record posted successfully to order {work_order.order_number} for invoice {invoice.invoice_number}.', 'success')
        else:
            flash(f'Failed to post provider record: {result.get("result", "Unknown error")}', 'warning')
            
    except Exception as exc:
        current_app.logger.error(f"Failed to post provider record: {exc}", exc_info=True)
        flash(f'Error posting provider record: {str(exc)}', 'danger')
    
    return redirect(url_for('portal.view_invoice_accounts', invoice_id=invoice.id))

