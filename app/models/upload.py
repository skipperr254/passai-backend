"""
Pydantic models for upload-related data structures
"""
from pydantic import BaseModel
from typing import Optional, List


class UploadResponse(BaseModel):
    """Response for single file upload"""
    success: bool
    material: dict
    message: str


class BatchUploadResult(BaseModel):
    """Result for a single file in batch upload"""
    file_name: str
    success: bool
    material: Optional[dict] = None
    error: Optional[str] = None


class BatchUploadResponse(BaseModel):
    """Response for batch upload"""
    total: int
    successful: int
    failed: int
    results: List[BatchUploadResult]


class StorageUsage(BaseModel):
    """Storage usage information"""
    used: int
    limit: int
    used_mb: float
    limit_mb: float
    percentage: float
    available: int


class ProcessMaterialRequest(BaseModel):
    """Request to process material by path"""
    material_id: str
    storage_path: str
    file_type: str


class ProcessMaterialResponse(BaseModel):
    """Response for process material"""
    success: bool
    material_id: str
    processing_status: str
    error_message: Optional[str] = None
    text_length: int
    text_preview: Optional[str] = None
