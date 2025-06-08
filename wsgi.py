from flask import Flask, render_template

# Flask 앱 생성
app = Flask(__name__,
           template_folder='templates',
           static_folder='static')

@app.route('/')
def index():
    return render_template('convert.html')

@app.route('/convert')
def convert():
    return render_template('convert.html')

if __name__ == '__main__':
    app.run(debug=True) 