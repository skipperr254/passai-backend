from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List
import os

# Get the project root directory (two levels up from this file)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    # Supabase configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    
    # CORS configuration
    CORS_ORIGINS: str = "*"  # Comma-separated origins for production
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # Tesseract configuration (for OCR)
    TESSERACT_CMD: str = ""  # Path to tesseract executable if not in PATH
    
    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    def validate_settings(self) -> None:
        """Validate that required settings are present"""
        if not self.SUPABASE_URL:
            raise ValueError("SUPABASE_URL is required")
        if not self.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY is required")
        if not self.SUPABASE_JWT_SECRET:
            raise ValueError("SUPABASE_JWT_SECRET is required")

    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = True

settings = Settings()

# Validate on startup
try:
    settings.validate_settings()
except ValueError as e:
    print(f"⚠️  Configuration warning: {e}")

# Configure Tesseract if path is provided
if settings.TESSERACT_CMD:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD