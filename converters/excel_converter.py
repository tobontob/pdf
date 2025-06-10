import os
import tempfile
import uuid
import win32com.client
import pandas as pd
import time
from pdf2docx import Converter
from docx import Document

class ExcelConverter:
    def __init__(self):
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'pdf_converter')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        # Excel 인스턴스 초기화
        self.excel = None

    def init_excel(self):
        """Excel 객체 초기화"""
        if self.excel is None:
            self.excel = win32com.client.Dispatch("Excel.Application")
            self.excel.Visible = False
            self.excel.DisplayAlerts = False

    def close_excel(self):
        """Excel 객체 종료"""
        try:
            if self.excel:
                self.excel.Quit()
                self.excel = None
        except:
            pass

    def pdf_to_excel(self, pdf_path, preserve_formatting=True, detect_tables=True):
        """PDF를 Excel 문서로 변환"""
        temp_docx = None
        try:
            # 임시 파일 경로 생성
            output_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}_output.xlsx")
            temp_docx = os.path.join(self.temp_dir, f"{uuid.uuid4()}_temp.docx")
            
            # PDF를 DOCX로 변환
            cv = Converter(pdf_path)
            cv.convert(temp_docx, start=0, end=None)
            cv.close()
            
            # DOCX에서 텍스트 추출
            doc = Document(temp_docx)
            
            # DataFrame 생성
            data = []
            for para in doc.paragraphs:
                if para.text.strip():
                    data.append([para.text])
            
            # DataFrame을 Excel로 저장
            df = pd.DataFrame(data, columns=['Text'])
            df.to_excel(output_path, index=False, engine='openpyxl')
            
            # 파일이 제대로 생성되었는지 확인
            if not os.path.exists(output_path):
                raise Exception("Failed to generate Excel file")
                
            return output_path
            
        except Exception as e:
            raise Exception(f"PDF to Excel conversion failed: {str(e)}")
        finally:
            self.close_excel()
            # 임시 파일 정리
            if temp_docx and os.path.exists(temp_docx):
                try:
                    os.unlink(temp_docx)
                except:
                    pass

    def excel_to_pdf(self, excel_path):
        """Excel 문서를 PDF로 변환"""
        try:
            # 임시 파일 경로 생성
            output_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}_output.pdf")
            
            # Excel 초기화
            self.init_excel()
            
            # Excel 파일 열기
            workbook = self.excel.Workbooks.Open(excel_path)
            
            # PDF로 저장
            workbook.ExportAsFixedFormat(0, output_path)  # 0 = PDF 형식
            
            # 저장이 완료될 때까지 대기
            time.sleep(1)
            
            workbook.Close()
            
            return output_path
        except Exception as e:
            raise Exception(f"Excel to PDF conversion failed: {str(e)}")
        finally:
            self.close_excel()

    def cleanup(self, *file_paths):
        """임시 파일 정리"""
        for file_path in file_paths:
            try:
                if file_path and os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {str(e)}")
                continue

    def __del__(self):
        """소멸자에서 Excel 객체 정리"""
        self.close_excel()