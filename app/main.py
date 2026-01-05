from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.process_material import router as process_material_router
from app.core.config import settings

app = FastAPI(
    title="PassAI Material Processing API",
    version="2.0.0",
    description="Text extraction service for study materials"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(process_material_router, prefix="/api/v1", tags=["Material Processing"])