from pdf_processor import create_app
import io
from flask import send_file

app = create_app()

# Vercel은 'app' 변수를 찾습니다
if __name__ == '__main__':
    app.run()  # debug=True 제거 

def process_file(file):
    # 메모리에서 파일 처리
    file_content = file.read()
    # 처리 로직
    result = process_in_memory(file_content)
    # 바로 응답으로 전송
    return send_file(
        io.BytesIO(result),
        as_attachment=True,
        download_name='processed.pdf'
    ) 