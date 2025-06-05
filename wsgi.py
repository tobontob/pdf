from pdf_processor import create_app

app = create_app()

# Vercel은 'app' 변수를 찾습니다
if __name__ == '__main__':
    app.run()  # debug=True 제거 