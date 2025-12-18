from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from typing import Optional
import uuid
from datetime import datetime

from app.utils.supabase import supabase
from app.services.pdf import extract_pdf_text
from app.services.docx import extract_docx_text
from app.services.pptx import extract_pptx_text
from app.services.image import extract_image_text
from app.services.text import extract_text_content
from app.core.security import get_current_user

router = APIRouter()

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

# File size limits matching frontend
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10 MB
FREE_TIER_STORAGE_LIMIT = 500 * 1024 * 1024  # 500 MB
MIN_TEXT_LENGTH = 50  # Minimum characters for valid extraction

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    subject_id: str = Form(...),
    user_id: str = Depends(get_current_user)
):
    """
    Upload and process a study material file
    
    Process:
    1. Validate file type and size
    2. Check user storage quota
    3. Upload to Supabase storage
    4. Extract text content
    5. Save metadata to database
    
    Returns material record with processing status
    """
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file.content_type}. Supported types: PDF, DOCX, PPTX, JPG, PNG, TXT"
        )

    file_bytes = await file.read()
    file_type = ALLOWED_TYPES[file.content_type]
    
    # Validate file size based on type
    max_size = MAX_IMAGE_SIZE if file_type == "image" else MAX_DOCUMENT_SIZE
    if len(file_bytes) > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=400, 
            detail=f"File size exceeds {max_size_mb}MB limit for {file_type} files"
        )
    
    # Check user storage quota
    try:
        storage_response = supabase.from_("study_materials").select("file_size").eq("user_id", user_id).execute()
        total_used: int = sum(item.get("file_size", 0) if isinstance(item, dict) else 0 for item in (storage_response.data or []))  # type: ignore
        
        if total_used + len(file_bytes) > FREE_TIER_STORAGE_LIMIT:
            used_mb = total_used / (1024 * 1024)
            limit_mb = FREE_TIER_STORAGE_LIMIT / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"Storage limit exceeded. Used: {used_mb:.1f}MB / {limit_mb:.1f}MB"
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Storage check error: {e}")
        # Continue even if storage check fails
    
    # Generate storage path: {user_id}/{subject_id}/{unique_filename}
    file_id = str(uuid.uuid4())
    safe_filename = (file.filename or "unknown").replace(" ", "_")
    storage_path = f"{user_id}/{subject_id}/{file_id}_{safe_filename}"

    # Upload to Supabase Storage bucket
    try:
        upload_response = supabase.storage.from_("materials").upload(
            storage_path, 
            file_bytes, 
            {"content-type": file.content_type}
        )
    except Exception as e:
        print(f"Storage upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file to storage")
    
    # Extract text based on file type
    extracted_text = ""
    processing_status = "processing"
    error_message = None
    
    try:
        if file_type == "pdf":
            extracted_text = extract_pdf_text(file_bytes)
        elif file_type == "docx":
            extracted_text = extract_docx_text(file_bytes)
        elif file_type == "pptx":
            extracted_text = extract_pptx_text(file_bytes)
        elif file_type == "image":
            extracted_text = extract_image_text(file_bytes)
        elif file_type == "text":
            extracted_text = extract_text_content(file_bytes)
        
        # Validate extracted text
        if not extracted_text or len(extracted_text.strip()) < MIN_TEXT_LENGTH:
            processing_status = "failed"
            error_message = f"Could not extract sufficient text (minimum {MIN_TEXT_LENGTH} characters)"
        else:
            processing_status = "ready"
            
    except Exception as e:
        print(f"Text extraction error: {e}")
        processing_status = "failed"
        error_message = f"Text extraction failed: {str(e)}"

    # Get public URL (for reference, even though bucket may be private)
    public_url_data = supabase.storage.from_("materials").get_public_url(storage_path)
    public_url = public_url_data if isinstance(public_url_data, str) else public_url_data.get("publicUrl", "")

    # Insert DB record into study_materials table
    try:
        db_response = supabase.table("study_materials").insert({
            "id": file_id,
            "user_id": user_id,
            "subject_id": subject_id,
            "file_name": file.filename,
            "file_type": file_type,
            "file_size": len(file_bytes),
            "storage_path": storage_path,
            "text_content": extracted_text if extracted_text else None,
            "processing_status": processing_status,
            "error_message": error_message,
            "thumbnail_url": None,  # Can be generated later
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        # Rollback: delete the uploaded file from storage if DB insert fails
        try:
            supabase.storage.from_("materials").remove([storage_path])
        except:
            pass
        print(f"Database insert error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save file metadata: {str(e)}")

    return {
        "success": True,
        "material": {
            "id": file_id,
            "file_name": file.filename,
            "file_type": file_type,
            "file_size": len(file_bytes),
            "storage_path": storage_path,
            "processing_status": processing_status,
            "error_message": error_message,
            "text_content": extracted_text[:500] + "..." if extracted_text and len(extracted_text) > 500 else extracted_text,
            "created_at": datetime.utcnow().isoformat(),
        }
    }


@router.post("/batch-upload")
async def batch_upload_files(
    files: list[UploadFile] = File(...),
    subject_id: str = Form(...),
    user_id: str = Depends(get_current_user)
):
    """
    Upload multiple files at once (alternative to direct Supabase upload)
    
    Note: For better bandwidth efficiency, consider uploading directly to 
    Supabase and using /batch-process instead.
    
    Returns results for each file
    """
    if len(files) > MAX_FILES_PER_UPLOAD:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_FILES_PER_UPLOAD} files allowed per batch"
        )
    
    results = []
    
    for file in files:
        try:
            # Reuse single upload logic
            result = await upload_file(file, subject_id, user_id)
            results.append({
                "file_name": file.filename,
                "success": True,
                "material": result["material"]
            })
        except HTTPException as e:
            results.append({
                "file_name": file.filename,
                "success": False,
                "error": e.detail
            })
        except Exception as e:
            results.append({
                "file_name": file.filename,
                "success": False,
                "error": str(e)
            })
    
    successful = sum(1 for r in results if r.get("success"))
    
    return {
        "total": len(files),
        "successful": successful,
        "failed": len(files) - successful,
        "results": results
    }


# Add constant at module level
MAX_FILES_PER_UPLOAD = 10


@router.post("/process-material")
async def process_material_by_path(
    material_id: str = Form(...),
    storage_path: str = Form(...),
    file_type: str = Form(...),
    user_id: str = Depends(get_current_user)
):
    """
    Process a material that was already uploaded to Supabase storage
    
    This endpoint is for the recommended architecture where:
    1. Frontend uploads file directly to Supabase storage
    2. Frontend creates DB record with processing_status='pending'
    3. Frontend calls this endpoint with storage path
    4. Backend downloads, extracts text, updates DB
    
    This reduces bandwidth costs on the backend server.
    """
    try:
        # Verify the material belongs to the user
        material_check = supabase.table("study_materials").select("user_id, processing_status").eq("id", material_id).single().execute()
        
        if not material_check.data:
            raise HTTPException(status_code=404, detail="Material not found")
        
        material_data = material_check.data if isinstance(material_check.data, dict) else {}
        if material_data.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized to process this material")
        
        if material_data.get("processing_status") == "ready":
            raise HTTPException(status_code=400, detail="Material already processed")
        
        # Update status to processing
        supabase.table("study_materials").update({
            "processing_status": "processing",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", material_id).execute()
        
        # Download file from storage
        try:
            download_response = supabase.storage.from_("materials").download(storage_path)
            file_bytes = download_response
        except Exception as e:
            print(f"Storage download error: {e}")
            supabase.table("study_materials").update({
                "processing_status": "failed",
                "error_message": f"Failed to download file: {str(e)}",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", material_id).execute()
            raise HTTPException(status_code=500, detail="Failed to download file from storage")
        
        # Extract text based on file type
        extracted_text = ""
        processing_status = "processing"
        error_message = None
        
        try:
            if file_type == "pdf":
                extracted_text = extract_pdf_text(file_bytes)
            elif file_type == "docx":
                extracted_text = extract_docx_text(file_bytes)
            elif file_type == "pptx":
                extracted_text = extract_pptx_text(file_bytes)
            elif file_type == "image":
                extracted_text = extract_image_text(file_bytes)
            elif file_type == "text":
                extracted_text = extract_text_content(file_bytes)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Validate extracted text
            if not extracted_text or len(extracted_text.strip()) < MIN_TEXT_LENGTH:
                processing_status = "failed"
                error_message = f"Could not extract sufficient text (minimum {MIN_TEXT_LENGTH} characters)"
            else:
                processing_status = "ready"
                
        except Exception as e:
            print(f"Text extraction error: {e}")
            processing_status = "failed"
            error_message = f"Text extraction failed: {str(e)}"
        
        # Update DB with extracted text
        update_data = {
            "text_content": extracted_text if extracted_text else None,
            "processing_status": processing_status,
            "error_message": error_message,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("study_materials").update(update_data).eq("id", material_id).execute()
        
        return {
            "success": processing_status == "ready",
            "material_id": material_id,
            "processing_status": processing_status,
            "error_message": error_message,
            "text_length": len(extracted_text) if extracted_text else 0,
            "text_preview": extracted_text[:200] + "..." if extracted_text and len(extracted_text) > 200 else extracted_text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Process material error: {e}")
        # Try to update status to failed
        try:
            supabase.table("study_materials").update({
                "processing_status": "failed",
                "error_message": str(e),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", material_id).execute()
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/storage-usage")
async def get_storage_usage(user_id: str = Depends(get_current_user)):
    """
    Get user's current storage usage and limit
    """
    try:
        storage_response = supabase.from_("study_materials").select("file_size").eq("user_id", user_id).execute()
        total_used: int = sum(item.get("file_size", 0) if isinstance(item, dict) else 0 for item in (storage_response.data or []))  # type: ignore
        
        return {
            "used": total_used,
            "limit": FREE_TIER_STORAGE_LIMIT,
            "used_mb": round(total_used / (1024 * 1024), 2),
            "limit_mb": round(FREE_TIER_STORAGE_LIMIT / (1024 * 1024), 2),
            "percentage": round((total_used / FREE_TIER_STORAGE_LIMIT) * 100, 1),
            "available": FREE_TIER_STORAGE_LIMIT - total_used,
        }
    except Exception as e:
        print(f"Storage usage error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch storage usage")


@router.post("/batch-process")
async def batch_process_materials(
    material_ids: list[str] = Form(...),
    user_id: str = Depends(get_current_user)
):
    """
    Process multiple materials that were uploaded to storage
    
    Returns status for each material
    """
    results = []
    
    for material_id in material_ids:
        try:
            # Get material info
            material = supabase.table("study_materials").select("*").eq("id", material_id).single().execute()
            
            if not material.data:
                results.append({
                    "material_id": material_id,
                    "success": False,
                    "error": "Material not found"
                })
                continue
            
            material_data = material.data if isinstance(material.data, dict) else {}
            if material_data.get("user_id") != user_id:
                results.append({
                    "material_id": material_id,
                    "success": False,
                    "error": "Unauthorized"
                })
                continue
            
            # Update to processing
            supabase.table("study_materials").update({
                "processing_status": "processing",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", material_id).execute()
            
            # Download and process
            try:
                storage_path = str(material_data.get("storage_path", ""))
                download_response = supabase.storage.from_("materials").download(storage_path)
                file_bytes = download_response
                
                # Extract text
                extracted_text = ""
                file_type = str(material_data.get("file_type", ""))
                
                if file_type == "pdf":
                    extracted_text = extract_pdf_text(file_bytes)
                elif file_type == "docx":
                    extracted_text = extract_docx_text(file_bytes)
                elif file_type == "pptx":
                    extracted_text = extract_pptx_text(file_bytes)
                elif file_type == "image":
                    extracted_text = extract_image_text(file_bytes)
                elif file_type == "text":
                    extracted_text = extract_text_content(file_bytes)
                
                # Validate and update
                if extracted_text and len(extracted_text.strip()) >= MIN_TEXT_LENGTH:
                    supabase.table("study_materials").update({
                        "text_content": extracted_text,
                        "processing_status": "ready",
                        "error_message": None,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", material_id).execute()
                    
                    results.append({
                        "material_id": material_id,
                        "success": True,
                        "processing_status": "ready",
                        "text_length": len(extracted_text)
                    })
                else:
                    supabase.table("study_materials").update({
                        "processing_status": "failed",
                        "error_message": "Insufficient text extracted",
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", material_id).execute()
                    
                    results.append({
                        "material_id": material_id,
                        "success": False,
                        "error": "Insufficient text extracted"
                    })
                    
            except Exception as e:
                supabase.table("study_materials").update({
                    "processing_status": "failed",
                    "error_message": str(e),
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", material_id).execute()
                
                results.append({
                    "material_id": material_id,
                    "success": False,
                    "error": str(e)
                })
                
        except Exception as e:
            results.append({
                "material_id": material_id,
                "success": False,
                "error": str(e)
            })
    
    successful = sum(1 for r in results if r.get("success"))
    
    return {
        "total": len(material_ids),
        "successful": successful,
        "failed": len(material_ids) - successful,
        "results": results
    }