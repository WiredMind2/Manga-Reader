import logging
import json
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class TranslatorService:
    def __init__(self):
        self.provider = settings.TRANSLATION_PROVIDER.lower()
        
        if self.provider == "ollama":
            import ollama
            self.client = ollama.Client(host=settings.OLLAMA_HOST)
            self.model = settings.OLLAMA_MODEL
        elif self.provider == "openrouter":
            self.api_key = settings.OPENROUTER_API_KEY
            self.model = settings.OPENROUTER_MODEL
            if not self.api_key:
                logger.warning("OpenRouter API key not configured")
        else:
            raise ValueError(f"Unsupported translation provider: {self.provider}")

    def translate(self, text: str) -> dict:
        """
        Translate Japanese text and return detailed breakdown.
        """
        if self.provider == "ollama":
            return self._translate_ollama(text)
        elif self.provider == "openrouter":
            return self._translate_openrouter(text)
        else:
            return self._error_response(text, "Unsupported translation provider")

    def _translate_ollama(self, text: str) -> dict:
        """Translate using Ollama"""
        prompt = self._build_prompt(text)
        
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
            logger.error(f"Ollama translation failed: {e}")
            return self._error_response(text, str(e))

    def _translate_openrouter(self, text: str) -> dict:
        """Translate using OpenRouter API"""
        import httpx
        
        if not self.api_key:
            return self._error_response(text, "OpenRouter API key not configured")
        
        prompt = self._build_prompt(text)
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "response_format": {"type": "json_object"}
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    return self._error_response(text, f"API error: {response.status_code}")
                
                result = response.json()
                content = result['choices'][0]['message']['content']
                return json.loads(content)
                
        except Exception as e:
            logger.error(f"OpenRouter translation failed: {e}")
            return self._error_response(text, str(e))

    def _build_prompt(self, text: str) -> str:
        """Build the translation prompt"""
        return f"""
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

    def _error_response(self, text: str, error: str) -> dict:
        """Return a fallback error response"""
        return {
            "original": text,
            "reading": "Error",
            "translation": "Translation service unavailable",
            "kanji_breakdown": [],
            "error": error
        }


def get_translator_service():
    return TranslatorService()
