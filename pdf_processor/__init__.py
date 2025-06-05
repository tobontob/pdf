"""
PDF Processor - A comprehensive PDF processing web application
"""

from flask import Flask
import os
from flask_cors import CORS

def create_app():
    app = Flask(__name__,
                static_folder='static',  # pdf_processor/static을 사용
                static_url_path='/static')
    CORS(app)
    
    # Configure application
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching
    app.config['TEMPLATES_AUTO_RELOAD'] = True    # Auto reload templates
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.debug = True  # Enable debug mode

    # Print debug information
    print(f"App root path: {app.root_path}")
    print(f"Static folder: {app.static_folder}")
    print(f"Template folder: {app.template_folder}")

    # Configure upload folder
    UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
    PROCESSED_FOLDER = os.path.join(app.root_path, 'processed')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        print(f"Created upload folder: {UPLOAD_FOLDER}")
    if not os.path.exists(PROCESSED_FOLDER):
        os.makedirs(PROCESSED_FOLDER)
        print(f"Created processed folder: {PROCESSED_FOLDER}")
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

    # Import and register routes
    from . import app as main_bp
    app.register_blueprint(main_bp.bp)

    return app 