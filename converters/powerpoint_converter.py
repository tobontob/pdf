import os
import tempfile
import uuid
import win32com.client
import fitz
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
import time

class PowerPointConverter:
    def __init__(self):
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'pdf_converter')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        # PowerPoint 인스턴스 초기화
        self.powerpoint = None

    def init_powerpoint(self):
        """PowerPoint 객체 초기화"""
        if self.powerpoint is None:
            self.powerpoint = win32com.client.Dispatch("PowerPoint.Application")
            self.powerpoint.Visible = False

    def close_powerpoint(self):
        """PowerPoint 객체 종료"""
        try:
            if self.powerpoint:
                self.powerpoint.Quit()
                self.powerpoint = None
        except:
            pass

    def pdf_to_ppt(self, pdf_path, extract_images=True, preserve_layout=True, create_animations=False):
        """PDF를 PowerPoint 프레젠테이션으로 변환"""
        try:
            # 임시 파일 경로 생성
            output_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}_output.pptx")
            images_dir = os.path.join(self.temp_dir, str(uuid.uuid4()))
            os.makedirs(images_dir, exist_ok=True)

            # PDF 문서 열기
            pdf_doc = fitz.open(pdf_path)
            
            # 새 프레젠테이션 생성
            prs = Presentation()
            
            # 16:9 슬라이드 크기 설정
            prs.slide_width = Inches(16)
            prs.slide_height = Inches(9)

            for page_num in range(len(pdf_doc)):
                # 새 슬라이드 추가
                slide = prs.slides.add_slide(prs.slide_layouts[6])  # 빈 레이아웃
                
                if extract_images:
                    # 페이지에서 이미지 추출
                    page = pdf_doc[page_num]
                    image_list = page.get_images()
                    
                    for img_idx, img_info in enumerate(image_list):
                        xref = img_info[0]
                        base_image = pdf_doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # 이미지 저장
                        image_path = os.path.join(images_dir, f'image_{page_num}_{img_idx}.png')
                        with open(image_path, 'wb') as img_file:
                            img_file.write(image_bytes)
                        
                        # 이미지를 슬라이드에 추가
                        if preserve_layout:
                            # 원본 위치 정보 사용
                            rect = page.get_image_bbox(img_info)
                            left = Inches(rect.x0 * 16 / page.rect.width)
                            top = Inches(rect.y0 * 9 / page.rect.height)
                            width = Inches((rect.x1 - rect.x0) * 16 / page.rect.width)
                            height = Inches((rect.y1 - rect.y0) * 9 / page.rect.height)
                        else:
                            # 기본 위치 사용
                            left = Inches(1)
                            top = Inches(1)
                            width = Inches(8)
                            height = Inches(6)
                        
                        slide.shapes.add_picture(image_path, left, top, width, height)

                # 텍스트 추출 및 추가
                page = pdf_doc[page_num]
                text_blocks = page.get_text("blocks")
                
                for block in text_blocks:
                    if preserve_layout:
                        # 원본 위치 정보 사용
                        left = Inches(block[0] * 16 / page.rect.width)
                        top = Inches(block[1] * 9 / page.rect.height)
                        width = Inches((block[2] - block[0]) * 16 / page.rect.width)
                        height = Inches((block[3] - block[1]) * 9 / page.rect.height)
                    else:
                        # 기본 위치 사용
                        left = Inches(1)
                        top = Inches(1)
                        width = Inches(8)
                        height = Inches(6)
                    
                    textbox = slide.shapes.add_textbox(left, top, width, height)
                    textbox.text = block[4]
                
                if create_animations:
                    # 간단한 애니메이션 효과 추가
                    for shape in slide.shapes:
                        if hasattr(shape, 'animation_settings'):
                            shape.animation_settings.entrance_effect_type = 1  # 페이드 인

            # 프레젠테이션 저장
            prs.save(output_path)
            
            return output_path
        except Exception as e:
            raise Exception(f"PDF to PowerPoint conversion failed: {str(e)}")
        finally:
            # 임시 이미지 파일 삭제
            if os.path.exists(images_dir):
                for file in os.listdir(images_dir):
                    os.remove(os.path.join(images_dir, file))
                os.rmdir(images_dir)

    def ppt_to_pdf(self, ppt_path):
        """PowerPoint 프레젠테이션을 PDF로 변환"""
        try:
            # 임시 파일 경로 생성
            output_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}_output.pdf")
            
            # PowerPoint 초기화
            self.init_powerpoint()
            
            # 프레젠테이션 열기
            presentation = self.powerpoint.Presentations.Open(ppt_path)
            
            # PDF로 저장
            presentation.SaveAs(output_path, 32)  # 32 = PDF 형식
            
            # 저장이 완료될 때까지 대기
            time.sleep(1)
            
            presentation.Close()
            
            return output_path
        except Exception as e:
            raise Exception(f"PowerPoint to PDF conversion failed: {str(e)}")
        finally:
            self.close_powerpoint()

    def cleanup(self, *file_paths):
        """임시 파일 삭제"""
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"Error cleaning up file {path}: {e}")

    def __del__(self):
        """소멸자에서 PowerPoint 객체 정리"""
        self.close_powerpoint() 