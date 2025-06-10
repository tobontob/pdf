from flask import Flask, render_template, request, send_file, jsonify, send_from_directory
import os
import tempfile
from werkzeug.utils import secure_filename
from pdf2docx import Converter
from pathlib import Path
import uuid
import sys
import shutil
from io import BytesIO, StringIO
import subprocess
from fpdf import FPDF
import olefile
import zlib
import struct

def extract_text_from_hwp(hwp_path):
    """Extract text from HWP file using olefile"""
    try:
        # Open the HWP file using olefile
        ole = olefile.OleFileIO(hwp_path)
        
        # Get the "FileHeader" stream
        if ole.exists('FileHeader'):
            header = ole.openstream('FileHeader').read()
            # Check if this is a valid HWP file
            if header[36:40] == b'HWP ':
                # Get the body text sections
                text = ''
                for entry in ole.listdir():
                    # Look for body text sections (starts with 'BodyText')
                    if entry[0].startswith('BodyText'):
                        stream = ole.openstream(entry).read()
                        # Simple text extraction - this is a basic implementation
                        # and may not work for all HWP files
                        try:
                            # Try to decode as UTF-16LE (common for HWP text)
                            text += stream.decode('utf-16le', errors='ignore')
                        except:
                            try:
                                # Fallback to other encodings if needed
                                text += stream.decode('euc-kr', errors='ignore')
                            except:
                                text += stream.decode('cp949', errors='ignore')
                return text
        return ""
    except Exception as e:
        print(f"Error extracting text from HWP: {str(e)}")
        return ""

# Import converters
from converters.image_converter import ImageConverter
from converters.document_converter import DocumentConverter
from converters.excel_converter import ExcelConverter
from converters.powerpoint_converter import PowerPointConverter

# Flask 앱 생성
app = Flask(__name__,
           template_folder='templates',
           static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 임시 파일 저장 경로
TEMP_DIR = os.path.join(tempfile.gettempdir(), 'pdf_converter')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# 변환기 인스턴스 생성
image_converter = ImageConverter()
document_converter = DocumentConverter()
excel_converter = ExcelConverter()
powerpoint_converter = PowerPointConverter()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/image')
def image_converter_page():
    return render_template('image.html')

@app.route('/document')
def document_converter_page():
    return render_template('document.html')

@app.route('/excel')
def excel_converter_page():
    return render_template('excel.html')

@app.route('/powerpoint')
def powerpoint_converter_page():
    return render_template('powerpoint.html')

@app.route('/hwp')
def hwp_converter_page():
    return render_template('hwp.html')

@app.route('/convert/pdf-to-docx', methods=['POST'])
def pdf_to_docx():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # 고유한 임시 파일 경로 생성
        unique_id = str(uuid.uuid4())
        pdf_path = os.path.join(TEMP_DIR, f"{unique_id}_input.pdf")
        docx_path = os.path.join(TEMP_DIR, f"{unique_id}_output.docx")
        
        try:
            # PDF 파일 저장
            file.save(pdf_path)
            
            # PDF를 DOCX로 변환
            cv = Converter(pdf_path)
            cv.convert(docx_path)
            cv.close()
            
            # 변환된 파일 전송
            return send_file(
                docx_path,
                as_attachment=True,
                download_name=os.path.splitext(file.filename)[0] + '.docx',
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        finally:
            # 임시 파일 삭제
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                if os.path.exists(docx_path):
                    os.remove(docx_path)
            except Exception as e:
                print(f"Error cleaning up temporary files: {e}")

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/convert/pdf-to-hwp', methods=['POST'])
def pdf_to_hwp():
    return jsonify({
        'error': 'PDF에서 HWP로의 변환은 현재 지원되지 않습니다. 다른 방법을 시도해 주세요.'
    }), 400

@app.route('/convert/hwp-to-pdf', methods=['POST'])
def hwp_to_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 제공되지 않았습니다.'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        # 파일 확장자 확인
        filename = secure_filename(file.filename)
        if not (filename.lower().endswith('.hwp') or filename.lower().endswith('.hwp')):
            return jsonify({'error': 'HWP 파일만 업로드 가능합니다.'}), 400
        
        # 고유한 임시 파일 경로 생성
        unique_id = str(uuid.uuid4())
        temp_dir = os.path.join(TEMP_DIR, unique_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        input_path = os.path.join(temp_dir, filename)
        
        try:
            # 파일 저장
            file.save(input_path)
            
            # HWP 파일에서 텍스트 추출
            try:
                # Extract text from HWP file
                hwp_text = extract_text_from_hwp(input_path)
                
                if not hwp_text.strip():
                    raise Exception("HWP 파일에서 텍스트를 추출할 수 없습니다. 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다.")
                
                # Create a PDF object
                pdf = FPDF()
                pdf.add_page()
                
                # Set font (Korean support)
                try:
                    # Try to use Arial Unicode if available
                    pdf.add_font('Arial', '', 'C:/Windows/Fonts/arial.ttf', uni=True)
                    pdf.set_font('Arial', size=12)
                except:
                    try:
                        # Try to use Malgun Gothic if available
                        pdf.add_font('MalgunGothic', '', 'C:/Windows/Fonts/malgun.ttf', uni=True)
                        pdf.set_font('MalgunGothic', size=12)
                    except:
                        # Fallback to default font
                        pdf.add_font('Arial')
                        pdf.set_font('Arial', size=12)
                
                # Add text to PDF with proper encoding
                try:
                    # Try to encode as UTF-8 first
                    pdf.multi_cell(0, 10, txt=hwp_text.encode('utf-8', 'replace').decode('utf-8'))
                except:
                    try:
                        # Fallback to cp949 encoding
                        pdf.multi_cell(0, 10, txt=hwp_text.encode('cp949', 'replace').decode('cp949'))
                    except:
                        # Final fallback - just use the text as is
                        pdf.multi_cell(0, 10, txt=hwp_text)
                
                # Save PDF to a bytes buffer
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                
                # Return the PDF file
                return send_file(
                    BytesIO(pdf_bytes),
                    as_attachment=True,
                    download_name=f"{os.path.splitext(filename)[0]}.pdf",
                    mimetype='application/pdf'
                )
                
            except Exception as e:
                print(f"HWP to PDF conversion error: {str(e)}")
                return jsonify({'error': f'HWP 파일 처리 중 오류가 발생했습니다: {str(e)}'}), 500
                
        except Exception as e:
            print(f"File processing error: {str(e)}")
            return jsonify({'error': f'파일 처리 중 오류가 발생했습니다: {str(e)}'}), 500
            
        finally:
            # Clean up temporary files
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                print(f"Error cleaning up temporary files: {e}")
                
    except Exception as e:
        print(f"HWP to PDF conversion error: {str(e)}")
        return jsonify({'error': f'서버 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/convert/pdf-to-image', methods=['POST'])
def convert_pdf_to_image():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        format = request.form.get('format', 'jpg')
        if format not in ['jpg', 'png']:
            return jsonify({'error': 'Invalid format'}), 400
        
        # 임시 파일 저장
        input_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_input.pdf")
        file.save(input_path)
        
        try:
            # PDF를 이미지로 변환
            output_path = image_converter.pdf_to_image(input_path, format)
            
            # 변환된 파일 전송
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"{os.path.splitext(file.filename)[0]}.{format}",
                mimetype=f'image/{format}'
            )
        finally:
            # 임시 파일 삭제
            image_converter.cleanup(input_path, output_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert/image-to-pdf', methods=['POST'])
def convert_image_to_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # 임시 파일 저장
        input_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_input{os.path.splitext(file.filename)[1]}")
        file.save(input_path)
        
        try:
            # 이미지를 PDF로 변환
            output_path = image_converter.image_to_pdf(input_path)
            
            # 변환된 파일 전송
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"{os.path.splitext(file.filename)[0]}.pdf",
                mimetype='application/pdf'
            )
        finally:
            # 임시 파일 삭제
            image_converter.cleanup(input_path, output_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert/pdf-to-doc', methods=['POST'])
def convert_pdf_to_doc():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # 임시 파일 저장
        input_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_input.pdf")
        file.save(input_path)
        
        try:
            # PDF를 Word로 변환
            output_path = document_converter.pdf_to_doc(input_path)
            
            # 변환된 파일 전송
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"{os.path.splitext(file.filename)[0]}.docx",
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        finally:
            # 임시 파일 삭제
            document_converter.cleanup(input_path, output_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert/doc-to-pdf', methods=['POST'])
def convert_doc_to_pdf():
    input_path = None
    output_path = None
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # 임시 파일 저장
        input_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_input.docx")
        file.save(input_path)
        
        # Word를 PDF로 변환
        output_path = document_converter.doc_to_pdf(input_path)
        
        # 변환된 파일 전송
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{os.path.splitext(file.filename)[0]}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # 임시 파일 삭제
        if input_path or output_path:
            document_converter.cleanup(input_path, output_path)

@app.route('/api/convert/pdf-to-hwp', methods=['POST'])
def convert_pdf_to_hwp():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # 임시 파일 저장
        input_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_input.pdf")
        file.save(input_path)
        
        try:
            # PDF를 HWP로 변환
            output_path = hwp_converter.pdf_to_hwp(input_path)
            
            # 변환된 파일 전송
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"{os.path.splitext(file.filename)[0]}.hwp",
                mimetype='application/x-hwp'
            )
        finally:
            # 임시 파일 삭제
            hwp_converter.cleanup(input_path, output_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert/hwp-to-pdf', methods=['POST'])
def convert_hwp_to_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.hwp'):
            return jsonify({'error': 'Invalid file format. Please upload an HWP file.'}), 400
        
        # 파일 저장
        filename = secure_filename(file.filename)
        temp_path = os.path.join(TEMP_DIR, filename)
        file.save(temp_path)
        
        # 파일 변환
        output_path = hwp_converter.hwp_to_pdf(temp_path)
        
        # 임시 파일 정리
        hwp_converter.cleanup(temp_path)
        
        return jsonify({'path': output_path})
        
    except Exception as e:
        return str(e), 500

@app.route('/api/convert/pdf-to-excel', methods=['POST'])
def convert_pdf_to_excel():
    output_path = None
    input_path = None
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # 옵션 가져오기
        preserve_formatting = request.form.get('preserveFormatting', 'true').lower() == 'true'
        detect_tables = request.form.get('detectTables', 'true').lower() == 'true'
        
        # 임시 파일 저장
        input_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_input.pdf")
        file.save(input_path)
        
        # PDF를 Excel로 변환
        output_path = excel_converter.pdf_to_excel(
            input_path,
            preserve_formatting=preserve_formatting,
            detect_tables=detect_tables
        )
        
        if not output_path or not os.path.exists(output_path):
            raise Exception("Failed to generate Excel file")
        
        # 변환된 파일 전송
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{os.path.splitext(file.filename)[0]}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        app.logger.error(f"PDF to Excel conversion error: {str(e)}")
        return jsonify({'error': f'PDF to Excel conversion failed: {str(e)}'}), 500
    finally:
        # 임시 파일 정리
        try:
            if input_path and os.path.exists(input_path):
                os.unlink(input_path)
            if output_path and os.path.exists(output_path):
                os.unlink(output_path)
        except Exception as e:
            app.logger.error(f"Error cleaning up temporary files: {str(e)}")

@app.route('/api/convert/excel-to-pdf', methods=['POST'])
def convert_excel_to_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # 임시 파일 저장
        input_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_input.xlsx")
        file.save(input_path)
        
        try:
            # Excel을 PDF로 변환
            output_path = excel_converter.excel_to_pdf(input_path)
            
            # 변환된 파일 전송
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"{os.path.splitext(file.filename)[0]}.pdf",
                mimetype='application/pdf'
            )
        finally:
            # 임시 파일 삭제
            excel_converter.cleanup(input_path, output_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert/pdf-to-ppt', methods=['POST'])
def convert_pdf_to_ppt():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # 옵션 가져오기
        extract_images = request.form.get('extractImages', 'true').lower() == 'true'
        preserve_layout = request.form.get('preserveLayout', 'true').lower() == 'true'
        create_animations = request.form.get('createAnimations', 'false').lower() == 'true'
        
        # 임시 파일 저장
        input_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_input.pdf")
        file.save(input_path)
        
        try:
            # PDF를 PowerPoint로 변환
            output_path = powerpoint_converter.pdf_to_ppt(
                input_path,
                extract_images=extract_images,
                preserve_layout=preserve_layout,
                create_animations=create_animations
            )
            
            # 변환된 파일 전송
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"{os.path.splitext(file.filename)[0]}.pptx",
                mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
            )
        finally:
            # 임시 파일 삭제
            powerpoint_converter.cleanup(input_path, output_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert/ppt-to-pdf', methods=['POST'])
def convert_ppt_to_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # 임시 파일 저장
        input_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_input.pptx")
        file.save(input_path)
        
        try:
            # PowerPoint를 PDF로 변환
            output_path = powerpoint_converter.ppt_to_pdf(input_path)
            
            # 변환된 파일 전송
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"{os.path.splitext(file.filename)[0]}.pdf",
                mimetype='application/pdf'
            )
        finally:
            # 임시 파일 삭제
            powerpoint_converter.cleanup(input_path, output_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download')
def download_file():
    try:
        file_path = request.args.get('path')
        if not file_path or not os.path.exists(file_path):
            return 'File not found', 404
            
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True) 