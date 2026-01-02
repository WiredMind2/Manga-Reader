import logging
from PIL import Image
import io
from functools import lru_cache

logger = logging.getLogger(__name__)

class OcrService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OcrService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        try:
            from manga_ocr import MangaOcr
            self.mocr = MangaOcr()
            self._initialized = True
            logger.info("MangaOCR initialized successfully")
        except ImportError:
            logger.error("manga-ocr not installed. OCR features will not work.")
            self.mocr = None
        except Exception as e:
            logger.error(f"Failed to initialize MangaOCR: {e}")
            self.mocr = None

    def process_region(self, image_path: str, box: tuple[int, int, int, int]) -> str:
        """
        Process a region of an image and return the text.
        box: (x, y, width, height)
        """
        if not self.mocr:
            raise RuntimeError("OCR service is not available")

        try:
            img = Image.open(image_path)
            # Convert box (x, y, w, h) to (left, top, right, bottom)
            x, y, w, h = box
            crop_box = (x, y, x + w, y + h)
            
            cropped = img.crop(crop_box)
            text = self.mocr(cropped)
            return text
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise

@lru_cache()
def get_ocr_service():
    return OcrService()
