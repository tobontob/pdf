# PDF Processing Application

This application provides various PDF processing functionalities including:
- PDF conversion (to/from Word, Excel, PowerPoint, Images)
- PDF organization (merge, split, rotate, delete pages)
- PDF editing (text, watermark, page numbers, annotations)
- OCR capabilities
- Security features (encryption/decryption)

## Setup Instructions

1. Install Python 3.8 or higher
2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR:
- Windows: Download installer from https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt-get install tesseract-ocr`
- Mac: `brew install tesseract`

4. Run the application:
```bash
python app.py
```

## Project Structure

```
pdf_processor/
├── app.py                 # Main Flask application
├── requirements.txt       # Project dependencies
├── static/               # Static files (CSS, JS, etc.)
├── templates/            # HTML templates
└── utils/               # Utility functions
    ├── converter.py     # PDF conversion utilities
    ├── organizer.py     # PDF organization utilities
    ├── editor.py        # PDF editing utilities
    └── security.py      # PDF security utilities
```

## Features

1. PDF Conversion
   - Convert PDF to Word/Excel/PowerPoint
   - Convert Word/Excel/PowerPoint to PDF
   - Convert PDF to images
   - Convert images to PDF

2. PDF Organization
   - Merge multiple PDFs
   - Split PDF into multiple files
   - Rotate PDF pages
   - Delete/extract pages

3. PDF Editing
   - Add/edit text
   - Add watermarks
   - Add page numbers
   - Add annotations

4. Security
   - Encrypt PDF
   - Decrypt PDF
   - Add password protection 