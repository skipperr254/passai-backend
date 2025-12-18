from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.health import router as health_router
from api.v1.upload import router as upload_router
from core.config import settings

app = FastAPI(title="Document Processing API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")