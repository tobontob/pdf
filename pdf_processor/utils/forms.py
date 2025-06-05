from PyPDF2 import PdfReader, PdfWriter
import json
import fitz  # PyMuPDF

def add_form_fields(input_path, output_path, fields):
    """
    Add form fields to a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the modified PDF
        fields (list): List of field dictionaries with properties:
            - name (str): Field name
            - type (str): Field type ('text', 'checkbox', 'radio', 'combo', 'list')
            - rect (list): Field rectangle [x0, y0, x1, y1]
            - value (str/bool): Default value
            - options (list): Options for combo/list fields
    """
    doc = fitz.open(input_path)
    
    for field in fields:
        page = doc[0]  # Add to first page for now
        
        # Create field widget
        widget = None
        if field['type'] == 'text':
            widget = page.add_text_field(
                rect=fitz.Rect(field['rect']),
                name=field['name'],
                value=field.get('value', '')
            )
        elif field['type'] == 'checkbox':
            widget = page.add_checkbox_field(
                rect=fitz.Rect(field['rect']),
                name=field['name'],
                checked=field.get('value', False)
            )
        elif field['type'] == 'radio':
            widget = page.add_radio_button_field(
                rect=fitz.Rect(field['rect']),
                name=field['name'],
                checked=field.get('value', False)
            )
        elif field['type'] in ('combo', 'list'):
            widget = page.add_combobox_field(
                rect=fitz.Rect(field['rect']),
                name=field['name'],
                values=field.get('options', []),
                value=field.get('value', '')
            )
        
        if widget:
            # Set common properties
            widget.update({
                'text_color': (0, 0, 0),  # Black text
                'border_color': (0, 0, 0),  # Black border
                'field_type': field['type']
            })
    
    doc.save(output_path)
    doc.close()

def fill_form_fields(input_path, output_path, field_values):
    """
    Fill form fields in a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the filled PDF
        field_values (dict): Dictionary of field names and values
    """
    doc = fitz.open(input_path)
    
    # Get form fields
    fields = doc.get_form_text_fields()
    
    # Fill each field
    for name, value in field_values.items():
        if name in fields:
            doc.set_form_text_field(name, value)
    
    doc.save(output_path)
    doc.close()

def extract_form_fields(input_path):
    """
    Extract form fields and their values from a PDF file.
    
    Args:
        input_path (str): Path to the input PDF file
    
    Returns:
        dict: Dictionary of field names and their current values
    """
    doc = fitz.open(input_path)
    
    # Get all form fields
    fields = {}
    for widget in doc.get_form_widget_values():
        fields[widget.field_name] = {
            'type': widget.field_type_string,
            'value': widget.field_value,
            'rect': widget.rect
        }
    
    doc.close()
    return fields

def flatten_form_fields(input_path, output_path):
    """
    Flatten form fields in a PDF file (make them non-editable).
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the flattened PDF
    """
    doc = fitz.open(input_path)
    
    # Get form fields
    fields = doc.get_form_text_fields()
    
    # Convert each field to text
    for page in doc:
        for widget in page.widgets():
            field_name = widget.field_name
            if field_name in fields:
                # Get field value and position
                value = fields[field_name]
                rect = widget.rect
                
                # Add text annotation
                page.insert_text(
                    (rect.x0, rect.y0),
                    str(value),
                    fontsize=12,
                    color=(0, 0, 0)  # Black text
                )
                
                # Remove the form field
                widget.delete()
    
    doc.save(output_path)
    doc.close() 