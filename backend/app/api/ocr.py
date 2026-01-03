"""
OCR API endpoints for text extraction and translation from manga images.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models import Page, Chapter, Manga, User
from app.api.auth import get_current_user
from app.services.ocr_service import ocr_service

router = APIRouter()


class OCRRequest(BaseModel):
    """Request model for OCR operations"""
    source_language: str = Field(default="Japanese", description="Source language of the text")
    target_language: Optional[str] = Field(default=None, description="Target language for translation")
    custom_prompt: Optional[str] = Field(default=None, description="Custom prompt for the OCR model")


class OCRResponse(BaseModel):
    """Response model for OCR operations"""
    success: bool
    text: Optional[str] = None
    original_text: Optional[str] = None
    translated_text: Optional[str] = None
    source_language: str
    target_language: Optional[str] = None
    model: str
    error: Optional[str] = None


@router.get("/status")
async def get_ocr_status():
    """Get OCR service status"""
    return {
        "enabled": ocr_service.enabled,
        "available": ocr_service.is_available(),
        "model": ocr_service.model if ocr_service.enabled else None,
        "base_url": ocr_service.base_url if ocr_service.enabled else None
    }


@router.post("/{manga_id}/{chapter_id}/{page_id}/extract", response_model=OCRResponse)
async def extract_text_from_page(
    manga_id: int,
    chapter_id: int,
    page_id: int,
    ocr_request: OCRRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Extract text from a manga page image using OCR.
    
    This endpoint uses Ollama with Qwen2.5-VL model to extract text from the image.
    Supports multilingual text extraction, particularly strong with Japanese and other Asian scripts.
    """
    if not ocr_service.enabled:
        raise HTTPException(status_code=503, detail="OCR service is not enabled")
    
    if not ocr_service.is_available():
        raise HTTPException(status_code=503, detail="OCR service is not available")
    
    # Verify page exists and belongs to the correct manga/chapter
    result = await db.execute(
        select(Page, Chapter, Manga)
        .join(Chapter, Page.chapter_id == Chapter.id)
        .join(Manga, Chapter.manga_id == Manga.id)
        .where(
            Page.id == page_id,
            Chapter.id == chapter_id,
            Manga.id == manga_id
        )
    )
    
    page_data = result.first()
    if not page_data:
        raise HTTPException(status_code=404, detail="Page not found")
    
    page, chapter, manga = page_data
    
    # Extract text from the page image
    result = await ocr_service.extract_text(
        image_path=page.file_path,
        source_language=ocr_request.source_language,
        prompt=ocr_request.custom_prompt
    )
    
    return OCRResponse(
        success=result["success"],
        text=result.get("text"),
        source_language=result["source_language"],
        model=result["model"],
        error=result.get("error")
    )


@router.post("/{manga_id}/{chapter_id}/{page_id}/translate", response_model=OCRResponse)
async def translate_text_from_page(
    manga_id: int,
    chapter_id: int,
    page_id: int,
    ocr_request: OCRRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Extract and translate text from a manga page image using OCR.
    
    This endpoint uses Ollama with Qwen2.5-VL model to extract and translate text from the image.
    It can read Japanese text and translate it to English (or other specified languages).
    The model handles around 85-90% accuracy with Japanese text in images.
    """
    if not ocr_service.enabled:
        raise HTTPException(status_code=503, detail="OCR service is not enabled")
    
    if not ocr_service.is_available():
        raise HTTPException(status_code=503, detail="OCR service is not available")
    
    # Verify page exists and belongs to the correct manga/chapter
    result = await db.execute(
        select(Page, Chapter, Manga)
        .join(Chapter, Page.chapter_id == Chapter.id)
        .join(Manga, Chapter.manga_id == Manga.id)
        .where(
            Page.id == page_id,
            Chapter.id == chapter_id,
            Manga.id == manga_id
        )
    )
    
    page_data = result.first()
    if not page_data:
        raise HTTPException(status_code=404, detail="Page not found")
    
    page, chapter, manga = page_data
    
    # Default target language to English if not specified
    target_language = ocr_request.target_language or "English"
    
    # Extract and translate text from the page image
    result = await ocr_service.extract_and_translate(
        image_path=page.file_path,
        source_language=ocr_request.source_language,
        target_language=target_language,
        prompt=ocr_request.custom_prompt
    )
    
    return OCRResponse(
        success=result["success"],
        original_text=result.get("original_text"),
        translated_text=result.get("translated_text"),
        source_language=result["source_language"],
        target_language=result.get("target_language"),
        model=result["model"],
        error=result.get("error")
    )
