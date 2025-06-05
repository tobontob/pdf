import fitz  # PyMuPDF
from PIL import Image
import io
import json

def get_pdf_metadata(input_path):
    """
    Get metadata from a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
    
    Returns:
        dict: Dictionary containing PDF metadata
    """
    doc = fitz.open(input_path)
    
    metadata = {
        'title': doc.metadata.get('title', ''),
        'author': doc.metadata.get('author', ''),
        'subject': doc.metadata.get('subject', ''),
        'keywords': doc.metadata.get('keywords', ''),
        'creator': doc.metadata.get('creator', ''),
        'producer': doc.metadata.get('producer', ''),
        'creation_date': doc.metadata.get('creationDate', ''),
        'modification_date': doc.metadata.get('modDate', ''),
        'page_count': doc.page_count,
        'file_size': doc.stream_length,
        'pdf_version': doc.version
    }
    
    doc.close()
    return metadata

def extract_text_from_page(input_path, page_number):
    """
    Extract text from a specific page of a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
        page_number (int): Page number to extract text from (1-based)
    
    Returns:
        str: Extracted text from the page
    """
    doc = fitz.open(input_path)
    
    # Convert to 0-based index and validate
    page_index = page_number - 1
    if 0 <= page_index < doc.page_count:
        page = doc[page_index]
        text = page.get_text()
    else:
        text = ''
    
    doc.close()
    return text

def generate_thumbnail(input_path, page_number=1, size=(200, 200)):
    """
    Generate a thumbnail image for a specific page of a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
        page_number (int): Page number to generate thumbnail from (1-based)
        size (tuple): Target thumbnail size (width, height)
    
    Returns:
        bytes: Thumbnail image data in PNG format
    """
    doc = fitz.open(input_path)
    
    # Convert to 0-based index and validate
    page_index = page_number - 1
    if 0 <= page_index < doc.page_count:
        page = doc[page_index]
        
        # Set zoom factors to fit target size
        zoom_x = size[0] / page.rect.width
        zoom_y = size[1] / page.rect.height
        zoom = min(zoom_x, zoom_y)  # Use smaller zoom to fit both dimensions
        
        # Create pixmap with white background
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Save thumbnail to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        thumbnail_data = img_buffer.getvalue()
    else:
        thumbnail_data = None
    
    doc.close()
    return thumbnail_data

def get_page_count(input_path):
    """
    Get the number of pages in a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
    
    Returns:
        int: Number of pages in the PDF
    """
    doc = fitz.open(input_path)
    count = doc.page_count
    doc.close()
    return count 