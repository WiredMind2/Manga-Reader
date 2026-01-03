"""
API tests for OCR endpoints
"""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

from app.models import User, Manga, Chapter, Page


pytestmark = pytest.mark.asyncio


class TestOCRStatusEndpoint:
    """Test cases for OCR status endpoint"""
    
    async def test_get_status_enabled(self, authenticated_client: AsyncClient):
        """Test getting OCR status when enabled"""
        with patch('app.api.ocr.ocr_service') as mock_service:
            mock_service.enabled = True
            mock_service.is_available.return_value = True
            mock_service.model = "qwen2.5-vl:7b"
            mock_service.base_url = "http://localhost:11434"
            
            response = await authenticated_client.get("/api/ocr/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is True
            assert data["available"] is True
            assert data["model"] == "qwen2.5-vl:7b"
            assert data["base_url"] == "http://localhost:11434"
    
    async def test_get_status_disabled(self, authenticated_client: AsyncClient):
        """Test getting OCR status when disabled"""
        with patch('app.api.ocr.ocr_service') as mock_service:
            mock_service.enabled = False
            mock_service.is_available.return_value = False
            
            response = await authenticated_client.get("/api/ocr/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is False
            assert data["available"] is False
            assert data["model"] is None


class TestOCRExtractEndpoint:
    """Test cases for OCR text extraction endpoint"""
    
    async def test_extract_text_success(
        self, 
        authenticated_client: AsyncClient,
        test_manga: Manga,
        test_chapter: Chapter
    ):
        """Test successful text extraction"""
        # Get the first page
        page_id = 1
        
        with patch('app.api.ocr.ocr_service') as mock_service:
            mock_service.enabled = True
            mock_service.is_available.return_value = True
            mock_service.model = "qwen2.5-vl:7b"
            
            # Mock extract_text method
            mock_service.extract_text = AsyncMock(return_value={
                "success": True,
                "text": "こんにちは世界",
                "source_language": "Japanese",
                "model": "qwen2.5-vl:7b"
            })
            
            response = await authenticated_client.post(
                f"/api/ocr/{test_manga.id}/{test_chapter.id}/{page_id}/extract",
                json={
                    "source_language": "Japanese"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["text"] == "こんにちは世界"
            assert data["source_language"] == "Japanese"
            assert data["model"] == "qwen2.5-vl:7b"
            
            # Verify the service was called
            mock_service.extract_text.assert_called_once()
    
    async def test_extract_text_not_authenticated(
        self, 
        client: AsyncClient,
        test_manga: Manga,
        test_chapter: Chapter
    ):
        """Test extraction fails without authentication"""
        response = await client.post(
            f"/api/ocr/{test_manga.id}/{test_chapter.id}/1/extract",
            json={"source_language": "Japanese"}
        )
        
        assert response.status_code == 401
    
    async def test_extract_text_service_disabled(
        self, 
        authenticated_client: AsyncClient,
        test_manga: Manga,
        test_chapter: Chapter
    ):
        """Test extraction fails when service is disabled"""
        with patch('app.api.ocr.ocr_service') as mock_service:
            mock_service.enabled = False
            
            response = await authenticated_client.post(
                f"/api/ocr/{test_manga.id}/{test_chapter.id}/1/extract",
                json={"source_language": "Japanese"}
            )
            
            assert response.status_code == 503
            assert "not enabled" in response.json()["detail"].lower()
    
    async def test_extract_text_service_unavailable(
        self, 
        authenticated_client: AsyncClient,
        test_manga: Manga,
        test_chapter: Chapter
    ):
        """Test extraction fails when service is unavailable"""
        with patch('app.api.ocr.ocr_service') as mock_service:
            mock_service.enabled = True
            mock_service.is_available.return_value = False
            
            response = await authenticated_client.post(
                f"/api/ocr/{test_manga.id}/{test_chapter.id}/1/extract",
                json={"source_language": "Japanese"}
            )
            
            assert response.status_code == 503
            assert "not available" in response.json()["detail"].lower()
    
    async def test_extract_text_page_not_found(
        self, 
        authenticated_client: AsyncClient,
        test_manga: Manga,
        test_chapter: Chapter
    ):
        """Test extraction fails for non-existent page"""
        with patch('app.api.ocr.ocr_service') as mock_service:
            mock_service.enabled = True
            mock_service.is_available.return_value = True
            
            response = await authenticated_client.post(
                f"/api/ocr/{test_manga.id}/{test_chapter.id}/9999/extract",
                json={"source_language": "Japanese"}
            )
            
            assert response.status_code == 404
    
    async def test_extract_text_custom_prompt(
        self, 
        authenticated_client: AsyncClient,
        test_manga: Manga,
        test_chapter: Chapter
    ):
        """Test extraction with custom prompt"""
        with patch('app.api.ocr.ocr_service') as mock_service:
            mock_service.enabled = True
            mock_service.is_available.return_value = True
            mock_service.extract_text = AsyncMock(return_value={
                "success": True,
                "text": "Custom extracted text",
                "source_language": "Japanese",
                "model": "qwen2.5-vl:7b"
            })
            
            custom_prompt = "Extract text in a special format"
            response = await authenticated_client.post(
                f"/api/ocr/{test_manga.id}/{test_chapter.id}/1/extract",
                json={
                    "source_language": "Japanese",
                    "custom_prompt": custom_prompt
                }
            )
            
            assert response.status_code == 200
            
            # Verify custom prompt was passed
            call_kwargs = mock_service.extract_text.call_args[1]
            assert call_kwargs["prompt"] == custom_prompt


class TestOCRTranslateEndpoint:
    """Test cases for OCR translation endpoint"""
    
    async def test_translate_text_success(
        self, 
        authenticated_client: AsyncClient,
        test_manga: Manga,
        test_chapter: Chapter
    ):
        """Test successful text translation"""
        with patch('app.api.ocr.ocr_service') as mock_service:
            mock_service.enabled = True
            mock_service.is_available.return_value = True
            mock_service.model = "qwen2.5-vl:7b"
            
            mock_service.extract_and_translate = AsyncMock(return_value={
                "success": True,
                "original_text": "こんにちは世界",
                "translated_text": "Hello World",
                "source_language": "Japanese",
                "target_language": "English",
                "model": "qwen2.5-vl:7b"
            })
            
            response = await authenticated_client.post(
                f"/api/ocr/{test_manga.id}/{test_chapter.id}/1/translate",
                json={
                    "source_language": "Japanese",
                    "target_language": "English"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["original_text"] == "こんにちは世界"
            assert data["translated_text"] == "Hello World"
            assert data["source_language"] == "Japanese"
            assert data["target_language"] == "English"
    
    async def test_translate_text_default_target_language(
        self, 
        authenticated_client: AsyncClient,
        test_manga: Manga,
        test_chapter: Chapter
    ):
        """Test translation with default target language"""
        with patch('app.api.ocr.ocr_service') as mock_service:
            mock_service.enabled = True
            mock_service.is_available.return_value = True
            mock_service.extract_and_translate = AsyncMock(return_value={
                "success": True,
                "original_text": "こんにちは",
                "translated_text": "Hello",
                "source_language": "Japanese",
                "target_language": "English",
                "model": "qwen2.5-vl:7b"
            })
            
            response = await authenticated_client.post(
                f"/api/ocr/{test_manga.id}/{test_chapter.id}/1/translate",
                json={
                    "source_language": "Japanese"
                    # No target_language specified
                }
            )
            
            assert response.status_code == 200
            
            # Verify default target language was used (English)
            call_kwargs = mock_service.extract_and_translate.call_args[1]
            assert call_kwargs["target_language"] == "English"
    
    async def test_translate_text_not_authenticated(
        self, 
        client: AsyncClient,
        test_manga: Manga,
        test_chapter: Chapter
    ):
        """Test translation fails without authentication"""
        response = await client.post(
            f"/api/ocr/{test_manga.id}/{test_chapter.id}/1/translate",
            json={"source_language": "Japanese"}
        )
        
        assert response.status_code == 401
    
    async def test_translate_text_service_disabled(
        self, 
        authenticated_client: AsyncClient,
        test_manga: Manga,
        test_chapter: Chapter
    ):
        """Test translation fails when service is disabled"""
        with patch('app.api.ocr.ocr_service') as mock_service:
            mock_service.enabled = False
            
            response = await authenticated_client.post(
                f"/api/ocr/{test_manga.id}/{test_chapter.id}/1/translate",
                json={"source_language": "Japanese"}
            )
            
            assert response.status_code == 503
    
    async def test_translate_text_page_not_found(
        self, 
        authenticated_client: AsyncClient,
        test_manga: Manga,
        test_chapter: Chapter
    ):
        """Test translation fails for non-existent page"""
        with patch('app.api.ocr.ocr_service') as mock_service:
            mock_service.enabled = True
            mock_service.is_available.return_value = True
            
            response = await authenticated_client.post(
                f"/api/ocr/{test_manga.id}/{test_chapter.id}/9999/translate",
                json={"source_language": "Japanese"}
            )
            
            assert response.status_code == 404
    
    async def test_translate_text_error_handling(
        self, 
        authenticated_client: AsyncClient,
        test_manga: Manga,
        test_chapter: Chapter
    ):
        """Test translation handles errors gracefully"""
        with patch('app.api.ocr.ocr_service') as mock_service:
            mock_service.enabled = True
            mock_service.is_available.return_value = True
            mock_service.extract_and_translate = AsyncMock(return_value={
                "success": False,
                "error": "OCR processing failed",
                "original_text": "",
                "translated_text": "",
                "source_language": "Japanese",
                "target_language": "English",
                "model": "qwen2.5-vl:7b"
            })
            
            response = await authenticated_client.post(
                f"/api/ocr/{test_manga.id}/{test_chapter.id}/1/translate",
                json={"source_language": "Japanese"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "error" in data
