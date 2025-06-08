import os
import tempfile
import uuid
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup
import pdfkit

class HwpConverter:
    def __init__(self):
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'pdf_converter')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            
        # wkhtmltopdf 설정
        self.wkhtmltopdf_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        self.pdf_config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)

    def extract_text_from_hwp(self, hwp_path):
        """HWP 파일에서 텍스트 추출"""
        try:
            # 임시 텍스트 파일 경로
            text_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}_output.txt")
            
            # hwp5txt 명령어 실행
            subprocess.run(['hwp5txt', '--output', text_path, hwp_path], check=True)
            
            # 텍스트 파일 읽기
            with open(text_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            # 임시 파일 삭제
            os.remove(text_path)
            
            return text
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"HWP 파일 변환 오류: {str(e)}")
        except Exception as e:
            raise Exception(f"텍스트 추출 오류: {str(e)}")

    def create_html(self, text):
        """추출된 텍스트로 HTML 생성"""
        soup = BeautifulSoup('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>변환된 문서</title>
        </head>
        <body></body>
        </html>
        ''', 'html.parser')
        
        # 스타일 추가
        style = soup.new_tag('style')
        style.string = '''
            @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap');
            body { 
                font-family: 'Nanum Gothic', 'Malgun Gothic', sans-serif;
                line-height: 1.8;
                margin: 2cm;
                word-break: keep-all;
                overflow-wrap: break-word;
                font-size: 11pt;
            }
            p { 
                margin: 0;
                padding: 0.5em 0;
                text-align: justify;
            }
            .page-break {
                page-break-after: always;
            }
        '''
        soup.head.append(style)
        
        # 텍스트를 단락으로 분할하여 추가
        paragraphs = text.split('\n')
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                p = soup.new_tag('p')
                p.string = paragraph.strip()
                soup.body.append(p)
                
                # 빈 줄이 연속으로 나오면 페이지 나누기 추가
                if i < len(paragraphs) - 1 and not paragraphs[i+1].strip():
                    div = soup.new_tag('div')
                    div['class'] = 'page-break'
                    soup.body.append(div)
        
        return str(soup)

    def hwp_to_pdf(self, hwp_path):
        """HWP를 PDF로 변환"""
        try:
            # 임시 파일 경로 생성
            temp_dir = os.path.join(self.temp_dir, str(uuid.uuid4()))
            os.makedirs(temp_dir, exist_ok=True)
            
            # HWP에서 텍스트 추출
            text = self.extract_text_from_hwp(hwp_path)
            
            # HTML 생성
            html_content = self.create_html(text)
            html_path = os.path.join(temp_dir, 'output.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # PDF 생성
            output_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}_output.pdf")
            options = {
                'page-size': 'A4',
                'margin-top': '20mm',
                'margin-right': '20mm',
                'margin-bottom': '20mm',
                'margin-left': '20mm',
                'encoding': 'UTF-8',
                'no-outline': None,
                'enable-local-file-access': None,
                'disable-smart-shrinking': None,
                'dpi': 300,
                'image-dpi': 300
            }
            
            pdfkit.from_file(html_path, output_path, options=options, configuration=self.pdf_config)
            
            return output_path
            
        except Exception as e:
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
            raise Exception(f"HWP to PDF conversion failed: {str(e)}")

    def cleanup(self, *file_paths):
        """임시 파일 삭제"""
        for path in file_paths:
            try:
                if os.path.exists(path):
                    if os.path.isdir(path):
                        import shutil
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
            except Exception as e:
                print(f"Error cleaning up file {path}: {e}") 