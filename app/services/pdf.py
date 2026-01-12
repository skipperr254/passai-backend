import PyPDF2
from io import BytesIO

def extract_pdf_text(bytes_data: bytes) -> str:
    reader = PyPDF2.PdfReader(BytesIO(bytes_data))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    # Remove null bytes that PostgreSQL cannot store
    text = text.replace('\x00', '')
    return text.strip()