"""
OCR Service using Ollama for text extraction and translation from manga images.
Supports Qwen2.5-VL 7B model for multilingual text-in-image tasks.
"""
import base64
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import io
import zipfile
import rarfile

from PIL import Image
import ollama

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaOCRService:
    """Service for OCR and translation using Ollama models"""
    
    def __init__(self):
        self.enabled = settings.OLLAMA_ENABLED
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        
        if self.enabled:
            # Initialize Ollama client
            self.client = ollama.Client(host=self.base_url)
            logger.info(f"Ollama OCR Service initialized with model: {self.model}")
        else:
            self.client = None
            logger.info("Ollama OCR Service is disabled")
    
    def is_available(self) -> bool:
        """Check if the OCR service is available"""
        if not self.enabled or not self.client:
            return False
        
        try:
            # Try to list models to verify connection
            self.client.list()
            return True
        except Exception as e:
            logger.error(f"Ollama service not available: {e}")
            return False
    
    async def extract_text(
        self, 
        image_path: str,
        source_language: str = "Japanese",
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract text from an image using Ollama vision model.
        
        Args:
            image_path: Path to the image file
            source_language: Source language of the text (default: Japanese)
            prompt: Custom prompt for text extraction
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        if not self.enabled or not self.client:
            raise ValueError("Ollama OCR service is not enabled")
        
        try:
            # Load and prepare image
            image_data = self._prepare_image(image_path)
            
            # Create prompt for text extraction
            if prompt is None:
                prompt = f"Read all the {source_language} text in this image. Extract all text exactly as it appears, preserving the order and layout. Only output the extracted text, no explanations."
            
            # Call Ollama API
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                images=[image_data],
                options={
                    "temperature": 0.1,  # Low temperature for more deterministic output
                }
            )
            
            extracted_text = response.get('response', '').strip()
            
            return {
                "success": True,
                "text": extracted_text,
                "source_language": source_language,
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "source_language": source_language,
                "model": self.model
            }
    
    async def extract_and_translate(
        self,
        image_path: str,
        source_language: str = "Japanese",
        target_language: str = "English",
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract text from an image and translate it.
        
        Args:
            image_path: Path to the image file
            source_language: Source language of the text (default: Japanese)
            target_language: Target language for translation (default: English)
            prompt: Custom prompt for extraction and translation
            
        Returns:
            Dictionary containing original text, translation, and metadata
        """
        if not self.enabled or not self.client:
            raise ValueError("Ollama OCR service is not enabled")
        
        try:
            # Load and prepare image
            image_data = self._prepare_image(image_path)
            
            # Create prompt for text extraction and translation
            if prompt is None:
                prompt = f"Read and translate the {source_language} text in this image into {target_language}. First, extract the original text, then provide the translation. Format your response as:\nOriginal: [extracted text]\nTranslation: [translated text]"
            
            # Call Ollama API
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                images=[image_data],
                options={
                    "temperature": 0.3,  # Slightly higher for more natural translations
                }
            )
            
            response_text = response.get('response', '').strip()
            
            # Parse the response to extract original and translation
            original_text = ""
            translated_text = ""
            
            lines = response_text.split('\n')
            for line in lines:
                if line.startswith('Original:'):
                    original_text = line.replace('Original:', '').strip()
                elif line.startswith('Translation:'):
                    translated_text = line.replace('Translation:', '').strip()
            
            # If parsing failed, use the whole response as translation
            if not translated_text:
                translated_text = response_text
            
            return {
                "success": True,
                "original_text": original_text,
                "translated_text": translated_text,
                "source_language": source_language,
                "target_language": target_language,
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"Error translating text from image: {e}")
            return {
                "success": False,
                "error": str(e),
                "original_text": "",
                "translated_text": "",
                "source_language": source_language,
                "target_language": target_language,
                "model": self.model
            }
    
    def _prepare_image(self, image_path: str) -> str:
        """
        Prepare image for Ollama API by converting to base64.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        try:
            # Handle archive paths (format: archive_path:internal_path)
            if ':' in image_path:
                # Extract from archive
                archive_extensions = ['.zip', '.cbz', '.rar', '.cbr']
                colon_idx = -1
                
                for ext in archive_extensions:
                    ext_pos = image_path.lower().find(ext + ':')
                    if ext_pos != -1:
                        colon_idx = ext_pos + len(ext)
                        break
                
                if colon_idx > 0:
                    archive_path = image_path[:colon_idx]
                    internal_path = image_path[colon_idx + 1:]
                    
                    # Load image from archive
                    if archive_path.lower().endswith(('.zip', '.cbz')):
                        with zipfile.ZipFile(archive_path, 'r') as archive:
                            with archive.open(internal_path) as image_file:
                                image = Image.open(io.BytesIO(image_file.read()))
                    elif archive_path.lower().endswith(('.rar', '.cbr')):
                        with rarfile.RarFile(archive_path, 'r') as archive:
                            with archive.open(internal_path) as image_file:
                                image = Image.open(io.BytesIO(image_file.read()))
                    else:
                        raise ValueError(f"Unsupported archive format: {archive_path}")
                else:
                    raise ValueError(f"Invalid archive path format: {image_path}")
            else:
                # Load regular file
                image = Image.open(image_path)
            
            # Convert to RGB if necessary
            image = self._convert_to_rgb(image)
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Encode to base64
            return base64.b64encode(img_byte_arr).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error preparing image: {e}")
            raise
    
    def _convert_to_rgb(self, image: Image.Image) -> Image.Image:
        """
        Convert image to RGB format if necessary.
        
        Args:
            image: PIL Image object
            
        Returns:
            RGB PIL Image object
        """
        if image.mode in ('RGBA', 'P', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            return background
        elif image.mode != 'RGB':
            return image.convert('RGB')
        return image


# Global service instance
ocr_service = OllamaOCRService()
