"""
Process Material API Endpoint
Handles text extraction from files already uploaded to Supabase Storage
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.security import get_current_user
from app.repositories.material_repository import material_repository
from app.services.pdf import extract_pdf_text
from app.services.docx import extract_docx_text
from app.services.pptx import extract_pptx_text
from app.services.image import extract_image_text
from app.services.text import extract_text_content
from app.utils.supabase import supabase
from app.core.constants import MIN_TEXT_LENGTH, STORAGE_BUCKET

router = APIRouter()


class ProcessMaterialRequest(BaseModel):
    """Request body for processing a material"""
    material_id: str
    storage_path: str


class ProcessMaterialResponse(BaseModel):
    """Response for successful material processing"""
    success: bool
    material_id: str
    text_length: int
    file_type: str
    processing_time: int
    message: str


@router.post("/process-material", response_model=ProcessMaterialResponse)
async def process_material(
    request: ProcessMaterialRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Process a material that was already uploaded to Supabase storage
    
    Flow:
    1. Validate material exists and belongs to user
    2. Update status to 'processing'
    3. Download file from Supabase Storage
    4. Extract text based on file type
    5. Save text to database with 'ready' status
    6. Return success response
    
    Frontend subscribes to database changes via Supabase Realtime for status updates.
    """
    start_time = datetime.now()
    
    try:
        print(f"🔧 Processing material: {request.material_id}")
        
        # 1. Fetch material record and verify ownership
        material = material_repository.get_by_id(request.material_id, user_id)
        
        if not material:
            raise HTTPException(
                status_code=404, 
                detail="Material not found or access denied"
            )
        
        print(f"📄 Material details: {material['file_name']} ({material['file_type']})")
        
        # 2. Update status to 'processing'
        material_repository.update_status(request.material_id, "processing")
        
        # 3. Download file from Supabase Storage
        try:
            response = supabase.storage.from_(STORAGE_BUCKET).download(request.storage_path)
            file_bytes = response
        except Exception as e:
            error_msg = f"Failed to download file from storage: {str(e)}"
            material_repository.update_status(request.material_id, "failed", error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # 4. Extract text based on file type
        try:
            extracted_text = await extract_text_by_type(file_bytes, material['file_type'])
        except Exception as e:
            error_msg = f"Failed to extract text: {str(e)}"
            material_repository.update_status(request.material_id, "failed", error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # 5. Validate extracted text
        if not extracted_text or len(extracted_text.strip()) < MIN_TEXT_LENGTH:
            error_msg = f"Extracted text is too short (minimum {MIN_TEXT_LENGTH} characters). File may be empty or corrupted."
            material_repository.update_status(request.material_id, "failed", error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 6. Save text content and update status to 'ready'
        from app.models.material import MaterialUpdate
        material_repository.update(
            request.material_id,
            MaterialUpdate(
                text_content=extracted_text,
                processing_status="ready",
                error_message=None
            )
        )
        
        # 7. Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        print(f"✅ Material processed successfully: {len(extracted_text)} characters in {processing_time}ms")
        
        return ProcessMaterialResponse(
            success=True,
            material_id=request.material_id,
            text_length=len(extracted_text),
            file_type=material['file_type'],
            processing_time=processing_time,
            message="Material processed successfully. Text extracted and saved."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Process material error: {e}")
        material_repository.update_status(
            request.material_id, 
            "failed", 
            f"Unexpected error: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process material: {str(e)}"
        )


async def extract_text_by_type(file_bytes: bytes, file_type: str) -> str:
    """
    Extract text from file based on type
    
    Args:
        file_bytes: File content as bytes
        file_type: File type (pdf, docx, pptx, image, text)
        
    Returns:
        Extracted text content
        
    Raises:
        ValueError: If file type is unsupported
        Exception: If extraction fails
    """
    print(f"📝 Extracting text from {file_type} file...")
    
    if file_type == "pdf":
        return extract_pdf_text(file_bytes)
    elif file_type == "docx":
        return extract_docx_text(file_bytes)
    elif file_type == "pptx":
        return extract_pptx_text(file_bytes)
    elif file_type == "image":
        return extract_image_text(file_bytes)
    elif file_type == "text":
        return extract_text_content(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
