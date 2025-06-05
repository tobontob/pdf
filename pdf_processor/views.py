from flask import Blueprint, render_template, request, send_file, jsonify
import PyPDF2
import io
import os
import traceback

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return jsonify({
            'error': str(e),
            'trace': traceback.format_exc()
        }), 500

@main_bp.route('/convert')
def convert():
    return render_template('convert.html')

@main_bp.route('/edit')
def edit():
    return render_template('edit.html')

@main_bp.route('/organize')
def organize():
    return render_template('organize.html')

@main_bp.route('/compress')
def compress():
    return render_template('compress.html')

@main_bp.route('/ocr')
def ocr():
    return render_template('ocr.html')

@main_bp.route('/process', methods=['POST'])
def process_file():
    try:
        if 'file' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400
        
        if not file.filename.endswith('.pdf'):
            return 'Only PDF files are allowed', 400
        
        # 메모리에서 PDF 처리
        pdf_content = io.BytesIO(file.read())
        pdf_reader = PyPDF2.PdfReader(pdf_content)
        pdf_writer = PyPDF2.PdfWriter()
        
        # 모든 페이지 복사
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # 결과를 메모리에 저장
        output = io.BytesIO()
        pdf_writer.write(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='processed.pdf'
        )
    except Exception as e:
        return jsonify({
            'error': str(e),
            'trace': traceback.format_exc()
        }), 500 