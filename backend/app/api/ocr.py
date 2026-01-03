from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.services.ocr import get_ocr_service
from app.services.translator import get_translator_service
from app.api.auth import get_current_user
from app.models import User
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class OcrRequest(BaseModel):
    """Request model for OCR processing"""
    manga_id: int = Field(..., description="Manga ID")
    chapter_id: int = Field(..., description="Chapter ID")
    page_id: int = Field(..., description="Page ID")
    x: int = Field(..., ge=0, description="X coordinate of selection box")
    y: int = Field(..., ge=0, description="Y coordinate of selection box")
    width: int = Field(..., gt=0, description="Width of selection box")
    height: int = Field(..., gt=0, description="Height of selection box")


class KanjiBreakdown(BaseModel):
    """Model for individual kanji breakdown"""
    kanji: str
    reading: str
    meaning: str


class OcrResponse(BaseModel):
    """Response model for OCR processing with translation"""
    original: str = Field(..., description="Original Japanese text from OCR")
    reading: str = Field(..., description="Hiragana/romaji reading")
    translation: str = Field(..., description="English translation")
    kanji_breakdown: list[KanjiBreakdown] = Field(default_factory=list, description="Breakdown of kanji characters")
    notes: Optional[str] = Field(None, description="Cultural notes or nuances")
    error: Optional[str] = Field(None, description="Error message if any")


@router.post("/process", response_model=OcrResponse)
async def process_ocr(
    request: OcrRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process a selected region of a manga page:
    1. Extract Japanese text using OCR
    2. Translate to English using Ollama
    3. Provide kanji breakdown and cultural notes
    """
    try:
        # Get the page from database to retrieve file_path
        # NOTE: This endpoint assumes all authenticated users have access to all manga.
        # If user-specific access control is added in the future, add permission checks here.
        from sqlalchemy import select
        from app.models import Page, Chapter, Manga
        
        result = await db.execute(
            select(Page, Chapter, Manga)
            .join(Chapter, Page.chapter_id == Chapter.id)
            .join(Manga, Chapter.manga_id == Manga.id)
            .where(
                Page.id == request.page_id,
                Chapter.id == request.chapter_id,
                Manga.id == request.manga_id
            )
        )
        
        page_data = result.first()
        if not page_data:
            raise HTTPException(
                status_code=404,
                detail="Page not found or IDs do not match"
            )
        
        page, chapter, manga = page_data
        image_path = page.file_path
        
        # Get OCR service
        ocr_service = get_ocr_service()
        
        # Extract text from the selected region
        logger.info(f"Processing OCR for region: ({request.x}, {request.y}, {request.width}, {request.height})")
        japanese_text = ocr_service.process_region(
            image_path,
            (request.x, request.y, request.width, request.height)
        )
        
        if not japanese_text or not japanese_text.strip():
            return OcrResponse(
                original="",
                reading="",
                translation="No text detected in the selected region",
                kanji_breakdown=[],
                notes="Try selecting a region with visible text",
                error=None
            )
        
        logger.info(f"OCR extracted text: {japanese_text}")
        
        # Translate using Ollama
        translator = get_translator_service()
        translation_result = translator.translate(japanese_text)
        
        # Parse kanji breakdown
        kanji_breakdown = []
        if "kanji_breakdown" in translation_result:
            for item in translation_result["kanji_breakdown"]:
                kanji_breakdown.append(KanjiBreakdown(
                    kanji=item.get("kanji", ""),
                    reading=item.get("reading", ""),
                    meaning=item.get("meaning", "")
                ))
        
        return OcrResponse(
            original=translation_result.get("original", japanese_text),
            reading=translation_result.get("reading", ""),
            translation=translation_result.get("translation", "Translation unavailable"),
            kanji_breakdown=kanji_breakdown,
            notes=translation_result.get("notes"),
            error=None
        )
        
    except RuntimeError as e:
        logger.error(f"OCR service error: {e}")
        raise HTTPException(
            status_code=503,
            detail="OCR service is not available. Please ensure manga-ocr is installed."
        )
    except Exception as e:
        logger.error(f"Error processing OCR request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process OCR request: {str(e)}"
        )
