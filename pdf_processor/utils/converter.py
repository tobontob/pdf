from pdf2docx import Converter
from docx2pdf import convert as docx2pdf
from pdf2image import convert_from_path
from PIL import Image
import os
import fitz  # PyMuPDF

def pdf_to_word(input_path, output_path):
    """
    Convert PDF to Word document.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the Word document
    """
    cv = Converter(input_path)
    cv.convert(output_path)
    cv.close()

def pdf_to_image(input_path, output_path, fmt='jpg'):
    """
    Convert PDF to image(s).
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the image(s)
        fmt (str): Output image format ('jpg' or 'png')
    """
    images = convert_from_path(input_path)
    
    # If single page, save directly
    if len(images) == 1:
        images[0].save(output_path, fmt.upper())
    else:
        # Save multiple pages with sequential names
        base_path = os.path.splitext(output_path)[0]
        for i, image in enumerate(images):
            image.save(f"{base_path}_{i+1}.{fmt}", fmt.upper())

def word_to_pdf(input_path, output_path):
    """
    Convert Word document to PDF.
    
    Args:
        input_path (str): Path to the input Word document
        output_path (str): Path to save the PDF file
    """
    docx2pdf(input_path, output_path)

def image_to_pdf(input_path, output_path):
    """
    Convert image to PDF.
    
    Args:
        input_path (str): Path to the input image file
        output_path (str): Path to save the PDF file
    """
    image = Image.open(input_path)
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    image.save(output_path, 'PDF')

def merge_pdfs(input_paths, output_path):
    """
    Merge multiple PDF files into one.
    
    Args:
        input_paths (list): List of paths to input PDF files
        output_path (str): Path to save the merged PDF
    """
    merger = fitz.open()
    
    for path in input_paths:
        merger.insert_pdf(fitz.open(path))
    
    merger.save(output_path)
    merger.close()

def split_pdf(input_path, output_path, start_page, end_page):
    """
    Split PDF file into a new file with specified page range.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the split PDF
        start_page (int): Start page number (1-based)
        end_page (int): End page number (1-based)
    """
    doc = fitz.open(input_path)
    new_doc = fitz.open()
    
    # Convert to 0-based indexing
    start_page -= 1
    end_page -= 1
    
    # Validate page range
    if start_page < 0:
        start_page = 0
    if end_page >= doc.page_count:
        end_page = doc.page_count - 1
    if start_page > end_page:
        start_page, end_page = end_page, start_page
    
    # Copy specified pages
    new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page)
    
    new_doc.save(output_path)
    new_doc.close()
    doc.close() 