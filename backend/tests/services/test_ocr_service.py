"""
Unit tests for OCR service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
from PIL import Image
import io

from app.services.ocr_service import OllamaOCRService


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client"""
    with patch('app.services.ocr_service.ollama.Client') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_settings_enabled():
    """Mock settings with Ollama enabled"""
    with patch('app.services.ocr_service.settings') as mock_settings:
        mock_settings.OLLAMA_ENABLED = True
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_settings.OLLAMA_MODEL = "qwen2.5-vl:7b"
        mock_settings.OLLAMA_TIMEOUT = 60
        yield mock_settings


@pytest.fixture
def mock_settings_disabled():
    """Mock settings with Ollama disabled"""
    with patch('app.services.ocr_service.settings') as mock_settings:
        mock_settings.OLLAMA_ENABLED = False
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_settings.OLLAMA_MODEL = "qwen2.5-vl:7b"
        mock_settings.OLLAMA_TIMEOUT = 60
        yield mock_settings


@pytest.fixture
def test_image_path():
    """Create a test image and return its path"""
    # Create a temporary test image
    temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img = Image.new('RGB', (100, 100), color='white')
    img.save(temp_file.name, 'JPEG')
    temp_file.close()
    yield temp_file.name
    # Cleanup
    Path(temp_file.name).unlink(missing_ok=True)


class TestOllamaOCRService:
    """Test cases for OllamaOCRService"""
    
    def test_init_enabled(self, mock_settings_enabled, mock_ollama_client):
        """Test service initialization with Ollama enabled"""
        service = OllamaOCRService()
        assert service.enabled is True
        assert service.base_url == "http://localhost:11434"
        assert service.model == "qwen2.5-vl:7b"
        assert service.client is not None
    
    def test_init_disabled(self, mock_settings_disabled):
        """Test service initialization with Ollama disabled"""
        service = OllamaOCRService()
        assert service.enabled is False
        assert service.client is None
    
    def test_is_available_when_enabled(self, mock_settings_enabled, mock_ollama_client):
        """Test is_available returns True when service is enabled and accessible"""
        mock_ollama_client.list.return_value = []
        service = OllamaOCRService()
        assert service.is_available() is True
        mock_ollama_client.list.assert_called_once()
    
    def test_is_available_when_disabled(self, mock_settings_disabled):
        """Test is_available returns False when service is disabled"""
        service = OllamaOCRService()
        assert service.is_available() is False
    
    def test_is_available_when_connection_fails(self, mock_settings_enabled, mock_ollama_client):
        """Test is_available returns False when connection fails"""
        mock_ollama_client.list.side_effect = Exception("Connection failed")
        service = OllamaOCRService()
        assert service.is_available() is False
    
    @pytest.mark.asyncio
    async def test_extract_text_success(self, mock_settings_enabled, mock_ollama_client, test_image_path):
        """Test successful text extraction"""
        mock_ollama_client.generate.return_value = {
            'response': 'こんにちは世界'
        }
        
        service = OllamaOCRService()
        result = await service.extract_text(test_image_path, source_language="Japanese")
        
        assert result["success"] is True
        assert result["text"] == 'こんにちは世界'
        assert result["source_language"] == "Japanese"
        assert result["model"] == "qwen2.5-vl:7b"
        
        # Verify Ollama was called with correct parameters
        mock_ollama_client.generate.assert_called_once()
        call_kwargs = mock_ollama_client.generate.call_args[1]
        assert call_kwargs["model"] == "qwen2.5-vl:7b"
        assert "Japanese" in call_kwargs["prompt"]
    
    @pytest.mark.asyncio
    async def test_extract_text_disabled(self, mock_settings_disabled, test_image_path):
        """Test extract_text raises error when service is disabled"""
        service = OllamaOCRService()
        
        with pytest.raises(ValueError, match="Ollama OCR service is not enabled"):
            await service.extract_text(test_image_path)
    
    @pytest.mark.asyncio
    async def test_extract_text_error(self, mock_settings_enabled, mock_ollama_client, test_image_path):
        """Test extract_text handles errors gracefully"""
        mock_ollama_client.generate.side_effect = Exception("API Error")
        
        service = OllamaOCRService()
        result = await service.extract_text(test_image_path)
        
        assert result["success"] is False
        assert "error" in result
        assert result["text"] == ""
    
    @pytest.mark.asyncio
    async def test_extract_and_translate_success(self, mock_settings_enabled, mock_ollama_client, test_image_path):
        """Test successful text extraction and translation"""
        mock_ollama_client.generate.return_value = {
            'response': 'Original: こんにちは世界\nTranslation: Hello World'
        }
        
        service = OllamaOCRService()
        result = await service.extract_and_translate(
            test_image_path, 
            source_language="Japanese",
            target_language="English"
        )
        
        assert result["success"] is True
        assert result["original_text"] == 'こんにちは世界'
        assert result["translated_text"] == 'Hello World'
        assert result["source_language"] == "Japanese"
        assert result["target_language"] == "English"
    
    @pytest.mark.asyncio
    async def test_extract_and_translate_fallback(self, mock_settings_enabled, mock_ollama_client, test_image_path):
        """Test extract_and_translate falls back to full response if parsing fails"""
        mock_ollama_client.generate.return_value = {
            'response': 'Hello World'  # No "Original:" or "Translation:" markers
        }
        
        service = OllamaOCRService()
        result = await service.extract_and_translate(test_image_path)
        
        assert result["success"] is True
        assert result["translated_text"] == 'Hello World'
    
    @pytest.mark.asyncio
    async def test_extract_and_translate_disabled(self, mock_settings_disabled, test_image_path):
        """Test extract_and_translate raises error when service is disabled"""
        service = OllamaOCRService()
        
        with pytest.raises(ValueError, match="Ollama OCR service is not enabled"):
            await service.extract_and_translate(test_image_path)
    
    @pytest.mark.asyncio
    async def test_extract_and_translate_error(self, mock_settings_enabled, mock_ollama_client, test_image_path):
        """Test extract_and_translate handles errors gracefully"""
        mock_ollama_client.generate.side_effect = Exception("API Error")
        
        service = OllamaOCRService()
        result = await service.extract_and_translate(test_image_path)
        
        assert result["success"] is False
        assert "error" in result
        assert result["original_text"] == ""
        assert result["translated_text"] == ""
    
    @pytest.mark.asyncio
    async def test_custom_prompt(self, mock_settings_enabled, mock_ollama_client, test_image_path):
        """Test using custom prompt"""
        mock_ollama_client.generate.return_value = {
            'response': 'Custom response'
        }
        
        service = OllamaOCRService()
        custom_prompt = "Extract text in a special way"
        result = await service.extract_text(test_image_path, prompt=custom_prompt)
        
        call_kwargs = mock_ollama_client.generate.call_args[1]
        assert call_kwargs["prompt"] == custom_prompt
    
    def test_prepare_image_success(self, mock_settings_enabled, mock_ollama_client, test_image_path):
        """Test image preparation succeeds"""
        service = OllamaOCRService()
        result = service._prepare_image(test_image_path)
        
        # Should return base64 encoded string
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_prepare_image_invalid_path(self, mock_settings_enabled, mock_ollama_client):
        """Test image preparation fails with invalid path"""
        service = OllamaOCRService()
        
        with pytest.raises(Exception):
            service._prepare_image("/nonexistent/path/image.jpg")
