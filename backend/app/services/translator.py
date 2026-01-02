import logging
import ollama
import json
from app.core.config import settings

logger = logging.getLogger(__name__)

class TranslatorService:
    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model = settings.OLLAMA_MODEL

    def translate(self, text: str) -> dict:
        """
        Translate Japanese text and return detailed breakdown.
        """
        prompt = f"""
        Analyze the following Japanese text from a manga:
        "{text}"

        Provide the output in the following JSON format ONLY:
        {{
            "original": "{text}",
            "reading": "hiragana reading",
            "translation": "natural english translation",
            "kanji_breakdown": [
                {{ "kanji": "kanji_char", "reading": "furigana", "meaning": "english meaning" }}
            ],
            "notes": "any cultural notes or nuances (optional)"
        }}
        """

        try:
            response = self.client.chat(model=self.model, messages=[
                {
                    'role': 'user',
                    'content': prompt,
                },
            ], format='json')
            
            content = response['message']['content']
            return json.loads(content)
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # Return a fallback structure
            return {
                "original": text,
                "reading": "Error",
                "translation": "Translation service unavailable",
                "kanji_breakdown": [],
                "error": str(e)
            }

def get_translator_service():
    return TranslatorService()
