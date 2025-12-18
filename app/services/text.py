"""
Text File Content Extraction
Extracts content from plain text files
"""

def extract_text_content(bytes_data: bytes) -> str:
    """
    Extracts text from a plain text file
    
    Args:
        bytes_data: Text file bytes
        
    Returns:
        File content as string
    """
    try:
        # Try UTF-8 first
        return bytes_data.decode('utf-8').strip()
    except UnicodeDecodeError:
        # Fallback to latin-1 if UTF-8 fails
        try:
            return bytes_data.decode('latin-1').strip()
        except Exception as e:
            print(f"Text extraction error: {e}")
            return ""
