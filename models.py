from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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