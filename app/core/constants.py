"""
Application-wide constants for file processing and storage
"""

# Supported file types matching frontend
ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "image/jpeg": "image",
    "image/jpg": "image",
    "image/png": "image",
    "text/plain": "text",
}

# File size limits
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10 MB
FREE_TIER_STORAGE_LIMIT = 500 * 1024 * 1024  # 500 MB

# Text extraction validation
MIN_TEXT_LENGTH = 50  # Minimum characters for valid extraction

# Supabase storage bucket name
STORAGE_BUCKET = "materials"

# Processing statuses
class ProcessingStatus:
    """Material processing status constants"""
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
