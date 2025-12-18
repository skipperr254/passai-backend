from docx import Document
from io import BytesIO

def extract_docx_text(bytes_data: bytes) -> str:
    document = Document(BytesIO(bytes_data))
    text = ""
    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"
    return text.strip()