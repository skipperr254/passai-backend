"""
Repository layer for material database operations
Handles all CRUD operations for study_materials table
"""
from typing import Optional, List, Dict, Any, cast
from datetime import datetime

from app.utils.supabase import supabase
from app.models.material import MaterialCreate, MaterialUpdate


class MaterialRepository:
    """Repository for material database operations"""
    
    def __init__(self):
        self.table = "study_materials"
    
    def create(self, material: MaterialCreate) -> Dict[str, Any]:
        """
        Create a new material record
        
        Args:
            material: Material data to insert
            
        Returns:
            Created material record
            
        Raises:
            Exception: If database operation fails
        """
        material_dict = material.model_dump()
        material_dict["created_at"] = datetime.utcnow().isoformat()
        material_dict["updated_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table(self.table).insert(material_dict).execute()
        return cast(Dict[str, Any], response.data[0]) if response.data else {}
    
    def get_by_id(self, material_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get material by ID, optionally filtered by user
        
        Args:
            material_id: Material ID
            user_id: Optional user ID to verify ownership
            
        Returns:
            Material record or None if not found
        """
        query = supabase.table(self.table).select("*").eq("id", material_id)
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        try:
            response = query.single().execute()
            return response.data if isinstance(response.data, dict) else None
        except Exception:
            return None
    
    def update(self, material_id: str, updates: MaterialUpdate) -> Dict[str, Any]:
        """
        Update material record
        
        Args:
            material_id: Material ID
            updates: Fields to update
            
        Returns:
            Updated material record
        """
        update_dict = updates.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table(self.table).update(update_dict).eq("id", material_id).execute()
        return cast(Dict[str, Any], response.data[0]) if response.data else {}
    
    def update_status(
        self, 
        material_id: str, 
        status: str, 
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update material processing status
        
        Args:
            material_id: Material ID
            status: New processing status
            error_message: Optional error message
            
        Returns:
            Updated material record
        """
        update_data = {
            "processing_status": status,
            "error_message": error_message,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table(self.table).update(update_data).eq("id", material_id).execute()
        return cast(Dict[str, Any], response.data[0]) if response.data else {}
    
    def get_storage_usage(self, user_id: str) -> int:
        """
        Calculate total storage used by user
        
        Args:
            user_id: User ID
            
        Returns:
            Total bytes used
        """
        response = supabase.table(self.table).select("file_size").eq("user_id", user_id).execute()
        
        total_used: int = sum(
            int(cast(dict, item).get("file_size", 0)) if isinstance(item, dict) else 0 
            for item in cast(List, response.data or [])
        )
        
        return total_used
    
    def delete(self, material_id: str, user_id: str) -> bool:
        """
        Delete material record
        
        Args:
            material_id: Material ID
            user_id: User ID for authorization
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            supabase.table(self.table).delete().eq("id", material_id).eq("user_id", user_id).execute()
            return True
        except Exception:
            return False
    
    def get_user_materials(self, user_id: str, subject_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all materials for a user, optionally filtered by subject
        
        Args:
            user_id: User ID
            subject_id: Optional subject ID filter
            
        Returns:
            List of material records
        """
        query = supabase.table(self.table).select("*").eq("user_id", user_id)
        
        if subject_id:
            query = query.eq("subject_id", subject_id)
        
        response = query.execute()
        return cast(List[Dict[str, Any]], response.data or [])


# Singleton instance
material_repository = MaterialRepository()
