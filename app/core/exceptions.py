"""
Custom exception classes for better error handling
"""
from fastapi import HTTPException

class MaterialProcessingError(Exception):
    """Base exception for material processing errors"""
    pass

class TextExtractionError(MaterialProcessingError):
    """Raised when text extraction fails"""
    pass

class StorageQuotaExceeded(MaterialProcessingError):
    """Raised when user storage quota is exceeded"""
    pass

class UnsupportedFileType(MaterialProcessingError):
    """Raised when file type is not supported"""
    pass

class FileSizeExceeded(MaterialProcessingError):
    """Raised when file size exceeds limit"""
    pass

def create_http_exception(status_code: int, detail: str, **kwargs) -> HTTPException:
    """
    Create a standardized HTTP exception
    
    Args:
        status_code: HTTP status code
        detail: Error message
        **kwargs: Additional fields to include in response
        
    Returns:
        HTTPException with consistent format
    """
    return HTTPException(
        status_code=status_code,
        detail=detail,
        headers=kwargs
    )
