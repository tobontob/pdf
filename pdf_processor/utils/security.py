import fitz  # PyMuPDF

def encrypt_pdf(input_path, output_path, user_password, owner_password=None):
    """
    Encrypt a PDF file with passwords.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the encrypted PDF
        user_password (str): Password for opening the PDF
        owner_password (str, optional): Password for full permissions
    """
    doc = fitz.open(input_path)
    
    # If owner_password is not provided, use user_password
    if not owner_password:
        owner_password = user_password
    
    # Set encryption
    encrypt_dict = {
        "user_pw": user_password,
        "owner_pw": owner_password,
        "permission": int(
            fitz.PDF_PERM_PRINT |  # Allow printing
            fitz.PDF_PERM_COPY |   # Allow copying text/images
            fitz.PDF_PERM_ANNOTATE # Allow annotations
        )
    }
    doc.save(output_path, encryption=encrypt_dict)
    doc.close()

def decrypt_pdf(input_path, output_path, password):
    """
    Decrypt a PDF file.
    
    Args:
        input_path (str): Path to the encrypted PDF file
        output_path (str): Path to save the decrypted PDF
        password (str): Password to decrypt the PDF
    """
    doc = fitz.open(input_path)
    
    # Try to authenticate with the password
    if doc.authenticate(password):
        # Save without encryption
        doc.save(output_path, encryption=None)
    
    doc.close()

def set_pdf_permissions(input_path, output_path, password, permissions):
    """
    Set permissions for a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the modified PDF
        password (str): Owner password to set permissions
        permissions (dict): Dictionary of permission flags:
            - print (bool): Allow printing
            - copy (bool): Allow copying text/images
            - modify (bool): Allow modifying content
            - annotate (bool): Allow annotations
            - form_fill (bool): Allow filling forms
            - extract (bool): Allow extracting content
    """
    doc = fitz.open(input_path)
    
    # Build permission flags
    perm = 0
    if permissions.get('print', True):
        perm |= fitz.PDF_PERM_PRINT
    if permissions.get('copy', True):
        perm |= fitz.PDF_PERM_COPY
    if permissions.get('modify', True):
        perm |= fitz.PDF_PERM_MODIFY
    if permissions.get('annotate', True):
        perm |= fitz.PDF_PERM_ANNOTATE
    if permissions.get('form_fill', True):
        perm |= fitz.PDF_PERM_FORM
    if permissions.get('extract', True):
        perm |= fitz.PDF_PERM_EXTRACT
    
    # Set encryption with permissions
    encrypt_dict = {
        "owner_pw": password,
        "permission": perm
    }
    doc.save(output_path, encryption=encrypt_dict)
    doc.close() 