from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
import os
import tempfile
from werkzeug.utils import secure_filename
import uuid
import shutil
import pdfkit
import base64
import json
import time
import sys
import platform

# Flask 앱 생성
app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = 'your-secret-key-here'  # 실제 운영 환경에서는 안전한 시크릿 키로 변경하세요

# 임시 파일 저장 경로
TEMP_DIR = os.path.join(tempfile.gettempdir(), 'pdf_converter')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR, exist_ok=True)

# PDF 변환 옵션
PDF_OPTIONS = {
    'page-size': 'A4',
    'margin-top': '10mm',
    'margin-right': '10mm',
    'margin-bottom': '10mm',
    'margin-left': '10mm',
    'encoding': 'UTF-8',
    'no-outline': None,
    'quiet': ''
}

# HTML을 PDF로 변환하는 함수
def html_to_pdf(html_content, options=None):
    if options is None:
        options = {}
    
    try:
        # 고유한 파일명 생성
        output_filename = os.path.join(TEMP_DIR, f"output_{uuid.uuid4().hex}.pdf")
        
        # PDF 생성
        pdfkit.from_string(
            input=html_content,
            output_path=output_filename,
            options=options,
            verbose=True
        )
        
        return output_filename
        
    except Exception as e:
        print(f"Error in html_to_pdf: {str(e)}", file=sys.stderr)
        raise

# HTML을 PDF로 변환하는 엔드포인트
@app.route('/api/convert/html', methods=['POST'])
def convert_html_to_pdf():
    if 'file' not in request.files and 'html' not in request.form:
        return jsonify({"error": "No file or HTML content provided"}), 400
    
    try:
        if 'file' in request.files and request.files['file'].filename != '':
            # 파일 업로드 처리
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No selected file"}), 400
                
            html_content = file.read().decode('utf-8')
        else:
            # 텍스트 에디터에서 온 HTML 내용 처리
            html_content = request.form.get('html', '')
        
        # PDF 옵션 설정
        options = PDF_OPTIONS.copy()
        options.update({
            'page-size': request.form.get('page_size', 'A4'),
            'orientation': request.form.get('orientation', 'portrait'),
        })
        
        # PDF 생성
        output_pdf = html_to_pdf(html_content, options)
        
        # 생성된 PDF 파일 전송
        return send_file(
            output_pdf,
            as_attachment=True,
            download_name='converted.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # 임시 파일 정리
        if 'output_pdf' in locals() and os.path.exists(output_pdf):
            try:
                os.remove(output_pdf)
            except:
                pass

# 라우트 정의
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert')
def convert():
    return render_template('convert.html')

@app.route('/document')
def document():
    return render_template('document.html')

@app.route('/excel')
def excel():
    return render_template('excel.html')

@app.route('/html')
def html():
    return render_template('html.html')

@app.route('/hwp')
def hwp():
    return render_template('hwp.html')

@app.route('/image')
def image():
    return render_template('image.html')

@app.route('/powerpoint')
def powerpoint():
    return render_template('powerpoint.html')

@app.route('/secret')
def secret():
    return render_template('secret.html')

@app.route('/html-converter')
def html_converter_page():
    return render_template('html_converter.html')

# 정적 파일 서빙을 위한 라우트
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# PDF to Word 변환 엔드포인트
@app.route('/api/convert/pdf-to-docx', methods=['POST'])
def convert_pdf_to_docx():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        # 임시 파일 저장
        unique_id = str(uuid.uuid4())
        pdf_path = os.path.join(TEMP_DIR, f"{unique_id}_input.pdf")
        docx_path = os.path.join(TEMP_DIR, f"{unique_id}_output.docx")
        
        file.save(pdf_path)
        
        # PDF를 DOCX로 변환
        from pdf2docx import Converter
        cv = Converter(pdf_path)
        cv.convert(docx_path)
        cv.close()
        
        return send_file(
            docx_path,
            as_attachment=True,
            download_name=os.path.splitext(file.filename)[0] + '.docx',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # 임시 파일 정리
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.remove(pdf_path)
        if 'docx_path' in locals() and os.path.exists(docx_path):
            os.remove(docx_path)

if __name__ == '__main__':
    # 정적 파일 디렉토리가 없으면 생성
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    # 로컬 개발 환경에서만 디버그 모드로 실행
    app.run(debug=True, host='0.0.0.0', port=5000)