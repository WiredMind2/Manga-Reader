import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from app.api.ocr import process_ocr, OcrRequest


@pytest.mark.asyncio
async def test_process_ocr_success(mock_current_user):
    """Test successful OCR processing"""
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
        image_path="/path/to/image.jpg",
        x=100,
        y=100,
        width=200,
        height=50
    )
    
    with patch('app.api.ocr.get_ocr_service', return_value=mock_ocr_service), \
         patch('app.api.ocr.get_translator_service', return_value=mock_translator_service):
        
        result = await process_ocr(request, mock_current_user)
        
        assert result.original == "こんにちは"
        assert result.reading == "konnichiwa"
        assert result.translation == "Hello"
        assert result.notes == "Common greeting"
        mock_ocr_service.process_region.assert_called_once_with(
            "/path/to/image.jpg",
            (100, 100, 200, 50)
        )


@pytest.mark.asyncio
async def test_process_ocr_no_text_detected(mock_current_user):
    """Test OCR when no text is detected"""
    mock_ocr_service = Mock()
    mock_ocr_service.process_region = Mock(return_value="")
    
    request = OcrRequest(
        image_path="/path/to/image.jpg",
        x=100,
        y=100,
        width=200,
        height=50
    )
    
    with patch('app.api.ocr.get_ocr_service', return_value=mock_ocr_service):
        result = await process_ocr(request, mock_current_user)
        
        assert result.original == ""
        assert result.translation == "No text detected in the selected region"
        assert "Try selecting a region with visible text" in result.notes


@pytest.mark.asyncio
async def test_process_ocr_with_kanji_breakdown(mock_current_user):
    """Test OCR with kanji breakdown"""
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
        image_path="/path/to/image.jpg",
        x=50,
        y=50,
        width=100,
        height=30
    )
    
    with patch('app.api.ocr.get_ocr_service', return_value=mock_ocr_service), \
         patch('app.api.ocr.get_translator_service', return_value=mock_translator_service):
        
        result = await process_ocr(request, mock_current_user)
        
        assert result.original == "漫画"
        assert result.translation == "manga/comic"
        assert len(result.kanji_breakdown) == 2
        assert result.kanji_breakdown[0].kanji == "漫"
        assert result.kanji_breakdown[0].reading == "man"
        assert result.kanji_breakdown[1].kanji == "画"


@pytest.mark.asyncio
async def test_process_ocr_service_unavailable(mock_current_user):
    """Test OCR when service is unavailable"""
    mock_ocr_service = Mock()
    mock_ocr_service.process_region = Mock(side_effect=RuntimeError("OCR service not available"))
    
    request = OcrRequest(
        image_path="/path/to/image.jpg",
        x=100,
        y=100,
        width=200,
        height=50
    )
    
    with patch('app.api.ocr.get_ocr_service', return_value=mock_ocr_service):
        with pytest.raises(HTTPException) as exc_info:
            await process_ocr(request, mock_current_user)
        
        assert exc_info.value.status_code == 503
        assert "OCR service is not available" in exc_info.value.detail


@pytest.mark.asyncio
async def test_process_ocr_translation_error(mock_current_user):
    """Test OCR when translation service fails"""
    mock_ocr_service = Mock()
    mock_ocr_service.process_region = Mock(return_value="テスト")
    
    mock_translator_service = Mock()
    mock_translator_service.translate = Mock(side_effect=Exception("Translation failed"))
    
    request = OcrRequest(
        image_path="/path/to/image.jpg",
        x=100,
        y=100,
        width=200,
        height=50
    )
    
    with patch('app.api.ocr.get_ocr_service', return_value=mock_ocr_service), \
         patch('app.api.ocr.get_translator_service', return_value=mock_translator_service):
        
        with pytest.raises(HTTPException) as exc_info:
            await process_ocr(request, mock_current_user)
        
        assert exc_info.value.status_code == 500
        assert "Failed to process OCR request" in exc_info.value.detail


@pytest.mark.asyncio
async def test_process_ocr_invalid_coordinates(mock_current_user):
    """Test OCR with invalid coordinates (should be validated by Pydantic)"""
    # Test negative x coordinate
    with pytest.raises(ValueError):
        OcrRequest(
            image_path="/path/to/image.jpg",
            x=-10,
            y=100,
            width=200,
            height=50
        )
    
    # Test zero width
    with pytest.raises(ValueError):
        OcrRequest(
            image_path="/path/to/image.jpg",
            x=100,
            y=100,
            width=0,
            height=50
        )
