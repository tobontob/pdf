import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os

def extract_text_from_pdf(input_path, use_ocr=False):
    """
    Extract text from a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
        use_ocr (bool): Whether to use OCR for text extraction
    
    Returns:
        list: List of extracted text for each page
    """
    doc = fitz.open(input_path)
    text_by_page = []
    
    for page in doc:
        if use_ocr:
            # Convert page to image
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(img)
        else:
            # Extract text directly from PDF
            text = page.get_text()
        
        text_by_page.append(text.strip())
    
    doc.close()
    return text_by_page

def extract_text_from_image(input_path, lang='eng'):
    """
    Extract text from an image file using OCR.
    
    Args:
        input_path (str): Path to the input image file
        lang (str): Language code for OCR (e.g., 'eng', 'kor', 'jpn')
    
    Returns:
        str: Extracted text from the image
    """
    # Open and process image
    image = Image.open(input_path)
    
    # Convert to RGB if necessary
    if image.mode not in ('L', 'RGB'):
        image = image.convert('RGB')
    
    # Extract text using OCR
    text = pytesseract.image_to_string(image, lang=lang)
    
    return text.strip()

def get_available_languages():
    """
    Get list of available OCR languages.
    
    Returns:
        list: List of available language codes
    """
    try:
        # Get Tesseract data directory
        tessdata_dir = os.path.join(os.path.dirname(pytesseract.get_tesseract_version().__str__()), 'tessdata')
        
        # List all .traineddata files
        languages = []
        for file in os.listdir(tessdata_dir):
            if file.endswith('.traineddata'):
                languages.append(file[:-12])  # Remove .traineddata extension
        
        return sorted(languages)
    except Exception:
        # Return basic languages if can't access tessdata directory
        return ['eng', 'kor', 'jpn', 'chi_sim', 'chi_tra'] 