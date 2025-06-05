from flask import Flask, render_template, request, send_file
import PyPDF2
import io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400
    
    if not file.filename.endswith('.pdf'):
        return 'Only PDF files are allowed', 400
    
    try:
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
        return str(e), 500

if __name__ == '__main__':
    app.run() 