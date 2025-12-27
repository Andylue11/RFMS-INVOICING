import os
import io
import base64
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


def _parse_job_lines(job_details: Dict[str, Any], order_lines: List[Dict[str, Any]] = None, install_date: str = None) -> List[Dict[str, Any]]:
    """
    Parse lines from job payload (from /order/jobs endpoint).
    Job lines are more specific to the booking and should be used if available.
    Matches job lines to order lines to get pricing information.
    
    Args:
        job_details: Job details dictionary from /order/jobs endpoint (the primary_job object)
        order_lines: Order lines from order payload (for pricing information)
        install_date: Optional install date for filtering (should match job's scheduledStart)
    """
    if not isinstance(job_details, dict):
        return []
    
    job_lines = job_details.get('lines', [])
    if not isinstance(job_lines, list) or not job_lines:
        return []
    
    current_app.logger.info(f"_parse_job_lines: Found {len(job_lines)} lines in job payload")
    
    # Get job scheduled date for filtering
    job_scheduled_date = job_details.get('scheduledStart') or job_details.get('scheduledEnd')
    
    # Create a mapping of order lines by lineNumber and styleName for matching
    order_lines_map = {}
    if order_lines:
        for order_line in order_lines:
            line_num = order_line.get('lineNumber')
            style_name = (order_line.get('styleName') or '').strip().upper()
            # Map by line number (primary) and style name (fallback)
            if line_num:
                order_lines_map[str(line_num)] = order_line
            if style_name and line_num:
                order_lines_map[f"{style_name}_{line_num}"] = order_line
    
    parsed_lines = []
    for job_line in job_lines:
        if not isinstance(job_line, dict):
            continue
        
        line_number = job_line.get('lineNumber')
        style_name = (job_line.get('styleName') or '').strip()
        color_name = (job_line.get('colorName') or '').strip()
        quantity = float(job_line.get('quantity') or job_line.get('length') or 0)
        units = job_line.get('units', '')
        
        # Find matching order line for pricing
        order_line = None
        if line_number:
            order_line = order_lines_map.get(str(line_number))
        if not order_line and style_name:
            # Try to match by style name
            style_upper = style_name.upper()
            for key, ord_line in order_lines_map.items():
                if ord_line.get('styleName', '').upper() == style_upper:
                    order_line = ord_line
                    break
        
        # Build description
        if style_name and color_name:
            description = f"{style_name} {color_name}".strip()
        elif style_name:
            description = style_name
        elif color_name:
            description = color_name
        else:
            description = job_line.get('material') or 'Service Line'
        
        # Get pricing from order line (if found), otherwise default to 0
        roll_item_number = ''
        if order_line:
            unit_price = float(order_line.get('unitCost') or order_line.get('unitPrice') or 0)
            product_code = order_line.get('productCode') or ''
            roll_item_number = order_line.get('rollItemNumber') or order_line.get('roll_item_number') or ''
        else:
            unit_price = 0.0
            product_code = ''
            current_app.logger.warning(f"_parse_job_lines: No matching order line found for job line {line_number} ({style_name})")
        
        # Check if this is an installer invoice line (product codes 38-49 and 51)
        # If we have product code, check it; otherwise try to infer from style name
        is_installer_line = False
        if product_code:
            is_installer_line = _is_installer_invoice_line(order_line) if order_line else False
        else:
            # Try to infer from style name (installer invoice lines are typically labor/service)
            style_upper = style_name.upper()
            installer_keywords = ['INSTALL', 'LABOR', 'TRAVEL', 'DUMP', 'TAKE UP', 'GLUE', 'NEGOTIATED']
            if any(keyword in style_upper for keyword in installer_keywords):
                is_installer_line = True
        
        if not is_installer_line:
            current_app.logger.debug(f"_parse_job_lines: Skipping job line {line_number} - not an installer invoice line")
            continue
        
        # Calculate line total
        total = quantity * unit_price
        
        parsed_lines.append({
            'source_line_number': int(line_number) if line_number else 0,
            'product_code': product_code,
            'roll_item_number': roll_item_number,
            'description': description,
            'quantity': quantity,
            'unit_price': unit_price,
            'extended_price': total,
            'tax_rate': 0.0,  # Lines are non-tax for installer invoices
        })
    
    current_app.logger.info(f"_parse_job_lines: Parsed {len(parsed_lines)} installer invoice lines from job payload")
    return parsed_lines


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
        # Get rollItemNumber for Service Code display
        roll_item_number = item.get('rollItemNumber') or item.get('roll_item_number') or ''
        
        lines.append({
            'source_line_number': int(line_number) if line_number else (index + 1),
            'product_code': product_code,
            'roll_item_number': roll_item_number,
            'description': description,
            'quantity': qty,
            'unit_price': unit_price,
            'extended_price': total,
            'tax_rate': float(item.get('taxRate') or item.get('tax_rate') or 0.1),
        })

    current_app.logger.info(f"_parse_order_lines: Parsed {len(lines)} service/labour lines for invoice")
    return lines


def _sync_work_order_lines(work_order: WorkOrder, order_details: Dict[str, Any] = None, job_details: Dict[str, Any] = None, install_date: str = None):
    """
    Sync work order lines from either job payload (preferred) or order payload (fallback).
    
    IMPORTANT: If job_details exists and has lines, ONLY use job lines (don't fall back to order lines).
    This ensures we only show lines that are actually in the scheduled booking, not all order lines.
    
    Args:
        work_order: WorkOrder object to sync lines for
        order_details: Order details from get_order() endpoint
        job_details: Job details from get_order_jobs() endpoint (primary_job object)
        install_date: Optional install date for filtering
    """
    lines = []
    
    # Try to use job lines first (more specific to the booking)
    # If job_details exists, we should ONLY use job lines, even if none match installer codes
    job_lines_exist = False
    if job_details:
        job_lines_raw = job_details.get('lines', [])
        if isinstance(job_lines_raw, list) and len(job_lines_raw) > 0:
            job_lines_exist = True
            current_app.logger.info(f"_sync_work_order_lines: Job has {len(job_lines_raw)} lines - will ONLY use job lines (no fallback to order lines)")
            # Get order lines for pricing information only
            order_lines_result = order_details.get('result', {}) if order_details else {}
            order_lines_list = order_lines_result.get('lines', []) if isinstance(order_lines_result, dict) else []
            if not order_lines_list:
                detail = order_details.get('detail', {}) if order_details else {}
                order_lines_list = detail.get('lines', []) if isinstance(detail, dict) else []
            
            lines = _parse_job_lines(job_details, order_lines=order_lines_list, install_date=install_date)
            current_app.logger.info(f"_sync_work_order_lines: Parsed {len(lines)} installer invoice lines from job payload")
    
    # Fall back to order lines ONLY if job_details doesn't exist or has no lines
    if not job_lines_exist and order_details:
        current_app.logger.info("_sync_work_order_lines: No job lines found, falling back to parsing lines from order payload")
        lines = _parse_order_lines(order_details, install_date=install_date)
    
    if not lines:
        current_app.logger.warning("_sync_work_order_lines: No lines found in job or order payload")
        # Delete all existing lines if we have no new lines
        for existing_line in list(work_order.lines):
            db.session.delete(existing_line)
        return

    # Delete all existing work order lines first to ensure we only have lines from the current sync
    # This is important because if we previously synced with order lines (that included lines not in the job),
    # those old lines would remain if we didn't delete them
    for existing_line in list(work_order.lines):
        db.session.delete(existing_line)
    db.session.flush()  # Flush deletions before creating new lines

    existing_by_source = {}  # Start fresh since we deleted all existing lines

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
    
    # Get existing work orders and invoices (limit to 5 most recent for dashboard)
    work_orders = WorkOrder.query.filter(
        (WorkOrder.installer_id == installer.id) | (WorkOrder.crew_code == installer.crew_code)
    ).order_by(WorkOrder.created_at.desc()).limit(5).all()

    invoices = InstallerInvoice.query.filter_by(installer_id=installer.id).order_by(
        InstallerInvoice.updated_at.desc()
    ).limit(5).all()
    
    # Get all submitted invoices for pending orders check (not limited to 5)
    all_submitted_invoices = InstallerInvoice.query.filter_by(
        installer_id=installer.id, 
        status='submitted'
    ).all()

    # Update work orders with job status from scheduler using /order/jobs endpoint (definitive method)
    # This is more reliable than searching by date range
    if installer.crew_code:
        try:
            # Update work orders with job info using /order/jobs endpoint
            # This is more reliable than searching by date range
            for wo in work_orders:
                if wo.order_number:
                    try:
                        jobs_response = rfms_client.get_order_jobs(wo.order_number)
                        scheduled_jobs = jobs_response.get('detail', [])
                        
                        if scheduled_jobs and isinstance(scheduled_jobs, list) and len(scheduled_jobs) > 0:
                            primary_job = scheduled_jobs[0]
                            
                            # Update job_number (job ID)
                            job_id = primary_job.get('jobId') or primary_job.get('id')
                            if job_id:
                                wo.job_number = str(job_id)
                            
                            # Update status
                            job_status = primary_job.get('jobStatus') or primary_job.get('status')
                            if job_status:
                                wo.status = job_status
                            
                            # Update scheduled_start date
                            scheduled_date_str = primary_job.get('scheduledStart') or primary_job.get('scheduledEnd')
                            if scheduled_date_str:
                                try:
                                    # Handle YYYYMMDD format
                                    if len(scheduled_date_str) == 8 and scheduled_date_str.isdigit():
                                        wo.scheduled_start = datetime.strptime(scheduled_date_str, '%Y%m%d')
                                    # Handle YYYY-MM-DD format
                                    elif '-' in scheduled_date_str:
                                        wo.scheduled_start = datetime.strptime(scheduled_date_str.split()[0], '%Y-%m-%d')
                                except (ValueError, TypeError):
                                    pass
                    except Exception as e:
                        current_app.logger.warning(f"Failed to get job details for order {wo.order_number}: {e}")
            
            db.session.commit()
        except Exception as exc:
            current_app.logger.warning(f"Failed to update work orders with scheduler info: {exc}")

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
                for inv in all_submitted_invoices 
                if inv.work_order and inv.work_order.order_number
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
        
        # Extract job ID, scheduled date, and job status using /order/jobs/{order_number} endpoint
        # This is the definitive way to get job information (as per RFMS-BUILDERS implementation)
        job_id = None
        scheduled_start = None
        job_status = None
        
        try:
            jobs_response = rfms_client.get_order_jobs(order_number)
            scheduled_jobs = jobs_response.get('detail', [])
            
            if scheduled_jobs and isinstance(scheduled_jobs, list) and len(scheduled_jobs) > 0:
                primary_job = scheduled_jobs[0]
                
                # Extract job ID
                job_id = primary_job.get('jobId') or primary_job.get('id')
                
                # Extract scheduled date (format: YYYYMMDD, convert to datetime)
                scheduled_date_str = primary_job.get('scheduledStart') or primary_job.get('scheduledEnd')
                if scheduled_date_str:
                    try:
                        # Handle YYYYMMDD format
                        if len(scheduled_date_str) == 8 and scheduled_date_str.isdigit():
                            scheduled_start = datetime.strptime(scheduled_date_str, '%Y%m%d')
                        # Handle YYYY-MM-DD format
                        elif '-' in scheduled_date_str:
                            scheduled_start = datetime.strptime(scheduled_date_str.split()[0], '%Y-%m-%d')
                        else:
                            scheduled_start = datetime.strptime(scheduled_date_str.split()[0], '%Y-%m-%d')
                    except (ValueError, TypeError) as e:
                        current_app.logger.warning(f"Could not parse scheduled date '{scheduled_date_str}': {e}")
                
                # Extract job status
                job_status = primary_job.get('jobStatus') or primary_job.get('status')
                
                current_app.logger.info(f"Found job ID {job_id}, scheduled date {scheduled_start}, status {job_status} for order {order_number}")
            else:
                current_app.logger.info(f"No scheduled jobs found for order {order_number}")
        except Exception as e:
            current_app.logger.warning(f"Failed to get job details for order {order_number}: {e}")
        
        # Store job ID, scheduled date, and status
        if job_id:
            work_order.job_number = str(job_id)
        if scheduled_start:
            work_order.scheduled_start = scheduled_start
        if job_status:
            work_order.status = job_status
        
        # Ensure job_number is saved to database
        db.session.flush()
        
        # Get job details for line extraction (if job exists)
        job_details_for_lines = None
        if job_id:
            try:
                jobs_response = rfms_client.get_order_jobs(order_number)
                scheduled_jobs = jobs_response.get('detail', [])
                if scheduled_jobs and isinstance(scheduled_jobs, list) and len(scheduled_jobs) > 0:
                    job_details_for_lines = scheduled_jobs[0]
                    current_app.logger.info(f"Retrieved job details with {len(job_details_for_lines.get('lines', []))} lines for line extraction")
            except Exception as e:
                current_app.logger.warning(f"Could not get job details for line extraction: {e}")
        
        # Sync work order lines (with optional install date filtering)
        # Prefer job lines over order lines (job lines are more specific to the booking)
        current_app.logger.info(f"Syncing work order lines for order {order_number}" + (f" with install date {install_date}" if install_date else ""))
        _sync_work_order_lines(work_order, order_details=order_details, job_details=job_details_for_lines, install_date=install_date)
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

        # Update invoice number if provided
        new_invoice_number = request.form.get('invoice_number', '').strip()
        if new_invoice_number:
            invoice.invoice_number = new_invoice_number.upper()
        
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
            # Validate that installer photos exist (either existing from RFMS or newly uploaded)
            existing_photos = []
            if work_order.order_number:
                if work_order.order_payload:
                    existing_photos = _get_installer_photos_from_order(work_order.order_payload)
                elif work_order.order_number:
                    try:
                        order_details = rfms_client.get_order(work_order.order_number, include_attachments=True)
                        existing_photos = _get_installer_photos_from_order(order_details)
                    except Exception as exc:
                        current_app.logger.warning(f"Failed to check existing photos for order {work_order.order_number}: {exc}")
            
            if not existing_photos and not uploaded_files:
                flash('Please upload at least one installer photo before submitting the invoice.', 'warning')
                db.session.rollback()
                return redirect(url_for('portal.edit_invoice', work_order_id=work_order.id))
            
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

    # Refresh work_order to ensure job_number is loaded from database
    db.session.refresh(work_order)
    # Also query directly to ensure we have the latest job_number
    work_order = WorkOrder.query.get(work_order.id)
    current_app.logger.info(f"Displaying invoice editor - Order: {work_order.order_number}, Job Number: {work_order.job_number}")

    # Fetch existing installer photos from RFMS order
    existing_installer_photos = []
    order_details_for_customer = None
    if work_order.order_number and work_order.order_payload:
        existing_installer_photos = _get_installer_photos_from_order(work_order.order_payload)
        order_details_for_customer = work_order.order_payload
    elif work_order.order_number:
        # Fetch fresh order data if not in payload
        try:
            order_details = rfms_client.get_order(work_order.order_number, include_attachments=True)
            existing_installer_photos = _get_installer_photos_from_order(order_details)
            order_details_for_customer = order_details
        except Exception as exc:
            current_app.logger.warning(f"Failed to fetch installer photos for order {work_order.order_number}: {exc}")
    
    # Extract customer details (Sold To and Ship To) and rollItemNumber mapping from order payload
    sold_to_details = None
    ship_to_details = None
    roll_item_numbers_map = {}  # Map source_line_number to rollItemNumber
    if order_details_for_customer:
        order_result = order_details_for_customer.get('result', {})
        
        # Extract rollItemNumber mapping from order lines (do this first)
        order_lines = order_result.get('lines', [])
        for order_line in order_lines:
            line_num = order_line.get('lineNumber')
            roll_item_num = order_line.get('rollItemNumber') or ''
            if line_num and roll_item_num:
                # Store with both int and str keys to handle type mismatches
                roll_item_numbers_map[int(line_num)] = roll_item_num
                roll_item_numbers_map[str(line_num)] = roll_item_num
        
        # Extract Sold To details
        sold_to = order_result.get('soldTo', {})
        if sold_to:
            # Build sold to name
            sold_to_name_parts = []
            if sold_to.get('businessName'):
                sold_to_name_parts.append(sold_to.get('businessName'))
            if sold_to.get('firstName'):
                sold_to_name_parts.append(sold_to.get('firstName'))
            if sold_to.get('lastName'):
                sold_to_name_parts.append(sold_to.get('lastName'))
            sold_to_name = ' '.join(sold_to_name_parts) if sold_to_name_parts else 'N/A'
            
            sold_to_details = {
                'name': sold_to_name,
            }
        
        # Extract Ship To details
        ship_to = order_result.get('shipTo', {})
        if ship_to:
            # Build ship to name
            ship_to_name_parts = []
            if ship_to.get('businessName'):
                ship_to_name_parts.append(ship_to.get('businessName'))
            if ship_to.get('firstName'):
                ship_to_name_parts.append(ship_to.get('firstName'))
            if ship_to.get('lastName'):
                ship_to_name_parts.append(ship_to.get('lastName'))
            ship_to_name = ' '.join(ship_to_name_parts) if ship_to_name_parts else 'N/A'
            
            # Build address - split into street address and suburb
            street_address_parts = []
            if ship_to.get('address1'):
                street_address_parts.append(ship_to.get('address1'))
            if ship_to.get('address2'):
                street_address_parts.append(ship_to.get('address2'))
            street_address = ', '.join(street_address_parts) if street_address_parts else 'N/A'
            
            # Build suburb line (city, state, postcode)
            suburb_parts = []
            if ship_to.get('city'):
                suburb_parts.append(ship_to.get('city'))
            if ship_to.get('state'):
                suburb_parts.append(ship_to.get('state'))
            if ship_to.get('postalCode'):
                suburb_parts.append(ship_to.get('postalCode'))
            suburb = ' '.join(suburb_parts) if suburb_parts else 'N/A'
            
            ship_to_details = {
                'name': ship_to_name,
                'street_address': street_address,
                'suburb': suburb,
            }

    return render_template(
        'invoice_editor.html',
        installer=installer,
        work_order=work_order,
        invoice=invoice,
        existing_installer_photos=existing_installer_photos,
        sold_to_details=sold_to_details,
        ship_to_details=ship_to_details,
        roll_item_numbers_map=roll_item_numbers_map,
    )


@portal_bp.route('/attachment-thumbnail/<int:attachment_id>')
@login_required
def get_attachment_thumbnail(attachment_id: int):
    """Get a thumbnail preview of an attachment."""
    try:
        # Get attachment data from RFMS
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
            from flask import abort
            abort(404, 'No file data found')
        
        # Decode base64 data
        try:
            file_bytes = base64.b64decode(file_data_b64)
        except Exception as e:
            current_app.logger.error(f"Failed to decode attachment {attachment_id}: {e}")
            from flask import abort
            abort(500, 'Failed to decode attachment')
        
        # Determine content type
        file_extension = None
        if isinstance(attachment_data, dict):
            file_extension = (attachment_data.get('fileExtension') or 
                            attachment_data.get('extension') or 
                            attachment_data.get('file_extension') or '')
        
        # Determine MIME type
        if file_extension:
            file_extension = file_extension.lstrip('.').lower()
            mime_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp',
                'bmp': 'image/bmp',
                'pdf': 'application/pdf',
            }
            content_type = mime_types.get(file_extension, 'application/octet-stream')
        else:
            content_type = 'image/jpeg'  # Default
        
        return send_file(
            io.BytesIO(file_bytes),
            mimetype=content_type,
            as_attachment=False
        )
        
    except Exception as exc:
        current_app.logger.error(f"Failed to get attachment thumbnail {attachment_id}: {exc}", exc_info=True)
        from flask import abort
        abort(500, f'Error retrieving attachment: {str(exc)}')


@portal_bp.route('/attachment-file/<int:attachment_id>')
@login_required
def get_attachment_file(attachment_id: int):
    """Get the full attachment file."""
    try:
        # Get attachment data from RFMS
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
            from flask import abort
            abort(404, 'No file data found')
        
        # Decode base64 data
        try:
            file_bytes = base64.b64decode(file_data_b64)
        except Exception as e:
            current_app.logger.error(f"Failed to decode attachment {attachment_id}: {e}")
            from flask import abort
            abort(500, 'Failed to decode attachment')
        
        # Get filename and content type
        filename = 'attachment'
        file_extension = None
        if isinstance(attachment_data, dict):
            filename = (attachment_data.get('name') or 
                       attachment_data.get('filename') or 
                       attachment_data.get('description') or 
                       'attachment')
            file_extension = (attachment_data.get('fileExtension') or 
                            attachment_data.get('extension') or 
                            attachment_data.get('file_extension') or '')
        
        if file_extension:
            file_extension = file_extension.lstrip('.').lower()
            if not filename.endswith(f'.{file_extension}'):
                filename = f"{filename}.{file_extension}"
        
        # Determine MIME type
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'bmp': 'image/bmp',
            'pdf': 'application/pdf',
        }
        content_type = mime_types.get(file_extension, 'application/octet-stream') if file_extension else 'application/octet-stream'
        
        return send_file(
            io.BytesIO(file_bytes),
            mimetype=content_type,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as exc:
        current_app.logger.error(f"Failed to get attachment file {attachment_id}: {exc}", exc_info=True)
        from flask import abort
        abort(500, f'Error retrieving attachment: {str(exc)}')


@portal_bp.route('/work-orders/<int:work_order_id>/delete', methods=['POST'])
@login_required
def delete_work_order(work_order_id: int):
    """Delete a work order and its associated invoice."""
    installer = current_installer()
    work_order = WorkOrder.query.get_or_404(work_order_id)
    
    # Check permissions
    if work_order.installer_id != installer.id and work_order.crew_code != installer.crew_code:
        flash('You do not have permission to delete this work order.', 'danger')
        return redirect(url_for('portal.dashboard'))
    
    # Delete associated invoice and its lines/attachments
    if work_order.invoice:
        invoice = work_order.invoice
        
        # Delete invoice lines
        for line in invoice.lines:
            db.session.delete(line)
        
        # Delete invoice attachments
        for attachment in invoice.attachments:
            db.session.delete(attachment)
        
        # Delete the invoice
        db.session.delete(invoice)
    
    # Delete work order lines
    for line in work_order.lines:
        db.session.delete(line)
    
    # Delete the work order
    db.session.delete(work_order)
    db.session.commit()
    
    flash(f'Work order {work_order.order_number} and its invoice have been deleted.', 'success')
    return redirect(url_for('portal.dashboard'))


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


@portal_bp.route('/export-invoices', methods=['GET', 'POST'])
@login_required
def export_invoices():
    """Export invoices page - allows selection and bulk export."""
    installer = current_installer()
    
    if request.method == 'POST':
        action = request.form.get('action')
        selected_invoice_ids = request.form.getlist('invoice_ids')
        
        if not selected_invoice_ids:
            flash('Please select at least one invoice to export.', 'warning')
            return redirect(url_for('portal.export_invoices'))
        
        # Get selected invoices
        invoices = InstallerInvoice.query.filter(
            InstallerInvoice.id.in_(selected_invoice_ids),
            InstallerInvoice.installer_id == installer.id
        ).all()
        
        if not invoices:
            flash('No valid invoices selected.', 'danger')
            return redirect(url_for('portal.export_invoices'))
        
        if action == 'export_xero':
            # Export to Xero CSV
            return _export_invoices_xero(invoices, installer)
        elif action == 'export_pdf_email':
            # Export to PDF and email
            email_address = request.form.get('email_address', '').strip()
            if not email_address:
                flash('Please provide an email address.', 'warning')
                return redirect(url_for('portal.export_invoices'))
            return _export_invoices_pdf_email(invoices, installer, email_address)
        else:
            flash('Invalid export action.', 'danger')
            return redirect(url_for('portal.export_invoices'))
    
    # GET request - show export page
    # Get all invoices for this installer
    all_invoices = InstallerInvoice.query.filter_by(
        installer_id=installer.id
    ).order_by(InstallerInvoice.created_at.desc()).all()
    
    return render_template(
        'export_invoices.html',
        installer=installer,
        invoices=all_invoices,
    )


def _export_invoices_xero(invoices: List[InstallerInvoice], installer: Installer):
    """Export multiple invoices to Xero CSV format."""
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
    
    for invoice in invoices:
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
    filename = f"invoices_xero_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


def _export_invoices_pdf_email(invoices: List[InstallerInvoice], installer: Installer, email_address: str):
    """Export multiple invoices to PDF and email them."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfgen import canvas
        import tempfile
        import os
        
        # Create temporary PDF file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        doc = SimpleDocTemplate(temp_file.name, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#01998e'),
            spaceAfter=30,
        )
        
        # Generate PDF for each invoice
        for idx, invoice in enumerate(invoices):
            if idx > 0:
                elements.append(PageBreak())
            
            # Title
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
            line_data = [['Description', 'Quantity', 'Unit Price', 'Line Total']]
            for line in invoice.lines:
                line_data.append([
                    line.description,
                    f"{line.quantity:.2f}",
                    f"${line.unit_price:.2f}",
                    f"${(line.quantity * line.unit_price):.2f}",
                ])
            
            line_table = Table(line_data, colWidths=[3.5*inch, 0.8*inch, 1*inch, 1*inch])
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
                ['GST (10%):', f"${invoice.tax_amount:.2f}"],
                ['Total:', f"${invoice.total:.2f}"],
            ]
            totals_table = Table(totals_data, colWidths=[1.5*inch, 1*inch])
            totals_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('TEXTCOLOR', (-1, -1), (-1, -1), colors.HexColor('#01998e')),
            ]))
            elements.append(totals_table)
            
            # Notes
            if invoice.notes:
                elements.append(Spacer(1, 0.3*inch))
                elements.append(Paragraph('<b>Notes:</b>', styles['Heading3']))
                elements.append(Paragraph(invoice.notes, styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        
        # Send email with PDF attachment
        from_address = os.getenv('REPORTS_EMAIL_ADDRESS', installer.email or 'reports@atozflooringsolutions.com.au')
        subject = f"Invoice Export - {len(invoices)} Invoice(s)"
        
        # Create invoice list for email body
        invoice_list = '\n'.join([f"<li>{inv.invoice_number} - {inv.work_order.order_number if inv.work_order else 'N/A'}</li>" for inv in invoices])
        body = f"""
        <html>
        <body>
            <p>Dear {installer.name},</p>
            <p>Please find attached {len(invoices)} invoice(s) in PDF format:</p>
            <ul>
                {invoice_list}
            </ul>
            <p>Best regards,<br>A to Z Flooring Solutions</p>
        </body>
        </html>
        """
        
        # Send email with attachment
        email_sender.send_email_with_attachment(
            from_address=from_address,
            to_address=email_address,
            subject=subject,
            body=body,
            body_type='HTML',
            attachment_path=temp_file.name,
            attachment_name=f"invoices_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        flash(f'Successfully exported {len(invoices)} invoice(s) to PDF and sent to {email_address}.', 'success')
        return redirect(url_for('portal.export_invoices'))
        
    except ImportError:
        flash('PDF generation requires reportlab. Install with: pip install reportlab', 'danger')
        return redirect(url_for('portal.export_invoices'))
    except Exception as exc:
        current_app.logger.error(f"Failed to export invoices to PDF and email: {exc}", exc_info=True)
        flash(f'Failed to export invoices. Error: {str(exc)}', 'danger')
        return redirect(url_for('portal.export_invoices'))


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

