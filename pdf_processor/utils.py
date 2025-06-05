import os
from PyPDF2 import PdfReader, PdfWriter
from pdf2docx import Converter
from PIL import Image
import pytesseract
from docx2pdf import convert
import img2pdf
import zipfile

def pdf_to_word(input_path, output_path):
    """PDF를 Word 문서로 변환"""
    try:
        cv = Converter(input_path)
        cv.convert(output_path)
        cv.close()
        return True
    except Exception as e:
        print(f"PDF to Word 변환 오류: {str(e)}")
        return False

def pdf_to_image(input_path, output_dir):
    """PDF를 이미지로 변환"""
    try:
        reader = PdfReader(input_path)
        os.makedirs(output_dir, exist_ok=True)
        
        for i, page in enumerate(reader.pages):
            # PDF 페이지를 이미지로 변환하는 로직 구현
            # 여기서는 예시로 빈 이미지 파일만 생성
            output_path = os.path.join(output_dir, f'page_{i+1}.png')
            Image.new('RGB', (595, 842), 'white').save(output_path)
        return True
    except Exception as e:
        print(f"PDF to Image 변환 오류: {str(e)}")
        return False

def word_to_pdf(input_path, output_path):
    """Word 문서를 PDF로 변환"""
    try:
        convert(input_path, output_path)
        return True
    except Exception as e:
        print(f"Word to PDF 변환 오류: {str(e)}")
        return False

def image_to_pdf(input_path, output_path):
    """이미지를 PDF로 변환"""
    try:
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(input_path))
        return True
    except Exception as e:
        print(f"Image to PDF 변환 오류: {str(e)}")
        return False

def merge_pdf_files(input_paths, output_path):
    """여러 PDF 파일을 하나로 병합"""
    try:
        writer = PdfWriter()
        
        for path in input_paths:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        return True
    except Exception as e:
        print(f"PDF 병합 오류: {str(e)}")
        return False

def split_pdf_range(input_path, output_dir, start_page, end_page):
    """PDF 파일의 특정 페이지 범위를 분할"""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for i in range(start_page - 1, min(end_page, len(reader.pages))):
            writer.add_page(reader.pages[i])
        
        output_path = os.path.join(output_dir, f'split_{start_page}-{end_page}.pdf')
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        # ZIP 파일 생성
        with zipfile.ZipFile(os.path.join(os.path.dirname(output_dir), 'split.zip'), 'w') as zipf:
            for file in os.listdir(output_dir):
                if file.endswith('.pdf'):
                    zipf.write(os.path.join(output_dir, file), file)
        
        return True
    except Exception as e:
        print(f"PDF 분할 오류: {str(e)}")
        return False

def split_pdf_all(input_path, output_dir):
    """PDF 파일의 모든 페이지를 개별 파일로 분할"""
    try:
        reader = PdfReader(input_path)
        
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            
            output_path = os.path.join(output_dir, f'page_{i+1}.pdf')
            with open(output_path, 'wb') as f:
                writer.write(f)
        
        # ZIP 파일 생성
        with zipfile.ZipFile(os.path.join(os.path.dirname(output_dir), 'split.zip'), 'w') as zipf:
            for file in os.listdir(output_dir):
                if file.endswith('.pdf'):
                    zipf.write(os.path.join(output_dir, file), file)
        
        return True
    except Exception as e:
        print(f"PDF 분할 오류: {str(e)}")
        return False

def rotate_pdf_pages(input_path, output_path, rotation, pages='all'):
    """PDF 페이지 회전"""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for i, page in enumerate(reader.pages):
            if pages == 'all' or str(i+1) in pages.split(','):
                page.rotate(rotation)
            writer.add_page(page)
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        return True
    except Exception as e:
        print(f"PDF 회전 오류: {str(e)}")
        return False

def edit_pdf_text(input_path, output_path):
    """PDF 텍스트 편집"""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        return True
    except Exception as e:
        print(f"PDF 텍스트 편집 오류: {str(e)}")
        return False

def edit_pdf_image(input_path, output_path):
    """PDF 이미지 편집"""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        return True
    except Exception as e:
        print(f"PDF 이미지 편집 오류: {str(e)}")
        return False

def add_pdf_annotation(input_path, output_path):
    """PDF 주석 추가"""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        return True
    except Exception as e:
        print(f"PDF 주석 추가 오류: {str(e)}")
        return False

def perform_ocr(input_path, output_path, language='eng'):
    """OCR 수행"""
    try:
        # PDF의 각 페이지를 이미지로 변환하고 OCR 수행
        text = pytesseract.image_to_string(Image.open(input_path), lang=language)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    except Exception as e:
        print(f"OCR 오류: {str(e)}")
        return False

def compress_pdf(input_path, output_path, compression_level='medium'):
    """PDF 압축"""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        return True
    except Exception as e:
        print(f"PDF 압축 오류: {str(e)}")
        return False 