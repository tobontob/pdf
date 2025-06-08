import os
import tempfile
import uuid
import win32com.client
import pythoncom
import time
from docx import Document
from pdf2docx import Converter

class DocumentConverter:
    def __init__(self):
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'pdf_converter')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        # Word 인스턴스 초기화
        self.word = None

    def init_word(self):
        """Word 객체 초기화"""
        if self.word is None:
            # COM 초기화
            pythoncom.CoInitialize()
            self.word = win32com.client.Dispatch("Word.Application")
            self.word.Visible = False
            self.word.DisplayAlerts = False

    def close_word(self):
        """Word 객체 종료"""
        try:
            if self.word:
                self.word.Quit()
                self.word = None
                pythoncom.CoUninitialize()
        except:
            pass

    def pdf_to_doc(self, pdf_path):
        """PDF를 Word 문서로 변환"""
        try:
            # 임시 파일 경로 생성
            output_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}_output.docx")
            
            # PDF를 Word로 변환
            cv = Converter(pdf_path)
            cv.convert(output_path)
            cv.close()
            
            return output_path
        except Exception as e:
            raise Exception(f"PDF to Word conversion failed: {str(e)}")

    def doc_to_pdf(self, doc_path):
        """Word 문서를 PDF로 변환"""
        try:
            # 임시 파일 경로 생성
            output_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}_output.pdf")
            
            # Word 초기화
            self.init_word()
            
            try:
                # 문서 열기
                doc = self.word.Documents.Open(os.path.abspath(doc_path))
                
                # PDF로 저장 (17 = PDF 형식)
                doc.SaveAs2(os.path.abspath(output_path), FileFormat=17)
                
                # 저장이 완료될 때까지 대기
                time.sleep(1)
                
                # 문서 닫기
                doc.Close()
                
                return output_path
            finally:
                self.close_word()
                
        except Exception as e:
            raise Exception(f"Word to PDF conversion failed: {str(e)}")

    def cleanup(self, *file_paths):
        """임시 파일 삭제"""
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"Error cleaning up file {path}: {e}")

    def __del__(self):
        """소멸자에서 Word 객체 정리"""
        self.close_word() 