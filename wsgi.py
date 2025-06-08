from flask import Flask, render_template, send_from_directory
import os

# Flask 앱 생성
app = Flask(__name__,
           template_folder='templates',
           static_folder='static')

# 시크릿 키 설정
app.secret_key = 'your-secret-key-here'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert')
def convert():
    return render_template('convert.html')

if __name__ == '__main__':
    app.run(debug=True) 