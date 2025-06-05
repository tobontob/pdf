from flask import Blueprint, render_template, request, send_file, jsonify, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os

from pdf_processor.utils.converter import (pdf_to_word, pdf_to_image, word_to_pdf,
                                         image_to_pdf, merge_pdfs, split_pdf)
from pdf_processor.utils.editor import (add_text, add_watermark, add_page_numbers,
                                      rotate_page, delete_page)
from pdf_processor.utils.security import encrypt_pdf, decrypt_pdf, set_pdf_permissions
from pdf_processor.utils.ocr import extract_text_from_pdf, extract_text_from_image, get_available_languages
from pdf_processor.utils.compressor import compress_pdf, get_file_size
from pdf_processor.utils.forms import (add_form_fields, fill_form_fields,
                                     extract_form_fields, flatten_form_fields)
from pdf_processor.utils.preview import (get_pdf_metadata, extract_text_from_page,
                                       generate_thumbnail, get_page_count)

bp = Blueprint('main', __name__, 
              url_prefix='',
              static_folder='static',
              static_url_path='/static')

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
PROCESSED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processed')

# Ensure upload and processed directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/convert', methods=['GET', 'POST'])
def convert():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '파일이 업로드되지 않았습니다'
            }), 400
        
        file = request.files['file']
        convert_to = request.form.get('convert_to')
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '파일이 선택되지 않았습니다'
            }), 400
        
        if not convert_to:
            return jsonify({
                'success': False,
                'message': '변환 형식이 지정되지 않았습니다'
            }), 400
        
        try:
            filename = secure_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_path)
            
            # Generate output filename
            output_filename = os.path.splitext(filename)[0]
            if convert_to == 'pdf_to_word':
                output_path = os.path.join(PROCESSED_FOLDER, f"{output_filename}.docx")
                success = pdf_to_word(input_path, output_path)
            elif convert_to == 'pdf_to_image':
                output_path = os.path.join(PROCESSED_FOLDER, output_filename)
                success = pdf_to_image(input_path, output_path)
            elif convert_to == 'word_to_pdf':
                output_path = os.path.join(PROCESSED_FOLDER, f"{output_filename}.pdf")
                success = word_to_pdf(input_path, output_path)
            elif convert_to == 'image_to_pdf':
                output_path = os.path.join(PROCESSED_FOLDER, f"{output_filename}.pdf")
                success = image_to_pdf(input_path, output_path)
            else:
                return jsonify({
                    'success': False,
                    'message': '지원하지 않는 변환 형식입니다'
                }), 400
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '파일 변환이 완료되었습니다.',
                    'download_url': url_for('main.download_file', filename=os.path.basename(output_path))
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '파일 변환 중 오류가 발생했습니다. 다시 시도해 주세요.'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'파일 처리 중 오류가 발생했습니다: {str(e)}'
            }), 500
        finally:
            # Clean up input file
            if os.path.exists(input_path):
                os.remove(input_path)
    
    return render_template('convert.html')

@bp.route('/convert/from-pdf', methods=['POST'])
def convert_from_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'PDF 파일이 업로드되지 않았습니다'
        }), 400
    
    file = request.files['pdf_file']
    output_format = request.form.get('output_format')
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': '파일이 선택되지 않았습니다'
        }), 400
    
    if not output_format:
        return jsonify({
            'success': False,
            'message': '변환 형식이 지정되지 않았습니다'
        }), 400
    
    try:
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)
        
        output_filename = os.path.splitext(filename)[0]
        if output_format == 'docx':
            output_path = os.path.join(PROCESSED_FOLDER, f"{output_filename}.docx")
            success = pdf_to_word(input_path, output_path)
        elif output_format in ['jpg', 'png']:
            output_path = os.path.join(PROCESSED_FOLDER, f"{output_filename}.{output_format}")
            success = pdf_to_image(input_path, output_path, format=output_format)
        elif output_format == 'text':
            output_path = os.path.join(PROCESSED_FOLDER, f"{output_filename}.txt")
            success = extract_text_from_pdf(input_path, output_path)
        else:
            return jsonify({
                'success': False,
                'message': '지원하지 않는 변환 형식입니다'
            }), 400
        
        if success:
            return jsonify({
                'success': True,
                'message': '파일 변환이 완료되었습니다',
                'download_url': url_for('main.download_file', filename=os.path.basename(output_path))
            })
        else:
            return jsonify({
                'success': False,
                'message': '파일 변환 중 오류가 발생했습니다'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'파일 처리 중 오류가 발생했습니다: {str(e)}'
        }), 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@bp.route('/convert/to-pdf', methods=['POST'])
def convert_to_pdf():
    if 'input_file' not in request.files:
        return jsonify({
            'success': False,
            'message': '파일이 업로드되지 않았습니다'
        }), 400
    
    file = request.files['input_file']
    merge_files = request.form.get('merge_files', False)
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': '파일이 선택되지 않았습니다'
        }), 400
    
    try:
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)
        
        output_filename = f"{os.path.splitext(filename)[0]}.pdf"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.doc', '.docx']:
            success = word_to_pdf(input_path, output_path)
        elif ext in ['.jpg', '.jpeg', '.png']:
            success = image_to_pdf(input_path, output_path)
        else:
            return jsonify({
                'success': False,
                'message': '지원하지 않는 파일 형식입니다'
            }), 400
        
        if success:
            return jsonify({
                'success': True,
                'message': '파일 변환이 완료되었습니다',
                'download_url': url_for('main.download_file', filename=output_filename)
            })
        else:
            return jsonify({
                'success': False,
                'message': '파일 변환 중 오류가 발생했습니다'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'파일 처리 중 오류가 발생했습니다: {str(e)}'
        }), 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@bp.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)

@bp.route('/organize', methods=['GET'])
def organize():
    return render_template('organize.html')

@bp.route('/merge_pdfs', methods=['POST'])
def merge_pdfs():
    if 'pdf_files' not in request.files:
        return jsonify({
            'success': False,
            'message': 'PDF 파일이 업로드되지 않았습니다'
        }), 400
    
    files = request.files.getlist('pdf_files')
    if not files or files[0].filename == '':
        return jsonify({
            'success': False,
            'message': '파일이 선택되지 않았습니다'
        }), 400
    
    try:
        # 파일 저장 및 병합 처리
        input_paths = []
        for file in files:
            filename = secure_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_path)
            input_paths.append(input_path)
        
        output_filename = 'merged.pdf'
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        success = merge_pdfs(input_paths, output_path)
        
        # 임시 파일 정리
        for path in input_paths:
            if os.path.exists(path):
                os.remove(path)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'PDF 파일 병합이 완료되었습니다',
                'download_url': url_for('main.download_file', filename=output_filename)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'PDF 파일 병합 중 오류가 발생했습니다'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'파일 처리 중 오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/split_pdf', methods=['POST'])
def split_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'PDF 파일이 업로드되지 않았습니다'
        }), 400
    
    file = request.files['pdf_file']
    split_type = request.form.get('split_type')
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': '파일이 선택되지 않았습니다'
        }), 400
    
    try:
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)
        
        output_dir = os.path.join(PROCESSED_FOLDER, 'split')
        os.makedirs(output_dir, exist_ok=True)
        
        if split_type == 'range':
            start_page = int(request.form.get('start_page', 1))
            end_page = int(request.form.get('end_page', 1))
            success = split_pdf_range(input_path, output_dir, start_page, end_page)
        else:
            success = split_pdf_all(input_path, output_dir)
        
        if os.path.exists(input_path):
            os.remove(input_path)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'PDF 파일 분할이 완료되었습니다',
                'download_url': url_for('main.download_file', filename='split.zip')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'PDF 파일 분할 중 오류가 발생했습니다'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'파일 처리 중 오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/rotate_pdf', methods=['POST'])
def rotate_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'PDF 파일이 업로드되지 않았습니다'
        }), 400
    
    file = request.files['pdf_file']
    page_number = request.form.get('page_number', type=int)
    angle = request.form.get('angle', type=int)
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': '파일이 선택되지 않았습니다'
        }), 400
    
    if not page_number or not angle:
        return jsonify({
            'success': False,
            'message': '페이지 번호와 회전 각도를 지정해주세요'
        }), 400
    
    try:
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)
        
        output_filename = f"rotated_{filename}"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        success = rotate_page(input_path, output_path, page_number, angle)
        
        if success:
            return jsonify({
                'success': True,
                'message': '페이지 회전이 완료되었습니다',
                'download_url': url_for('main.download_file', filename=output_filename)
            })
        else:
            return jsonify({
                'success': False,
                'message': '페이지 회전 중 오류가 발생했습니다'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'파일 처리 중 오류가 발생했습니다: {str(e)}'
        }), 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@bp.route('/delete_pages', methods=['POST'])
def delete_pages():
    if 'pdf_file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'PDF 파일이 업로드되지 않았습니다'
        }), 400
    
    file = request.files['pdf_file']
    page_numbers = request.form.get('page_numbers')
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': '파일이 선택되지 않았습니다'
        }), 400
    
    if not page_numbers:
        return jsonify({
            'success': False,
            'message': '삭제할 페이지 번호를 지정해주세요'
        }), 400
    
    try:
        # Parse page numbers (e.g., "1,3,5-7" -> [1,3,5,6,7])
        pages_to_delete = []
        for part in page_numbers.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages_to_delete.extend(range(start, end + 1))
            else:
                pages_to_delete.append(int(part))
        
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)
        
        output_filename = f"pages_deleted_{filename}"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        
        success = delete_page(input_path, output_path, pages_to_delete)
        
        if success:
            return jsonify({
                'success': True,
                'message': '페이지 삭제가 완료되었습니다',
                'download_url': url_for('main.download_file', filename=output_filename)
            })
        else:
            return jsonify({
                'success': False,
                'message': '페이지 삭제 중 오류가 발생했습니다'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'파일 처리 중 오류가 발생했습니다: {str(e)}'
        }), 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

@bp.route('/edit', methods=['GET', 'POST'])
def edit():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'PDF 파일이 업로드되지 않았습니다'
            }), 400
        
        file = request.files['pdf_file']
        edit_type = request.form.get('edit_type')
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '파일이 선택되지 않았습니다'
            }), 400
        
        try:
            filename = secure_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_path)
            
            output_filename = f'edited_{filename}'
            output_path = os.path.join(PROCESSED_FOLDER, output_filename)
            
            if edit_type == 'text':
                success = edit_pdf_text(input_path, output_path)
            elif edit_type == 'image':
                success = edit_pdf_image(input_path, output_path)
            elif edit_type == 'annotate':
                success = add_pdf_annotation(input_path, output_path)
            else:
                return jsonify({
                    'success': False,
                    'message': '지원하지 않는 편집 작업입니다'
                }), 400
            
            if os.path.exists(input_path):
                os.remove(input_path)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'PDF 파일 편집이 완료되었습니다',
                    'download_url': url_for('main.download_file', filename=output_filename)
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'PDF 파일 편집 중 오류가 발생했습니다'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'파일 처리 중 오류가 발생했습니다: {str(e)}'
            }), 500
            
    return render_template('edit.html')

@bp.route('/ocr', methods=['GET', 'POST'])
def ocr():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '파일이 업로드되지 않았습니다'
            }), 400
        
        file = request.files['file']
        language = request.form.get('language', 'eng')
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '파일이 선택되지 않았습니다'
            }), 400
        
        try:
            filename = secure_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_path)
            
            output_filename = f"{os.path.splitext(filename)[0]}_ocr.txt"
            output_path = os.path.join(PROCESSED_FOLDER, output_filename)
            
            success = perform_ocr(input_path, output_path, language)
            
            if os.path.exists(input_path):
                os.remove(input_path)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'OCR 처리가 완료되었습니다',
                    'download_url': url_for('main.download_file', filename=output_filename)
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'OCR 처리 중 오류가 발생했습니다'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'파일 처리 중 오류가 발생했습니다: {str(e)}'
            }), 500
            
    return render_template('ocr.html')

@bp.route('/compress', methods=['GET', 'POST'])
def compress():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'PDF 파일이 업로드되지 않았습니다'
            }), 400
        
        file = request.files['pdf_file']
        compression_level = request.form.get('compression_level', 'medium')
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '파일이 선택되지 않았습니다'
            }), 400
        
        try:
            filename = secure_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_path)
            
            output_filename = f"compressed_{filename}"
            output_path = os.path.join(PROCESSED_FOLDER, output_filename)
            
            success = compress_pdf(input_path, output_path, compression_level)
            
            if os.path.exists(input_path):
                os.remove(input_path)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'PDF 파일 압축이 완료되었습니다',
                    'download_url': url_for('main.download_file', filename=output_filename)
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'PDF 파일 압축 중 오류가 발생했습니다'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'파일 처리 중 오류가 발생했습니다: {str(e)}'
            }), 500
            
    return render_template('compress.html')

@bp.route('/security', methods=['GET', 'POST'])
def security():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': '파일이 업로드되지 않았습니다'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'PDF 파일만 허용됩니다'}), 400

        action = request.form.get('action')
        if not action:
            return jsonify({'error': '작업이 지정되지 않았습니다'}), 400

        # Save the uploaded file
        input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(input_path)

        try:
            if action == 'encrypt':
                password = request.form.get('password')
                if not password:
                    return jsonify({'error': '암호화를 위한 비밀번호가 필요합니다'}), 400
                
                encrypt_pdf(input_path, output_path, password)
                action_text = '암호화'

            elif action == 'decrypt':
                password = request.form.get('password')
                if not password:
                    return jsonify({'error': '복호화를 위한 비밀번호가 필요합니다'}), 400
                
                if not decrypt_pdf(input_path, output_path, password):
                    return jsonify({'error': '잘못된 비밀번호이거나 복호화에 실패했습니다'}), 400
                action_text = '복호화'

            elif action == 'set_permissions':
                owner_password = request.form.get('owner_password')
                if not owner_password:
                    return jsonify({'error': '소유자 비밀번호가 필요합니다'}), 400
                
                permissions = {
                    'print': 'permissions[print]' in request.form,
                    'modify': 'permissions[modify]' in request.form,
                    'copy': 'permissions[copy]' in request.form,
                    'annotate': 'permissions[annotate]' in request.form
                }
                
                set_pdf_permissions(input_path, output_path, owner_password, permissions)
                action_text = '권한 설정'

            else:
                return jsonify({'error': '지원하지 않는 작업입니다'}), 400

            # Clean up input file
            os.remove(input_path)

            # Generate download URL
            download_url = url_for('main.download_file', filename=secure_filename(output_filename))
            return jsonify({
                'message': f'PDF {action_text}가 완료되었습니다',
                'download_url': download_url
            })

        except Exception as e:
            # Clean up files in case of error
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
            return jsonify({'error': str(e)}), 500

    return render_template('security.html')

@bp.route('/forms', methods=['GET', 'POST'])
def forms():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        action = request.form.get('action')
        if not action:
            return jsonify({'error': 'No action specified'}), 400

        # Save the uploaded file
        input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(input_path)

        # Generate output filename
        output_filename = f"{os.path.splitext(file.filename)[0]}_{action}.pdf"
        output_path = os.path.join(UPLOAD_FOLDER, secure_filename(output_filename))

        try:
            if action == 'add_fields':
                # Collect field information
                fields = []
                field_counter = 0
                while f'field_type_{field_counter}' in request.form:
                    field = {
                        'type': request.form[f'field_type_{field_counter}'],
                        'name': request.form[f'field_name_{field_counter}'],
                        'page': int(request.form[f'field_page_{field_counter}']),
                        'x': float(request.form[f'field_x_{field_counter}']),
                        'y': float(request.form[f'field_y_{field_counter}'])
                    }
                    fields.append(field)
                    field_counter += 1
                
                add_form_fields(input_path, output_path, fields)
                action_text = 'added form fields'

            elif action == 'fill_fields':
                use_json = 'use_json' in request.form
                
                if use_json:
                    if 'json_file' not in request.files:
                        return jsonify({'error': 'No JSON file uploaded'}), 400
                    
                    json_file = request.files['json_file']
                    if json_file.filename == '':
                        return jsonify({'error': 'No JSON file selected'}), 400
                    
                    # Save JSON file
                    json_path = os.path.join(UPLOAD_FOLDER, secure_filename(json_file.filename))
                    json_file.save(json_path)
                    
                    fill_form_fields(input_path, output_path, json_path, from_json=True)
                    os.remove(json_path)
                else:
                    # Collect field values from form
                    field_values = {}
                    for key, value in request.form.items():
                        if key.startswith('field_value_'):
                            field_name = key.replace('field_value_', '')
                            field_values[field_name] = value
                    
                    fill_form_fields(input_path, output_path, field_values)
                
                action_text = 'filled form fields'

            elif action == 'extract_fields':
                fields = extract_form_fields(input_path)
                os.remove(input_path)  # No output file needed
                return jsonify(fields)

            elif action == 'flatten_fields':
                flatten_form_fields(input_path, output_path)
                action_text = 'flattened form fields'

            else:
                return jsonify({'error': 'Invalid action specified'}), 400

            # Clean up input file
            os.remove(input_path)

            # Generate download URL
            download_url = url_for('main.download_file', filename=secure_filename(output_filename))
            return jsonify({
                'message': f'PDF successfully {action_text}',
                'download_url': download_url
            })

        except Exception as e:
            # Clean up files in case of error
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
            return jsonify({'error': str(e)}), 500

    return render_template('forms.html')

@bp.route('/get_form_fields', methods=['POST'])
def get_form_fields():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed'}), 400

    # Save the uploaded file
    input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(input_path)

    try:
        fields = extract_form_fields(input_path)
        os.remove(input_path)
        return jsonify(fields)
    except Exception as e:
        if os.path.exists(input_path):
            os.remove(input_path)
        return jsonify({'error': str(e)}), 500

@bp.route('/preview', methods=['GET', 'POST'])
def preview():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        # Save the uploaded file
        input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(input_path)

        try:
            # Get metadata
            metadata = get_pdf_metadata(input_path)

            # Generate temporary URL for PDF access
            pdf_url = url_for('main.download_file', filename=secure_filename(file.filename))

            return jsonify({
                'message': 'PDF processed successfully',
                'pdf_url': pdf_url,
                'metadata': metadata
            })

        except Exception as e:
            if os.path.exists(input_path):
                os.remove(input_path)
            return jsonify({'error': str(e)}), 500

    return render_template('preview.html')

@bp.route('/preview/text/<path:filename>/<int:page>', methods=['GET'])
def get_page_text(filename, page):
    try:
        input_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        if not os.path.exists(input_path):
            return jsonify({'error': 'File not found'}), 404

        text = extract_text_from_page(input_path, page)
        return jsonify({'text': text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/preview/thumbnail/<path:filename>/<int:page>', methods=['GET'])
def get_page_thumbnail(filename, page):
    try:
        input_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        if not os.path.exists(input_path):
            return jsonify({'error': 'File not found'}), 404

        # Generate thumbnail filename
        thumbnail_filename = f"{os.path.splitext(filename)[0]}_thumb_{page}.png"
        thumbnail_path = os.path.join(UPLOAD_FOLDER, secure_filename(thumbnail_filename))

        # Generate thumbnail
        generate_thumbnail(input_path, page, thumbnail_path)

        # Return thumbnail URL
        return jsonify({
            'thumbnail_url': url_for('main.download_file', filename=secure_filename(thumbnail_filename))
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/batch', methods=['GET', 'POST'])
def batch():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        action = request.form.get('action')
        if not action:
            return jsonify({'error': 'No action specified'}), 400

        # Save the uploaded file
        input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(input_path)

        try:
            if action == 'convert':
                convert_to = request.form.get('convert_to', 'docx')
                output_filename = f"{os.path.splitext(file.filename)[0]}.{convert_to}"
                output_path = os.path.join(UPLOAD_FOLDER, secure_filename(output_filename))
                
                if convert_to in ['docx', 'xlsx', 'pptx']:
                    convert_to_office(input_path, output_path, convert_to)
                else:
                    convert_to_image(input_path, output_path, convert_to)
                
                action_text = f'converted to {convert_to.upper()}'

            elif action == 'compress':
                compression_level = request.form.get('compression_level', 'medium')
                output_filename = f"{os.path.splitext(file.filename)[0]}_compressed.pdf"
                output_path = os.path.join(UPLOAD_FOLDER, secure_filename(output_filename))
                
                compress_pdf(input_path, output_path, compression_level)
                action_text = 'compressed'

            elif action == 'extract_text':
                output_format = request.form.get('output_format', 'txt')
                use_ocr = 'use_ocr' in request.form
                
                output_filename = f"{os.path.splitext(file.filename)[0]}.{output_format}"
                output_path = os.path.join(UPLOAD_FOLDER, secure_filename(output_filename))
                
                if use_ocr:
                    extract_text_from_pdf(input_path, output_path, use_ocr=True)
                else:
                    extract_text_from_pdf(input_path, output_path)
                
                action_text = 'text extracted'

            elif action == 'add_watermark':
                watermark_text = request.form.get('watermark_text')
                if not watermark_text:
                    return jsonify({'error': 'Watermark text is required'}), 400
                
                opacity = float(request.form.get('watermark_opacity', 30)) / 100
                output_filename = f"{os.path.splitext(file.filename)[0]}_watermarked.pdf"
                output_path = os.path.join(UPLOAD_FOLDER, secure_filename(output_filename))
                
                add_watermark(input_path, output_path, watermark_text, opacity)
                action_text = 'watermark added'

            elif action == 'encrypt':
                password = request.form.get('password')
                if not password:
                    return jsonify({'error': 'Password is required'}), 400
                
                output_filename = f"{os.path.splitext(file.filename)[0]}_encrypted.pdf"
                output_path = os.path.join(UPLOAD_FOLDER, secure_filename(output_filename))
                
                encrypt_pdf(input_path, output_path, password)
                action_text = 'encrypted'

            else:
                return jsonify({'error': 'Invalid action specified'}), 400

            # Clean up input file
            os.remove(input_path)

            # Generate download URL
            download_url = url_for('main.download_file', filename=secure_filename(output_filename))
            return jsonify({
                'message': f'PDF successfully {action_text}',
                'download_url': download_url
            })

        except Exception as e:
            # Clean up files in case of error
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
            return jsonify({'error': str(e)}), 500

    return render_template('batch.html')

if __name__ == '__main__':
    bp.run(debug=True) 