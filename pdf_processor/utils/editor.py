import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import io
import os

def add_text(input_path, output_path, text, x, y, page_number=1, font_size=12, color=(0, 0, 0)):
    """
    Add text to a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the modified PDF
        text (str): Text to add
        x (float): X coordinate
        y (float): Y coordinate
        page_number (int): Page number to add text to (1-based)
        font_size (int): Font size
        color (tuple): RGB color tuple
    """
    doc = fitz.open(input_path)
    page = doc[page_number - 1]  # Convert to 0-based index
    
    # Convert RGB color to hex string
    color_str = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
    
    # Insert text
    page.insert_text((x, y), text, fontsize=font_size, color=color_str)
    
    doc.save(output_path)
    doc.close()

def add_watermark(input_path, output_path, text, opacity=0.3):
    """
    Add watermark to all pages of a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the watermarked PDF
        text (str): Watermark text
        opacity (float): Watermark opacity (0.0 to 1.0)
    """
    doc = fitz.open(input_path)
    
    for page in doc:
        # Get page dimensions
        rect = page.rect
        
        # Create watermark text
        font_size = min(rect.width, rect.height) / 20
        angle = 45  # Rotate 45 degrees
        
        # Create text annotation
        page.insert_text(
            (rect.width/2, rect.height/2),  # Center of page
            text,
            fontsize=font_size,
            rotate=angle,
            color=(0, 0, 0),  # Black color
            opacity=opacity,
            align=fitz.TEXT_ALIGN_CENTER
        )
    
    doc.save(output_path)
    doc.close()

def add_page_numbers(input_path, output_path, start_number=1, position='bottom-right'):
    """
    Add page numbers to a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the numbered PDF
        start_number (int): Starting page number
        position (str): Position of page numbers ('bottom-right', 'bottom-center', 'bottom-left')
    """
    doc = fitz.open(input_path)
    
    for i in range(doc.page_count):
        page = doc[i]
        rect = page.rect
        number = str(i + start_number)
        
        # Calculate position
        if position == 'bottom-right':
            x = rect.width - 50
            y = rect.height - 30
        elif position == 'bottom-center':
            x = rect.width / 2
            y = rect.height - 30
        else:  # bottom-left
            x = 50
            y = rect.height - 30
        
        # Add page number
        page.insert_text(
            (x, y),
            number,
            fontsize=10,
            color=(0, 0, 0)  # Black color
        )
    
    doc.save(output_path)
    doc.close()

def rotate_page(input_path, output_path, page_number, angle):
    """
    Rotate a specific page in a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the modified PDF
        page_number (int): Page number to rotate (1-based)
        angle (int): Rotation angle (90, 180, or 270)
    """
    doc = fitz.open(input_path)
    page = doc[page_number - 1]  # Convert to 0-based index
    
    # Normalize angle to 90-degree increments
    angle = ((angle + 45) // 90 * 90) % 360
    
    # Apply rotation
    page.set_rotation(angle)
    
    doc.save(output_path)
    doc.close()

def delete_page(input_path, output_path, page_number):
    """
    Delete a specific page from a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the modified PDF
        page_number (int): Page number to delete (1-based)
    """
    doc = fitz.open(input_path)
    
    # Convert to 0-based index and validate
    page_index = page_number - 1
    if 0 <= page_index < doc.page_count:
        doc.delete_page(page_index)
    
    doc.save(output_path)
    doc.close() 