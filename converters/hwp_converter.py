import os
import tempfile
import uuid
import subprocess
from pathlib import Path
import olefile
import re
from bs4 import BeautifulSoup
import pdfkit

class HwpConverter:
    def __init__(self):
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'pdf_converter')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def extract_text_from_hwp(self, hwp_path):
        """HWP 파일에서 텍스트 추출"""
        try:
            f = olefile.OleFileIO(hwp_path)
            dirs = f.listdir()

            # HWP 파일 내부의 "BodyText" 스트림 찾기
            bodytext = []
            for dir in dirs:
                if 'bodytext' in dir[0].lower():
                    body_stream = f.openstream(dir)
                    data = body_stream.read()
                    bodytext.append(data)
                    
            # 텍스트 추출 및 정리
            text = []
            for data in bodytext:
                # 한글 문자 찾기 (유니코드 범위: AC00-D7AF)
                found = re.findall(b'[\xac-\xd7][\x00-\xff]', data)
                for ch in found:
                    try:
                        text.append(ch.decode('utf-16'))
                    except:
                        continue

            return ''.join(text)
            
        finally:
            f.close()

    def create_html(self, text):
        """추출된 텍스트로 HTML 생성"""
        soup = BeautifulSoup('<html><head><meta charset="utf-8"></head><body></body></html>', 'html.parser')
        
        # 스타일 추가
        style = soup.new_tag('style')
        style.string = '''
            body { 
                font-family: 'Malgun Gothic', sans-serif;
                line-height: 1.6;
                margin: 2cm;
            }
            p { 
                margin-bottom: 1em; 
            }
        '''
        soup.head.append(style)
        
        # 텍스트를 단락으로 분할하여 추가
        for paragraph in text.split('\n'):
            if paragraph.strip():
                p = soup.new_tag('p')
                p.string = paragraph.strip()
                soup.body.append(p)
        
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
                'margin-top': '0mm',
                'margin-right': '0mm',
                'margin-bottom': '0mm',
                'margin-left': '0mm',
                'encoding': 'UTF-8'
            }
            
            pdfkit.from_file(html_path, output_path, options=options)
            
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