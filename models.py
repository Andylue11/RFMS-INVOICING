from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rfms_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    quote_number = db.Column(db.String(50))
    customer_name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    po_number = db.Column(db.String(50))
    scope_of_work = db.Column(db.Text)
    dollar_value = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'))
    job_number = db.Column(db.String(50))
    customer_name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now)

class PdfData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    customer_name = db.Column(db.String(100))
    business_name = db.Column(db.String(100))
    po_number = db.Column(db.String(50))
    scope_of_work = db.Column(db.Text)
    dollar_value = db.Column(db.Float)
    extracted_data = db.Column(db.JSON)
    processed = db.Column(db.Boolean, default=False)
    rfms_status = db.Column(db.String(50))  # new_order, billing_group_added, existing_order, new_quote, existing_quote
    rfms_document_number = db.Column(db.String(50))  # The RFMS document number
    notes = db.Column(db.Text)  # Notes from customer enquiry forms
    created_at = db.Column(db.DateTime, default=datetime.now)

class Installer(db.Model):
    """Portal installer account used for login and authorization."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    crew_code = db.Column(db.String(50), index=True)
    phone = db.Column(db.String(50))
    invoice_prefix = db.Column(db.String(20), default="INV")
    invoice_sequence = db.Column(db.Integer, default=1)
    active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)  # Admin access flag
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Business registration details
    business_name = db.Column(db.String(200))
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    postal_code = db.Column(db.String(20))
    abn = db.Column(db.String(20))  # Australian Business Number
    gst_registered = db.Column(db.Boolean, default=False)
    rfms_installer_id = db.Column(db.String(50), index=True)  # Link to RFMS installer ID (legacy)
    rfms_supplier_id = db.Column(db.Integer, index=True)  # RFMS Supplier ID for provider records
    approved = db.Column(db.Boolean, default=False)  # Admin approval required before activation

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def generate_invoice_number(self) -> str:
        """Auto-generate the next invoice number for this installer.
        Format: INV-{last_digit_of_year}{4_digit_sequence}
        Example: INV-60001 (for 2026), INV-70001 (for 2027)
        """
        from datetime import datetime
        current_year = datetime.now().year
        year_digit = str(current_year)[-1]  # Last digit of year (e.g., 6 for 2026, 7 for 2027)
        sequence = self.invoice_sequence or 1
        invoice_number = f"INV-{year_digit}{sequence:04d}"
        self.invoice_sequence = sequence + 1
        return invoice_number
    
    def get_full_address(self) -> str:
        """Get formatted full address."""
        parts = []
        if self.address_line1:
            parts.append(self.address_line1)
        if self.address_line2:
            parts.append(self.address_line2)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        return ', '.join(parts)


class WorkOrder(db.Model):
    """Installer work order pulled from RFMS Schedule Pro."""

    id = db.Column(db.Integer, primary_key=True)
    installer_id = db.Column(db.Integer, db.ForeignKey('installer.id'))
    order_number = db.Column(db.String(100), index=True)
    job_number = db.Column(db.String(100), index=True)
    crew_name = db.Column(db.String(200))
    crew_code = db.Column(db.String(100), index=True)
    scheduled_start = db.Column(db.DateTime)
    scheduled_end = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='scheduled')
    week_commencing = db.Column(db.Date)
    order_payload = db.Column(db.JSON)
    job_payload = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    installer = db.relationship('Installer', backref=db.backref('work_orders', lazy=True))


class WorkOrderLine(db.Model):
    """Individual costing lines extracted from RFMS orders."""

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_order.id'), nullable=False)
    source_line_number = db.Column(db.Integer)
    product_code = db.Column(db.String(100))
    description = db.Column(db.String(255))
    quantity = db.Column(db.Float, default=0)
    unit_price = db.Column(db.Float, default=0)
    extended_price = db.Column(db.Float, default=0)
    tax_rate = db.Column(db.Float, default=0.1)
    is_editable = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    work_order = db.relationship('WorkOrder', backref=db.backref('lines', lazy=True, cascade="all, delete-orphan"))


class InstallerInvoice(db.Model):
    """Invoice generated by installers based on their work orders."""

    id = db.Column(db.Integer, primary_key=True)
    installer_id = db.Column(db.Integer, db.ForeignKey('installer.id'), nullable=False)
    work_order_id = db.Column(db.Integer, db.ForeignKey('work_order.id'))
    invoice_number = db.Column(db.String(100), unique=True, index=True)
    status = db.Column(db.String(50), default='draft')
    subtotal = db.Column(db.Float, default=0)
    tax_amount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime)
    exported_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    installer = db.relationship('Installer', backref=db.backref('invoices', lazy=True))
    work_order = db.relationship('WorkOrder', backref=db.backref('invoice', uselist=False))


class InvoiceLine(db.Model):
    """Line items that compose an installer invoice."""

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('installer_invoice.id'), nullable=False)
    work_order_line_id = db.Column(db.Integer, db.ForeignKey('work_order_line.id'))
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, default=0)
    unit_price = db.Column(db.Float, default=0)
    tax_rate = db.Column(db.Float, default=0.1)
    total = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invoice = db.relationship('InstallerInvoice', backref=db.backref('lines', lazy=True, cascade="all, delete-orphan"))
    work_order_line = db.relationship('WorkOrderLine', backref=db.backref('invoice_lines', lazy=True))


class InvoiceAttachment(db.Model):
    """Attachments such as photos uploaded with an invoice."""

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('installer_invoice.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    stored_path = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoice = db.relationship('InstallerInvoice', backref=db.backref('attachments', lazy=True, cascade="all, delete-orphan"))


class StockReceiving(db.Model):
    """Track stock receiving events for daily reporting"""
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), nullable=False, index=True)
    sold_to_name = db.Column(db.String(200))
    city_suburb = db.Column(db.String(100))
    supplier_name = db.Column(db.String(200))
    stock_received = db.Column(db.String(200))  # Product name/style
    quantity = db.Column(db.Float)
    unit = db.Column(db.String(20))  # M2, SY, SF, etc.
    is_st_order = db.Column(db.Boolean, default=False)  # True for #ST orders
    received_date = db.Column(db.Date, nullable=False, index=True)  # Date stock was received
    received_at = db.Column(db.DateTime, default=datetime.now)  # Timestamp of record creation
    line_number = db.Column(db.Integer)  # Line number from order
    product_code = db.Column(db.String(20))
    
    def to_dict(self):
        """Convert to dictionary for reporting"""
        return {
            'order_number': self.order_number,
            'sold_to_name': self.sold_to_name or 'General Warehouse Stock' if self.is_st_order else 'Unknown',
            'city_suburb': self.city_suburb if not self.is_st_order else None,
            'supplier_name': self.supplier_name or 'Unknown',
            'stock_received': self.stock_received or 'N/A',
            'quantity': self.quantity or 0,
            'unit': self.unit or '',
            'is_st_order': self.is_st_order
        } 