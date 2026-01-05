"""
Pydantic models for material-related data structures
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MaterialBase(BaseModel):
    """Base material fields"""
    file_name: str
    file_type: str
    subject_id: str


class MaterialCreate(MaterialBase):
    """Material creation schema"""
    id: str
    user_id: str
    file_size: int
    storage_path: str
    text_content: Optional[str] = None
    processing_status: str
    error_message: Optional[str] = None
    thumbnail_url: Optional[str] = None


class MaterialUpdate(BaseModel):
    """Material update schema"""
    text_content: Optional[str] = None
    processing_status: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: Optional[str] = None


class Material(MaterialBase):
    """Complete material model"""
    id: str
    user_id: str
    file_size: int
    storage_path: str
    text_content: Optional[str] = None
    processing_status: str
    error_message: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MaterialStatus(BaseModel):
    """Material processing status response"""
    material_id: str
    file_name: str
    processing_status: str
    error_message: Optional[str] = None
    chunk_count: int = 0
    created_at: str
    updated_at: str
    is_ready_for_rag: bool
