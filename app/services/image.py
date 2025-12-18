"""
Image OCR Text Extraction
Extracts text from images using Tesseract OCR
"""
from PIL import Image
from io import BytesIO
import pytesseract

def extract_image_text(bytes_data: bytes) -> str:
    """
    Extracts text from an image using OCR
    
    Args:
        bytes_data: Image file bytes
        
    Returns:
        Extracted text string
    """
    try:
        image = Image.open(BytesIO(bytes_data))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print(f"Image OCR error: {e}")
        return ""
