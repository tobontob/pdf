import fitz  # PyMuPDF
import os

def compress_pdf(input_path, output_path, quality=50):
    """
    Compress a PDF file by reducing image quality and optimizing content.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the compressed PDF
        quality (int): Image quality (1-100, lower means more compression)
    """
    doc = fitz.open(input_path)
    
    for page in doc:
        # Get list of images on the page
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            xref = img[0]  # Cross-reference number of the image
            
            # Try to get image data
            try:
                base_image = doc.extract_image(xref)
                image_data = base_image["image"]
                
                # Convert to PIL Image for compression
                from PIL import Image
                import io
                
                image = Image.open(io.BytesIO(image_data))
                
                # Convert RGBA to RGB if necessary
                if image.mode == 'RGBA':
                    image = image.convert('RGB')
                
                # Compress image
                output_buffer = io.BytesIO()
                image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
                compressed_data = output_buffer.getvalue()
                
                # Replace image with compressed version
                page.replace_image(xref, compressed_data)
            except Exception:
                # Skip if image processing fails
                continue
    
    # Save with compression
    doc.save(output_path,
             garbage=4,  # Maximum garbage collection
             deflate=True,  # Compress streams
             clean=True)  # Clean unused elements
    doc.close()

def get_file_size(file_path, unit='MB'):
    """
    Get the size of a file in specified unit.
    
    Args:
        file_path (str): Path to the file
        unit (str): Unit of size ('B', 'KB', 'MB', 'GB')
    
    Returns:
        float: File size in specified unit
    """
    size_bytes = os.path.getsize(file_path)
    
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 * 1024,
        'GB': 1024 * 1024 * 1024
    }
    
    return size_bytes / units.get(unit.upper(), 1) 