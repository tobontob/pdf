import os
import tempfile
import uuid
import win32com.client
import tabula
import pandas as pd
import time

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
        try:
            # 임시 파일 경로 생성
            output_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}_output.xlsx")
            
            if detect_tables:
                # tabula-py를 사용하여 PDF에서 표 추출
                tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
                
                # 여러 시트에 표 저장
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    for i, table in enumerate(tables):
                        sheet_name = f'Table {i+1}' if len(tables) > 1 else 'Sheet1'
                        table.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                # 단순 텍스트 추출 및 저장
                tables = tabula.read_pdf(pdf_path, pages='all', stream=True)
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    for i, table in enumerate(tables):
                        sheet_name = f'Page {i+1}'
                        table.to_excel(writer, sheet_name=sheet_name, index=False)
            
            if preserve_formatting:
                # Excel을 사용하여 서식 개선
                self.init_excel()
                workbook = self.excel.Workbooks.Open(output_path)
                
                for sheet in workbook.Sheets:
                    sheet.Columns.AutoFit()
                    sheet.Rows.AutoFit()
                
                workbook.Save()
                workbook.Close()
            
            return output_path
        except Exception as e:
            raise Exception(f"PDF to Excel conversion failed: {str(e)}")
        finally:
            self.close_excel()

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
        """임시 파일 삭제"""
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"Error cleaning up file {path}: {e}")

    def __del__(self):
        """소멸자에서 Excel 객체 정리"""
        self.close_excel() 