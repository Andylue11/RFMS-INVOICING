#!/usr/bin/env python3
"""
Simple local runner for PDF Extractor
Run this to start the server on localhost only
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the PDF Extractor application locally"""
    print("=" * 60)
    print("🚀 PDF Extractor - Local Development Server")
    print("=" * 60)
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"📁 Working directory: {os.getcwd()}")
    print("🔄 Starting Flask application...")
    print()
    
    try:
        # Import and run the app
        from app import app
        
        with app.app_context():
            from models import db
            db.create_all()
            print("✅ Database initialized")
        
        # Run the app on port 5008 (or from PORT env var)
        port = int(os.getenv('PORT', 5008))
        print(f"🌐 Server starting on: http://127.0.0.1:{port}")
        print(f"📝 Access the app at: http://localhost:{port}")
        app.run(debug=True, host='127.0.0.1', port=port)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the correct directory and all dependencies are installed")
        print("💡 Try running: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
