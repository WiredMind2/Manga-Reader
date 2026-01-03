# OCR and Translation Feature - Implementation Summary

## Overview
This document describes the OCR (Optical Character Recognition) and translation feature implemented for the Manga Reader application. This feature helps users learn Japanese by providing instant translations of text selected on manga pages.

## Features Implemented

### 1. OCR Mode Toggle
- **Location**: Reader interface top toolbar
- **Activation**: Click the speech bubble icon or press 'O' key
- **Visual Indicator**: Button highlights in blue when OCR mode is active
- **Behavior**: When active, changes cursor to crosshair and enables text selection

### 2. Rectangle Selection
- **How it works**: 
  - Click and drag on the manga page to create a selection rectangle
  - Rectangle is displayed with blue border and semi-transparent fill
  - Selection coordinates are automatically scaled to match the original image dimensions
- **Validation**: Very small selections (< 10px) are ignored to prevent accidental clicks

### 3. Translation Side Panel
- **Layout**: Fixed panel on the right side of the screen (384px width)
- **Content Sections**:
  - **Original Text**: Japanese text extracted from the selected region
  - **Reading**: Hiragana/romaji pronunciation
  - **Translation**: English translation
  - **Kanji Breakdown**: Individual kanji characters with readings and meanings
  - **Cultural Notes**: Additional context when applicable
- **States**:
  - Empty state: Shows instructions for using OCR mode
  - Loading state: Animated spinner with "Processing..." message
  - Error state: Red-themed error message
  - Success state: Organized display of translation data

### 4. Backend API

#### Endpoint: `POST /api/ocr/process`
**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "manga_id": 1,
  "chapter_id": 5,
  "page_id": 23,
  "x": 100,
  "y": 150,
  "width": 200,
  "height": 50
}
```

**Response**:
```json
{
  "original": "漫画を読む",
  "reading": "まんがをよむ / manga wo yomu",
  "translation": "Read manga",
  "kanji_breakdown": [
    {
      "kanji": "漫",
      "reading": "man",
      "meaning": "random, rambling"
    },
    {
      "kanji": "画",
      "reading": "ga",
      "meaning": "picture, drawing"
    },
    {
      "kanji": "読",
      "reading": "yo",
      "meaning": "read"
    }
  ],
  "notes": "Common phrase for manga reading"
}
```

## Technical Architecture

### Backend Components

1. **OCR Service** (`backend/app/services/ocr.py`)
   - Uses `manga-ocr` library for Japanese text extraction
   - Implements thread-safe singleton pattern
   - Handles both regular files and archive-based images
   - Crops image to selected region before processing

2. **Translator Service** (`backend/app/services/translator.py`)
   - Supports two translation providers:
     - **Ollama**: Local AI translation (free, requires Ollama installation)
     - **OpenRouter**: Cloud API translation (paid, requires API key)
   - Provider configurable via settings
   - Returns structured JSON response with kanji breakdown
   - Includes error handling with fallback responses

3. **OCR API Router** (`backend/app/api/ocr.py`)
   - Validates page, chapter, and manga IDs
   - Retrieves file path from database (security)
   - Coordinates OCR and translation services
   - Returns formatted response

### Frontend Components

1. **Translation Panel** (`frontend/src/lib/components/TranslationPanel.svelte`)
   - Reusable component for displaying translations
   - Responsive design
   - Loading and error states
   - Beautiful typography for Japanese text

2. **Reader Integration** (`frontend/src/routes/read/[slug]/[chapter]/+page.svelte`)
   - OCR mode state management
   - Mouse event handlers for selection
   - Coordinate scaling logic
   - Keyboard shortcuts
   - API integration

## Security Considerations

1. **No File Path Exposure**: Frontend sends page IDs instead of file paths
2. **Database Lookup**: Backend retrieves actual file paths from database
3. **Authentication Required**: OCR endpoint requires valid JWT token
4. **Input Validation**: Pydantic models validate all request parameters
5. **ID Verification**: Query joins ensure page, chapter, and manga IDs are properly related

## Configuration

### Backend Settings
File: `config/settings.json`

#### Ollama Configuration (Local)
```json
{
  "ocr": {
    "translation_provider": "ollama",
    "ollama_host": "http://localhost:11434",
    "ollama_model": "llama3"
  }
}
```

#### OpenRouter Configuration (Cloud)
```json
{
  "ocr": {
    "translation_provider": "openrouter",
    "openrouter_api_key": "sk-or-v1-...",
    "openrouter_model": "anthropic/claude-3.5-sonnet"
  }
}
```

Environment variables:
- `TRANSLATION_PROVIDER`: Translation service to use ("ollama" or "openrouter")
- `OLLAMA_HOST`: URL to Ollama server (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model to use (default: llama3)
- `OPENROUTER_API_KEY`: OpenRouter API key
- `OPENROUTER_MODEL`: OpenRouter model to use (default: anthropic/claude-3.5-sonnet)

### Dependencies

**Backend** (`requirements.txt`):
- `manga-ocr`: Japanese OCR specialized for manga
- `ollama`: Python client for Ollama API (for Ollama provider)
- `httpx`: HTTP client (for OpenRouter provider)
- `Pillow`: Image processing

**Frontend** (built-in):
- Uses existing Svelte and TailwindCSS

## Usage Instructions

### For End Users

1. **Enable OCR Mode**:
   - Click the speech bubble icon in the top toolbar, OR
   - Press the 'O' key

2. **Select Text**:
   - Click and drag to create a rectangle around Japanese text
   - Release to submit for translation

3. **View Translation**:
   - Translation panel appears on the right side
   - Shows original text, reading, translation, and kanji breakdown
   - Click X to close the panel

4. **Exit OCR Mode**:
   - Press 'O' key again, OR
   - Press ESC key, OR
   - Close the translation panel

### For Developers

#### Running the Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Running Translation Service

You have two options for the translation backend:

**Option 1: Ollama (Local)**
```bash
# Install Ollama from ollama.ai
ollama serve

# Pull a model
ollama pull llama3
```

**Option 2: OpenRouter (Cloud)**
```bash
# Get API key from openrouter.ai
# Set in config/settings.json or environment variable
export OPENROUTER_API_KEY="sk-or-v1-..."
```

#### Running Tests
```bash
cd backend
pytest tests/api/test_ocr.py -v
```

## Keyboard Shortcuts

- **O**: Toggle OCR mode
- **ESC**: Exit OCR mode or return to manga list
- **← / →**: Navigate pages (disabled in OCR mode)
- **F**: Toggle UI controls
- **R**: Switch reading direction
- **+/-**: Zoom in/out
- **0**: Reset zoom

## Future Enhancements

Potential improvements for future versions:

1. **User Preferences**:
   - Save preferred translation model
   - Toggle kanji breakdown on/off
   - Adjust translation panel width

2. **Translation History**:
   - Save translation history for review
   - Export translations to Anki flashcards
   - Bookmarking favorite translations

3. **Advanced Features**:
   - Voice pronunciation of Japanese text
   - Multiple translation sources
   - Grammar breakdown
   - Context-aware translations

4. **Performance**:
   - Cache common translations
   - Batch processing of multiple selections
   - Offline mode with pre-downloaded models

5. **Accessibility**:
   - Keyboard-only navigation in OCR mode
   - Screen reader support
   - High contrast mode for translations

## Known Limitations

1. **OCR Accuracy**: 
   - Depends on image quality and text clarity
   - May struggle with handwritten or stylized fonts
   - Works best with standard manga fonts

2. **Translation Quality**:
   - Depends on Ollama model capabilities
   - May not capture nuanced context
   - Cultural references might need additional explanation

3. **Performance**:
   - OCR processing takes 1-3 seconds per request
   - Translation adds 2-5 seconds depending on text length
   - Requires active internet connection to Ollama server

4. **Browser Compatibility**:
   - Modern browsers required (Chrome, Firefox, Safari, Edge)
   - Mouse/touch events required for selection
   - No mobile optimization yet (desktop experience only)

## Troubleshooting

### OCR Not Working
1. Check if manga-ocr is installed: `pip list | grep manga-ocr`
2. Verify Ollama is running: `curl http://localhost:11434/api/tags`
3. Check browser console for errors
4. Ensure valid authentication token

### Translation Errors
1. Verify Ollama model is pulled: `ollama list`
2. Check Ollama logs for errors
3. Try a different model in settings
4. Verify network connectivity

### UI Issues
1. Clear browser cache
2. Check browser console for JavaScript errors
3. Verify frontend build is up to date
4. Test in different browser

## Contributing

When contributing to the OCR feature:

1. **Code Style**: Follow existing patterns in the codebase
2. **Testing**: Add tests for new functionality
3. **Documentation**: Update this file and code comments
4. **Security**: Never expose file paths to frontend
5. **Performance**: Consider impact on load times

## License

This feature is part of the Manga Reader application and follows the same MIT license.
