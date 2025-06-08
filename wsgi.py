from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for, send_from_directory
import PyPDF2
import io
import os
from werkzeug.utils import secure_filename
from pdf2docx import Converter
from docx2pdf import convert as docx2pdf
from pdf2image import convert_from_path
from PIL import Image

# Poppler 경로 설정 (Windows)
POPPLER_PATH = r"C:\Program Files\poppler\Library\bin"
if os.path.exists(POPPLER_PATH):
    os.environ["PATH"] += os.pathsep + POPPLER_PATH

# Flask 앱 생성
app = Flask(__name__,
           template_folder='templates',
           static_folder='static')

# 시크릿 키 설정
app.secret_key = 'your-secret-key-here'  # 실제 운영환경에서는 환경변수로 관리해야 합니다

# 업로드 폴더 설정
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
PROCESSED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'processed')

# 업로드 폴더가 없으면 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 최대 16MB 파일 크기 제한

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert')
def convert():
    return render_template('convert.html')

@app.route('/convert-from-pdf', methods=['POST'])
def convert_from_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'PDF 파일이 업로드되지 않았습니다'
        }), 400
    
    file = request.files['pdf_file']
    output_format = request.form.get('output_format')
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': '파일이 선택되지 않았습니다'
        }), 400
    
    if not output_format:
        return jsonify({
            'success': False,
            'message': '변환 형식이 지정되지 않았습니다'
        }), 400
    
    try:
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        output_filename = os.path.splitext(filename)[0]
        if output_format == 'docx':
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], f"{output_filename}.docx")
            cv = Converter(input_path)
            cv.convert(output_path)
            cv.close()
        elif output_format in ['jpg', 'png']:
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], f"{output_filename}.{output_format}")
            images = convert_from_path(input_path, poppler_path=POPPLER_PATH)
            if len(images) == 1:
                images[0].save(output_path, output_format.upper())
            else:
                base_path = os.path.splitext(output_path)[0]
                for i, image in enumerate(images):
                    image.save(f"{base_path}_{i+1}.{output_format}", output_format.upper())
        else:
            return jsonify({
                'success': False,
                'message': '지원하지 않는 변환 형식입니다'
            }), 400
        
        return jsonify({
            'success': True,
            'message': '파일 변환이 완료되었습니다',
            'download_url': url_for('download_file', filename=os.path.basename(output_path))
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'파일 처리 중 오류가 발생했습니다: {str(e)}'
        }), 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@app.route('/convert-to-pdf', methods=['POST'])
def convert_to_pdf():
    if 'input_file' not in request.files:
        return jsonify({
            'success': False,
            'message': '파일이 업로드되지 않았습니다'
        }), 400
    
    file = request.files['input_file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': '파일이 선택되지 않았습니다'
        }), 400
    
    try:
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        output_filename = f"{os.path.splitext(filename)[0]}.pdf"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.doc', '.docx']:
            docx2pdf(input_path, output_path)
        elif ext in ['.jpg', '.jpeg', '.png']:
            image = Image.open(input_path)
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            image.save(output_path, 'PDF')
        else:
            return jsonify({
                'success': False,
                'message': '지원하지 않는 파일 형식입니다'
            }), 400
        
        return jsonify({
            'success': True,
            'message': '파일 변환이 완료되었습니다',
            'download_url': url_for('download_file', filename=output_filename)
        })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'파일 처리 중 오류가 발생했습니다: {str(e)}'
        }), 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True) 