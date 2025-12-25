

app.py
+20
-1

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
from models import (
    db,
    Quote,
    Job,
    PdfData,
    Installer,
    WorkOrder,
    WorkOrderLine,
    InstallerInvoice,
    InvoiceLine,
    InvoiceAttachment,
)
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
from installer_portal import portal_bp, ensure_default_installer_account

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
app.config['INVOICE_UPLOAD_FOLDER'] = os.getenv(
    'INVOICE_UPLOAD_FOLDER',
    os.path.join(app.config['UPLOAD_FOLDER'], 'invoices')
)

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
os.makedirs(app.config['INVOICE_UPLOAD_FOLDER'], exist_ok=True)

# Initialize database with app
db.init_app(app)
app.register_blueprint(portal_bp)

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
@@ -4638,50 +4656,51 @@ def create_multiple_installer_pdfs():
        
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
        ensure_default_installer_account(app)
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
