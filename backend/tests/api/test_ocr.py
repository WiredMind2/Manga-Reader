import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import HTTPException

from app.api.ocr import process_ocr, OcrRequest


@pytest.mark.asyncio
async def test_process_ocr_success(mock_current_user, test_db, test_manga, test_chapter):
    """Test successful OCR processing"""
    # Get a page from the test chapter
    from sqlalchemy import select
    from app.models import Page
    
    result = await test_db.execute(
        select(Page).where(Page.chapter_id == test_chapter.id).limit(1)
    )
    page = result.scalar_one()
    
    # Mock OCR service
    mock_ocr_service = Mock()
    mock_ocr_service.process_region = Mock(return_value="こんにちは")
    
    # Mock translator service
    mock_translator_service = Mock()
    mock_translator_service.translate = Mock(return_value={
        "original": "こんにちは",
        "reading": "konnichiwa",
        "translation": "Hello",
        "kanji_breakdown": [],
        "notes": "Common greeting"
    })
    
    request = OcrRequest(
        manga_id=test_manga.id,
        chapter_id=test_chapter.id,
        page_id=page.id,
        x=100,
        y=100,
        width=200,
        height=50
    )
    
    with patch('app.api.ocr.get_ocr_service', return_value=mock_ocr_service), \
         patch('app.api.ocr.get_translator_service', return_value=mock_translator_service):
        
        result = await process_ocr(request, mock_current_user, test_db)
        
        assert result.original == "こんにちは"
        assert result.reading == "konnichiwa"
        assert result.translation == "Hello"
        assert result.notes == "Common greeting"
        mock_ocr_service.process_region.assert_called_once()


@pytest.mark.asyncio
async def test_process_ocr_page_not_found(mock_current_user, test_db, test_manga, test_chapter):
    """Test OCR with non-existent page"""
    request = OcrRequest(
        manga_id=test_manga.id,
        chapter_id=test_chapter.id,
        page_id=99999,  # Non-existent page
        x=100,
        y=100,
        width=200,
        height=50
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await process_ocr(request, mock_current_user, test_db)
    
    assert exc_info.value.status_code == 404
    assert "Page not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_process_ocr_no_text_detected(mock_current_user, test_db, test_manga, test_chapter):
    """Test OCR when no text is detected"""
    from sqlalchemy import select
    from app.models import Page
    
    result = await test_db.execute(
        select(Page).where(Page.chapter_id == test_chapter.id).limit(1)
    )
    page = result.scalar_one()
    
    mock_ocr_service = Mock()
    mock_ocr_service.process_region = Mock(return_value="")
    
    request = OcrRequest(
        manga_id=test_manga.id,
        chapter_id=test_chapter.id,
        page_id=page.id,
        x=100,
        y=100,
        width=200,
        height=50
    )
    
    with patch('app.api.ocr.get_ocr_service', return_value=mock_ocr_service):
        result = await process_ocr(request, mock_current_user, test_db)
        
        assert result.original == ""
        assert result.translation == "No text detected in the selected region"
        assert "Try selecting a region with visible text" in result.notes


@pytest.mark.asyncio
async def test_process_ocr_with_kanji_breakdown(mock_current_user, test_db, test_manga, test_chapter):
    """Test OCR with kanji breakdown"""
    from sqlalchemy import select
    from app.models import Page
    
    result = await test_db.execute(
        select(Page).where(Page.chapter_id == test_chapter.id).limit(1)
    )
    page = result.scalar_one()
    
    mock_ocr_service = Mock()
    mock_ocr_service.process_region = Mock(return_value="漫画")
    
    mock_translator_service = Mock()
    mock_translator_service.translate = Mock(return_value={
        "original": "漫画",
        "reading": "manga",
        "translation": "manga/comic",
        "kanji_breakdown": [
            {"kanji": "漫", "reading": "man", "meaning": "random, rambling"},
            {"kanji": "画", "reading": "ga", "meaning": "picture, drawing"}
        ],
        "notes": None
    })
    
    request = OcrRequest(
        manga_id=test_manga.id,
        chapter_id=test_chapter.id,
        page_id=page.id,
        x=50,
        y=50,
        width=100,
        height=30
    )
    
    with patch('app.api.ocr.get_ocr_service', return_value=mock_ocr_service), \
         patch('app.api.ocr.get_translator_service', return_value=mock_translator_service):
        
        result = await process_ocr(request, mock_current_user, test_db)
        
        assert result.original == "漫画"
        assert result.translation == "manga/comic"
        assert len(result.kanji_breakdown) == 2
        assert result.kanji_breakdown[0].kanji == "漫"
        assert result.kanji_breakdown[0].reading == "man"
        assert result.kanji_breakdown[1].kanji == "画"


@pytest.mark.asyncio
async def test_process_ocr_service_unavailable(mock_current_user, test_db, test_manga, test_chapter):
    """Test OCR when service is unavailable"""
    from sqlalchemy import select
    from app.models import Page
    
    result = await test_db.execute(
        select(Page).where(Page.chapter_id == test_chapter.id).limit(1)
    )
    page = result.scalar_one()
    
    mock_ocr_service = Mock()
    mock_ocr_service.process_region = Mock(side_effect=RuntimeError("OCR service not available"))
    
    request = OcrRequest(
        manga_id=test_manga.id,
        chapter_id=test_chapter.id,
        page_id=page.id,
        x=100,
        y=100,
        width=200,
        height=50
    )
    
    with patch('app.api.ocr.get_ocr_service', return_value=mock_ocr_service):
        with pytest.raises(HTTPException) as exc_info:
            await process_ocr(request, mock_current_user, test_db)
        
        assert exc_info.value.status_code == 503
        assert "OCR service is not available" in exc_info.value.detail


@pytest.mark.asyncio
async def test_process_ocr_translation_error(mock_current_user, test_db, test_manga, test_chapter):
    """Test OCR when translation service fails"""
    from sqlalchemy import select
    from app.models import Page
    
    result = await test_db.execute(
        select(Page).where(Page.chapter_id == test_chapter.id).limit(1)
    )
    page = result.scalar_one()
    
    mock_ocr_service = Mock()
    mock_ocr_service.process_region = Mock(return_value="テスト")
    
    mock_translator_service = Mock()
    mock_translator_service.translate = Mock(side_effect=Exception("Translation failed"))
    
    request = OcrRequest(
        manga_id=test_manga.id,
        chapter_id=test_chapter.id,
        page_id=page.id,
        x=100,
        y=100,
        width=200,
        height=50
    )
    
    with patch('app.api.ocr.get_ocr_service', return_value=mock_ocr_service), \
         patch('app.api.ocr.get_translator_service', return_value=mock_translator_service):
        
        with pytest.raises(HTTPException) as exc_info:
            await process_ocr(request, mock_current_user, test_db)
        
        assert exc_info.value.status_code == 500
        assert "Failed to process OCR request" in exc_info.value.detail


@pytest.mark.asyncio
async def test_process_ocr_invalid_coordinates(mock_current_user):
    """Test OCR with invalid coordinates (should be validated by Pydantic)"""
    # Test negative x coordinate
    with pytest.raises(ValueError):
        OcrRequest(
            manga_id=1,
            chapter_id=1,
            page_id=1,
            x=-10,
            y=100,
            width=200,
            height=50
        )
    
    # Test zero width
    with pytest.raises(ValueError):
        OcrRequest(
            manga_id=1,
            chapter_id=1,
            page_id=1,
            x=100,
            y=100,
            width=0,
            height=50
        )
