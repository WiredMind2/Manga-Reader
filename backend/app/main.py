from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.api.auth import router as auth_router
from app.api.manga import router as manga_router
from app.api.progress import router as progress_router
from app.api.images import router as images_router
from app.api.preferences import router as preferences_router
from app.api.ocr import router as ocr_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Ensure cache directories exist
    os.makedirs(settings.IMAGE_CACHE_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)
    
    yield
    
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Manga Reader API",
    description="A modern manga reader API with user authentication and progress tracking",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(manga_router, prefix="/api/manga", tags=["Manga"])
app.include_router(progress_router, prefix="/api/progress", tags=["Progress"])
app.include_router(images_router, prefix="/api/images", tags=["Images"])
app.include_router(preferences_router, prefix="/api/preferences", tags=["User Preferences"])
app.include_router(ocr_router, prefix="/api/ocr", tags=["OCR & Translation"])

# Serve static files for covers and cached images
if os.path.exists(settings.IMAGE_CACHE_DIR):
    app.mount("/static", StaticFiles(directory=settings.IMAGE_CACHE_DIR), name="static")


@app.get("/")
async def root():
    return {"message": "Manga Reader API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)