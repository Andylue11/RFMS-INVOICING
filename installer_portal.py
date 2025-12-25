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

from models import (
    db,
    Installer,
    WorkOrder,
    WorkOrderLine,
    InstallerInvoice,
    InvoiceLine,
    InvoiceAttachment,
)
from utils.rfms_client import RFMSClient

portal_bp = Blueprint('portal', __name__, url_prefix='/portal')
rfms_client = RFMSClient()


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


def _normalize_jobs_response(jobs_payload: Any) -> List[Dict[str, Any]]:
    if isinstance(jobs_payload, list):
        return jobs_payload

    if not isinstance(jobs_payload, dict):
        return []

    detail = jobs_payload.get('detail') or jobs_payload.get('jobs')
    if isinstance(detail, dict):
        detail = detail.get('jobs') or detail.get('detail')
    return detail if isinstance(detail, list) else []


def _parse_order_lines(order_details: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(order_details, dict):
        return []

    product_sections: List[Dict[str, Any]] = []
    potential_sections = [
        order_details.get('products'),
        order_details.get('lineItems'),
    ]

    detail = order_details.get('detail')
    if isinstance(detail, dict):
        potential_sections.extend([
            detail.get('products'),
            detail.get('lineItems'),
        ])

    for section in potential_sections:
        if isinstance(section, list):
            product_sections = section
            break

    lines: List[Dict[str, Any]] = []
    for index, item in enumerate(product_sections):
        if not isinstance(item, dict):
            continue

        qty = float(item.get('quantity') or item.get('qty') or 0)
        unit_price = float(item.get('unitPrice') or item.get('price') or 0)
        total = float(item.get('extendedPrice') or item.get('total') or qty * unit_price)
        description = (
            item.get('description')
            or item.get('productDescription')
            or item.get('styleName')
            or 'RFMS Line'
        )
        lines.append({
            'source_line_number': item.get('lineNumber') or index + 1,
            'product_code': item.get('productCode') or item.get('productNumber'),
            'description': description,
            'quantity': qty,
            'unit_price': unit_price,
            'extended_price': total,
            'tax_rate': float(item.get('taxRate') or 0.1),
        })

    return lines


def _sync_work_order_lines(work_order: WorkOrder, order_details: Dict[str, Any]):
    lines = _parse_order_lines(order_details)
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
        line.extended_price = line_data.get('extended_price') or (line.quantity * line.unit_price)
        line.tax_rate = line_data.get('tax_rate') if line_data.get('tax_rate') is not None else 0.1
        db.session.add(line)


def _hydrate_invoice_from_work_order(invoice: InstallerInvoice, work_order: WorkOrder):
    if invoice.lines:
        return

    for wo_line in work_order.lines:
        line_total = (wo_line.extended_price or 0) or (wo_line.quantity or 0) * (wo_line.unit_price or 0)
        new_line = InvoiceLine(
            invoice_id=invoice.id,
            work_order_line_id=wo_line.id,
            description=wo_line.description or 'Work order line',
            quantity=wo_line.quantity or 0,
            unit_price=wo_line.unit_price or 0,
            tax_rate=wo_line.tax_rate or 0.1,
            total=line_total,
        )
        db.session.add(new_line)


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


@portal_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').lower().strip()
        password = request.form.get('password') or ''

        installer = Installer.query.filter_by(email=email, active=True).first()
        if installer and installer.check_password(password):
            session['installer_id'] = installer.id
            installer.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Login successful.', 'success')
            return redirect(url_for('portal.dashboard'))

        flash('Invalid email or password.', 'danger')

    return render_template('portal_login.html')


@portal_bp.route('/logout')
@login_required
def logout():
    session.pop('installer_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('portal.login'))


@portal_bp.route('/dashboard')
@login_required
def dashboard():
    installer = current_installer()
    work_orders = WorkOrder.query.filter(
        (WorkOrder.installer_id == installer.id) | (WorkOrder.crew_code == installer.crew_code)
    ).order_by(WorkOrder.scheduled_start.asc().nulls_last()).all()

    invoices = InstallerInvoice.query.filter_by(installer_id=installer.id).order_by(
        InstallerInvoice.updated_at.desc()
    ).all()

    return render_template(
        'portal_dashboard.html',
        installer=installer,
        work_orders=work_orders,
        invoices=invoices,
    )


@portal_bp.route('/sync', methods=['POST'])
@login_required
def sync_jobs():
    installer = current_installer()
    week_offset = int(request.form.get('week_offset', 0))
    target_date = datetime.utcnow().date() + timedelta(weeks=week_offset)
    week_commencing = target_date - timedelta(days=target_date.weekday())
    week_end = week_commencing + timedelta(days=6)

    start_str = week_commencing.strftime('%m-%d-%Y')
    end_str = week_end.strftime('%m-%d-%Y')

    crews = [installer.crew_code] if installer.crew_code else None

    try:
        jobs_result = rfms_client.find_jobs_by_date_range(start_str, end_str, crews=crews)
        jobs = _normalize_jobs_response(jobs_result)
    except Exception as exc:
        current_app.logger.error(f"Failed to sync jobs: {exc}", exc_info=True)
        flash('Failed to retrieve jobs from RFMS. Please try again later.', 'danger')
        return redirect(url_for('portal.dashboard'))

    imported = 0
    for job in jobs:
        if not isinstance(job, dict):
            continue

        order_number = job.get('orderNumber') or job.get('orderNum') or job.get('order') or job.get('documentNumber')
        crew_name = job.get('crewName') or job.get('crew')
        job_number = job.get('jobNumber') or job.get('jobNum') or job.get('jobId')

        scheduled_start = job.get('scheduledStartDate') or job.get('scheduledStart') or job.get('installStartDate')
        scheduled_end = job.get('scheduledEndDate') or job.get('scheduledEnd') or job.get('installEndDate')

        work_order = WorkOrder.query.filter_by(order_number=order_number).first()
        if not work_order:
            work_order = WorkOrder(order_number=order_number)

        work_order.installer_id = installer.id
        work_order.job_number = str(job_number) if job_number else None
        work_order.crew_name = crew_name
        work_order.crew_code = installer.crew_code
        work_order.scheduled_start = _parse_date(scheduled_start)
        work_order.scheduled_end = _parse_date(scheduled_end)
        work_order.status = job.get('status') or job.get('jobStatus') or work_order.status or 'scheduled'
        work_order.week_commencing = week_commencing
        work_order.job_payload = job
        db.session.add(work_order)
        db.session.flush()

        if order_number:
            try:
                order_details = rfms_client.get_order(order_number)
                work_order.order_payload = order_details
                _sync_work_order_lines(work_order, order_details)
            except Exception as exc:
                current_app.logger.warning(f"Unable to fetch order {order_number}: {exc}")

        imported += 1

    db.session.commit()

    flash(f'Synced {imported} job(s) for {week_commencing:%Y-%m-%d}.', 'success')
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
        tax_rates = request.form.getlist('tax_rate[]')
        line_ids = request.form.getlist('line_id[]')

        invoice.notes = request.form.get('notes')

        updated_lines: List[InvoiceLine] = []
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
            tax_rate = float(tax_rates[idx] or 0.1)
            line_total = quantity * unit_price

            line.description = description
            line.quantity = quantity
            line.unit_price = unit_price
            line.tax_rate = tax_rate
            line.total = line_total * (1 + tax_rate)

            db.session.add(line)
            updated_lines.append(line)

        # Remove lines that were not included in the submission
        for existing in list(invoice.lines):
            if existing not in updated_lines:
                db.session.delete(existing)

        invoice.subtotal = sum(line.quantity * line.unit_price for line in invoice.lines)
        invoice.tax_amount = sum((line.quantity * line.unit_price) * line.tax_rate for line in invoice.lines)
        invoice.total = invoice.subtotal + invoice.tax_amount

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
                        description = f"Installer Invoice Photo - {invoice.invoice_number}"
                        rfms_client.add_attachment(
                            document_number=work_order.order_number,
                            file_path=file_path,
                            document_type="Order",
                            description=description
                        )
                        current_app.logger.info(f"Uploaded photo {file_path} to RFMS order {work_order.order_number}")
                    flash('Invoice submitted and photos uploaded to RFMS order.', 'success')
                except Exception as exc:
                    current_app.logger.error(f"Failed to upload photos to RFMS: {exc}", exc_info=True)
                    flash('Invoice submitted, but failed to upload some photos to RFMS. Please contact support.', 'warning')
            else:
                flash('Invoice submitted for processing.', 'success')
        else:
            flash('Invoice saved as draft.', 'success')

        db.session.commit()
        return redirect(url_for('portal.edit_invoice', work_order_id=work_order.id))

    return render_template(
        'invoice_editor.html',
        installer=installer,
        work_order=work_order,
        invoice=invoice,
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

