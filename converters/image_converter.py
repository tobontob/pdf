import os
import tempfile
from PIL import Image
import fitz  # PyMuPDF
import uuid

class ImageConverter:
    def __init__(self):
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'pdf_converter')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def pdf_to_image(self, pdf_path, format='jpg', dpi=300):
        """PDF를 이미지로 변환"""
        try:
            # 임시 파일 경로 생성
            output_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}_output.{format}")
            
            # PDF 열기
            pdf_document = fitz.open(pdf_path)
            
            # 첫 페이지 가져오기
            page = pdf_document[0]
            
            # 해상도 설정
            zoom = dpi / 72  # PDF 기본 DPI는 72
            matrix = fitz.Matrix(zoom, zoom)
            
            # 페이지를 이미지로 변환
            pix = page.get_pixmap(matrix=matrix)
            
            # 이미지 저장
            pix.save(output_path)
            
            return output_path
        except Exception as e:
            raise Exception(f"PDF to Image conversion failed: {str(e)}")

    def image_to_pdf(self, image_path):
        """이미지를 PDF로 변환"""
        try:
            # 임시 파일 경로 생성
            output_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}_output.pdf")
            
            # 이미지 열기
            image = Image.open(image_path)
            
            # RGBA 이미지를 RGB로 변환 (PDF는 RGBA를 지원하지 않음)
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            
            # PDF로 저장
            image.save(output_path, 'PDF', resolution=300.0)
            
            return output_path
        except Exception as e:
            raise Exception(f"Image to PDF conversion failed: {str(e)}")

    def cleanup(self, *file_paths):
        """임시 파일 삭제"""
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"Error cleaning up file {path}: {e}") 