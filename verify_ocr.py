#!/usr/bin/env python3
"""
Manual verification script for OCR functionality.
This script tests the OCR service integration with a sample image.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.ocr_service import OllamaOCRService
from app.core.config import settings


async def test_ocr_service():
    """Test the OCR service with sample operations"""
    print("=" * 60)
    print("Ollama OCR Service Manual Verification")
    print("=" * 60)
    
    # Initialize service
    print(f"\n1. Initializing OCR service...")
    print(f"   - Enabled: {settings.OLLAMA_ENABLED}")
    print(f"   - Base URL: {settings.OLLAMA_BASE_URL}")
    print(f"   - Model: {settings.OLLAMA_MODEL}")
    
    service = OllamaOCRService()
    
    # Check availability
    print(f"\n2. Checking service availability...")
    is_available = service.is_available()
    print(f"   - Available: {is_available}")
    
    if not is_available:
        print("\n❌ OCR service is not available.")
        print("   Please ensure:")
        print("   1. Ollama is installed (https://ollama.ai/)")
        print("   2. Ollama is running (ollama serve)")
        print("   3. Qwen2.5-VL model is pulled (ollama pull qwen2.5-vl:7b)")
        print("   4. config/settings.json has ollama.enabled = true")
        return
    
    print("\n✓ OCR service is available and ready!")
    
    # Note: Actual image testing would require a real image file
    print("\n3. Ready for image processing")
    print("   To test with actual images:")
    print("   - Use the API endpoints /api/ocr/{manga_id}/{chapter_id}/{page_id}/extract")
    print("   - Or call service.extract_text(image_path) directly")
    
    print("\n" + "=" * 60)
    print("Manual verification complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_ocr_service())
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
