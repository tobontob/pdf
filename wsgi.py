from flask import Flask, render_template, request, send_file, jsonify
import PyPDF2
import io
import os
import sys
import traceback

# 정적 파일과 템플릿 디렉토리 경로 설정
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'pdf_processor', 'static'))
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'pdf_processor', 'templates'))

app = Flask(__name__,
           static_folder=static_dir,
           template_folder=template_dir)

app.debug = True  # Vercel에서 디버그 정보를 볼 수 있도록 설정

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error rendering template: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'trace': traceback.format_exc(),
            'template_dir': template_dir,
            'static_dir': static_dir,
            'current_dir': os.getcwd(),
            'files': os.listdir(os.getcwd())
        }), 500

@app.route('/process', methods=['POST'])
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
        app.logger.error(f"Error processing file: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'trace': traceback.format_exc()
        }), 500

# 에러 핸들러 추가
@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal error: {str(error)}")
    app.logger.error(traceback.format_exc())
    return jsonify({
        'error': str(error),
        'trace': traceback.format_exc()
    }), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.route('/convert')
def convert():
    return render_template('convert.html')

@app.route('/edit')
def edit():
    return render_template('edit.html')

@app.route('/compress')
def compress():
    return render_template('compress.html')

@app.route('/ocr')
def ocr():
    return render_template('ocr.html')

if __name__ == '__main__':
    app.run() 