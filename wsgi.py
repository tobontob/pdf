from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
import os
import tempfile
from werkzeug.utils import secure_filename
import uuid
import shutil
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
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

# HTML을 PDF로 변환하는 함수
def html_to_pdf(html_content, options=None):
    if options is None:
        options = {}
    
    # 고유한 파일명 생성
    output_filename = f"converted_{uuid.uuid4().hex}.pdf"
    output_path = os.path.join(TEMP_DIR, output_filename)
    
    try:
        # WeasyPrint 스타일 설정
        styles = """
            @page {
                size: %s %s;
                margin: 20mm;
            }
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
            }
            img {
                max-width: 100%%;
                height: auto;
            }
        """ % (
            options.get('pageSize', 'A4'),
            options.get('orientation', 'portrait')
        )
        
        if not options.get('includeBackground', True):
            styles += """
                @page {
                    background: white !important;
                }
                body {
                    background: white !important;
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                }
            """
        
        # WeasyPrint로 HTML을 PDF로 변환
        if isinstance(html_content, bytes):
            html_content = html_content.decode('utf-8')
            
        # Base64 이미지 처리
        if ';base64,' in html_content:
            # base64 이미지 처리 로직 (필요시 구현)
            pass
            
        # CSS 적용
        css = CSS(string=styles)
        
        # HTML 변환
        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[css]
        )
        
        return output_path
        
    except Exception as e:
        print(f"HTML을 PDF로 변환하는 중 오류 발생: {str(e)}")
        raise

# HTML을 PDF로 변환하는 엔드포인트
@app.route('/convert/html-to-pdf', methods=['POST'])
def convert_html_to_pdf():
    try:
        if 'content' not in request.form and 'file' not in request.files:
            return jsonify({'error': '변환할 콘텐츠가 없습니다.'}), 400
            
        content = request.form.get('content', '')
        options = request.form.get('options')
        
        if options:
            try:
                options = json.loads(options)
            except json.JSONDecodeError:
                options = {}
        else:
            options = {}
        
        # 파일 업로드 처리
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                content = file.read().decode('utf-8')
        
        if not content:
            return jsonify({'error': '변환할 콘텐츠가 비어 있습니다.'}), 400
        
        # HTML을 PDF로 변환
        pdf_path = html_to_pdf(content, options)
        
        # 변환된 PDF 파일 전송
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"converted_{int(time.time())}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # 임시 파일 정리
        try:
            if 'pdf_path' in locals() and os.path.exists(pdf_path):
                os.remove(pdf_path)
        except Exception as e:
            print(f"임시 파일 삭제 중 오류: {e}")

# 라우트 정의
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/html')
def html_converter_page():
    return render_template('html.html')

@app.route('/secret')
def secret_page():
    return render_template('secret.html')

# Vercel 호환을 위한 핸들러
def vercel_handler(event, context):
    with app.app_context():
        response = app.full_dispatch_request()
        return {
            'statusCode': response.status_code,
            'headers': dict(response.headers),
            'body': response.get_data(as_text=True)
        }

if __name__ == '__main__':
    app.run(debug=True)