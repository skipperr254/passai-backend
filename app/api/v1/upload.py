from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import uuid

from utils.supabase import supabase
from services.pdf import extract_pdf_text
from services.docx import extract_docx_text
from services.pptx import extract_pptx_text
from core.security import get_current_user

router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx"
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user_id: str = Depends(get_current_user)):
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    file_bytes = await file.read()

    # Validate file size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the maximum limit of 10 MB.")
    
    # Generate a unique filename
    extension = ALLOWED_TYPES[file.content_type]
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.{extension}"

    # Upload to Supabase Storage bucket
    try:
        upload_response = supabase.storage.from_("documents").upload(filename, file_bytes, {"content-type": file.content_type})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload file.")
    
    # Extract text based on file type
    extracted_text = ""
    if extension == "pdf":
        extracted_text = extract_pdf_text(file_bytes)
    elif extension == "docx":
        extracted_text = extract_docx_text(file_bytes)
    elif extension == "pptx":
        extracted_text = extract_pptx_text(file_bytes)
    
     # 4. Get public URL
    public_url = supabase.storage.from_("documents").get_public_url(filename)

    # Insert DB record
    try:
        db_response = supabase.table("documents").insert({
            "id": file_id,
            "filename": filename,
            "original_filename": file.filename,
            "content_type": file.content_type,
            "url": public_url,
            "text_content": extracted_text,
            "user_id": user_id,
            "size": len(file_bytes)
        }).execute()
    except Exception as e:
        # We might want to delete the uploaded file from storage if DB insert fails
        supabase.storage.from_("documents").remove([filename]) # Delete the uploaded file
        print(f"Database insert error: {str(e)}")  # Log the actual error
        raise HTTPException(status_code=500, detail=f"Failed to save file metadata: {str(e)}")

    return {
        "id": file_id,
        "filename": filename,
        "original_filename": file.filename, # Might want to store original filename for better UX
        "content_type": file.content_type,
        "url": public_url
    }