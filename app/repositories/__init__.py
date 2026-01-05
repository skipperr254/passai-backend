"""
Repositories package - Data access layer for database operations
"""
from app.repositories.material_repository import material_repository, MaterialRepository

__all__ = [
    "material_repository",
    "MaterialRepository",
]
