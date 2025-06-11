import os
import uuid
import tempfile
import shutil
import olefile
from pdf2docx import Converter
import win32com.client
import pythoncom

class HWPConverter:
    def __init__(self):
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'hwp_converter')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)
        
        self.hwp = None
        self.com_initialized = False

    def init_hwp(self):
        """한글 오피스 초기화"""
        if self.hwp is None:
            try:
                pythoncom.CoInitialize()
                self.com_initialized = True
                self.hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
                self.hwp.XHwpWindows.Item(0).Visible = False
            except Exception as e:
                if self.com_initialized:
                    pythoncom.CoUninitialize()
                    self.com_initialized = False
                raise Exception(f"한글 오피스를 초기화할 수 없습니다: {str(e)}")

    def close_hwp(self):
        """한글 오피스 종료"""
        try:
            if self.hwp:
                self.hwp.Quit()
                self.hwp = None
        except Exception as e:
            print(f"한글 오피스 종료 중 오류: {str(e)}")
        finally:
            if self.com_initialized:
                pythoncom.CoUninitialize()
                self.com_initialized = False

    def pdf_to_hwp(self, pdf_path):
        """PDF를 HWP로 변환"""
        temp_docx = None
        output_path = None
        
        try:
            # 1. PDF를 DOCX로 변환
            temp_docx = os.path.join(self.temp_dir, f"{uuid.uuid4()}.docx")
            output_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}.hwp")
            
            # PDF를 DOCX로 변환
            cv = Converter(pdf_path)
            cv.convert(temp_docx)
            cv.close()
            
            # 2. DOCX를 HWP로 변환
            self.init_hwp()
            
            # 새 문서 생성
            self.hwp.CreateAction()
            self.hwp.Open(os.path.abspath(temp_docx))
            
            # HWP로 저장
            self.hwp.SaveAs(os.path.abspath(output_path), "HWP")
            
            if not os.path.exists(output_path):
                raise Exception("HWP 파일 생성에 실패했습니다.")
                
            return output_path
            
        except Exception as e:
            if output_path and os.path.exists(output_path):
                try:
                    os.unlink(output_path)
                except:
                    pass
            raise Exception(f"PDF를 HWP로 변환하는 중 오류가 발생했습니다: {str(e)}")
            
        finally:
            self.close_hwp()
            if temp_docx and os.path.exists(temp_docx):
                try:
                    os.unlink(temp_docx)
                except:
                    pass

    def hwp_to_text(self, hwp_path):
        """HWP 파일에서 텍스트 추출"""
        try:
            # HWP 파일인지 확인
            if not olefile.isOleFile(hwp_path):
                raise ValueError("올바른 HWP 파일이 아닙니다.")
                
            # HWP 파일 열기
            ole = olefile.OleFileIO(hwp_path)
            
            # HWP 파일에서 텍스트 추출 시도
            try:
                # HWP 파일 내부 구조에서 텍스트 추출
                encoded_text = ole.openstream('PrvText').read()
                text = encoded_text.decode('utf-16le', errors='ignore')
                return text.strip()
            except:
                # PrvText가 없는 경우 다른 방법으로 시도
                try:
                    # HWP 파일 내부의 Section0에서 텍스트 추출 시도
                    encoded_text = ole.openstream('BodyText/Section0').read()
                    # HWP 바이너리 형식에 따라 디코딩이 필요할 수 있음
                    # 여기서는 간단히 시도만 해보고, 정확한 파싱이 필요하면 추가 구현이 필요
                    text = encoded_text.decode('utf-8', errors='ignore')
                    return text.strip()
                except Exception as e:
                    raise Exception("HWP 파일에서 텍스트를 추출할 수 없습니다. 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다.")
            
        except Exception as e:
            raise Exception(f"HWP 파일 처리 중 오류가 발생했습니다: {str(e)}")
            
        finally:
            try:
                ole.close()
            except:
                pass

    def cleanup(self):
        """임시 파일 정리"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"임시 파일 정리 중 오류: {str(e)}")

    def __del__(self):
        """소멸자에서 리소스 정리"""
        self.close_hwp()
        self.cleanup()
