from flask import Flask, render_template, request, send_file, jsonify
import PyPDF2
import io
import os

# Flask 앱 생성
app = Flask(__name__,
           template_folder=os.path.join('pdf_processor', 'templates'),
           static_folder=os.path.join('pdf_processor', 'static'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert')
def convert():
    return render_template('convert.html')

@app.route('/edit')
def edit():
    return render_template('edit.html')

@app.route('/organize')
def organize():
    return render_template('organize.html')

@app.route('/compress')
def compress():
    return render_template('compress.html')

@app.route('/ocr')
def ocr():
    return render_template('ocr.html')

@app.route('/process', methods=['POST'])
def process_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
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
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run() 