# Production Configuration for Synology NAS
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging

# Create Flask app
app = Flask(__name__)

# Production configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/rfms_xtracr.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/app.log'),
        logging.StreamHandler()
    ]
)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import your existing models and routes
from models import PdfData, Quote, Job
from utils.ai_analyzer import DocumentAnalyzer

# Initialize AI analyzer
ai_analyzer = DocumentAnalyzer()

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('instance', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=False)
