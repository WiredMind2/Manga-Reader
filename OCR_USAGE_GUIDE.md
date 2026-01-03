# OCR Feature Usage Guide

This document explains how to use the Ollama OCR feature for text extraction and translation in manga images.

## Prerequisites

1. **Install Ollama**: Follow the instructions at https://ollama.ai/
2. **Pull the Qwen2.5-VL model**:
   ```bash
   ollama pull qwen2.5-vl:7b
   ```

## Configuration

1. Edit `config/settings.json` and enable Ollama:
   ```json
   {
     "ollama": {
       "enabled": true,
       "base_url": "http://localhost:11434",
       "model": "qwen2.5-vl:7b",
       "timeout": 60
     }
   }
   ```

2. Start the Ollama service (if not already running):
   ```bash
   ollama serve
   ```

## API Endpoints

### Check OCR Status
```bash
GET /api/ocr/status
```

Returns the current status of the OCR service:
```json
{
  "enabled": true,
  "available": true,
  "model": "qwen2.5-vl:7b",
  "base_url": "http://localhost:11434"
}
```

### Extract Text from Page
```bash
POST /api/ocr/{manga_id}/{chapter_id}/{page_id}/extract
Content-Type: application/json
Authorization: Bearer {your_token}

{
  "source_language": "Japanese",
  "custom_prompt": "Optional custom prompt"
}
```

Response:
```json
{
  "success": true,
  "text": "こんにちは世界",
  "source_language": "Japanese",
  "model": "qwen2.5-vl:7b"
}
```

### Extract and Translate Text from Page
```bash
POST /api/ocr/{manga_id}/{chapter_id}/{page_id}/translate
Content-Type: application/json
Authorization: Bearer {your_token}

{
  "source_language": "Japanese",
  "target_language": "English",
  "custom_prompt": "Optional custom prompt"
}
```

Response:
```json
{
  "success": true,
  "original_text": "こんにちは世界",
  "translated_text": "Hello World",
  "source_language": "Japanese",
  "target_language": "English",
  "model": "qwen2.5-vl:7b"
}
```

## User Preferences

Users can configure OCR preferences in their profile:

```bash
PUT /api/preferences
Content-Type: application/json
Authorization: Bearer {your_token}

{
  "ocr_enabled": true,
  "ocr_auto_translate": false,
  "ocr_source_language": "Japanese",
  "ocr_target_language": "English"
}
```

Available preferences:
- `ocr_enabled`: Enable/disable OCR features for the user
- `ocr_auto_translate`: Automatically translate text when viewing pages
- `ocr_source_language`: Default source language for OCR (e.g., "Japanese", "Chinese", "Korean")
- `ocr_target_language`: Default target language for translation (e.g., "English", "Spanish")

## Example Usage with cURL

### 1. Check OCR Status
```bash
curl -X GET http://localhost:8000/api/ocr/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Extract Text
```bash
curl -X POST http://localhost:8000/api/ocr/1/1/1/extract \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_language": "Japanese"
  }'
```

### 3. Translate Text
```bash
curl -X POST http://localhost:8000/api/ocr/1/1/1/translate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_language": "Japanese",
    "target_language": "English"
  }'
```

## Model Performance

The Qwen2.5-VL 7B model provides:
- **Strong multilingual support**: Handles Latin, Japanese, Chinese, Korean, and other Asian scripts
- **Image OCR accuracy**: Around 85-90% accuracy for Japanese text in images
- **Context awareness**: Can understand speech bubbles and panel layouts
- **Translation capability**: Can translate extracted text to various languages

## Troubleshooting

### OCR service not available
- Ensure Ollama is running: `ollama serve`
- Check that the model is pulled: `ollama list`
- Verify the base_url in settings.json matches your Ollama instance

### Poor OCR accuracy
- Try using custom prompts to guide the model
- Ensure images are clear and text is readable
- Consider cropping to specific speech bubbles for better focus

### Slow response times
- The 7B model requires significant compute resources
- Increase the timeout value in settings.json if needed
- Consider using a GPU-enabled Ollama instance for faster processing

## Integration with Frontend

The frontend can integrate OCR features by:
1. Checking OCR availability via `/api/ocr/status`
2. Adding "Extract Text" and "Translate" buttons to page viewer
3. Displaying extracted/translated text in overlay or side panel
4. Using user preferences to enable/disable features and set default languages

## Future Enhancements

Potential improvements for the OCR feature:
- Batch processing of multiple pages
- Caching of OCR results to avoid re-processing
- Support for cropping specific regions (speech bubbles) before OCR
- Integration with other translation services (Google Translate, DeepL)
- OCR result history and corrections
