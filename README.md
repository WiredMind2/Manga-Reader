# Manga Reader Web Application

A modern, responsive manga reader web application built with FastAPI backend and SvelteKit frontend.

## Features

- 📚 **Multi-format Support**: Browse manga from folders or archives (ZIP, RAR, CBZ, CBR)
- 👤 **User System**: Secure authentication and personal reading progress
- 📱 **Fully Responsive**: Perfect experience on desktop, tablet, and mobile
- 🎌 **Reading Modes**: Right-to-left (manga) and top-to-bottom (manhwa) support
- 📖 **Progress Tracking**: Remembers your last read chapter and page
- 🖼️ **Smart Optimization**: Server-side image optimization without modifying originals
- 🎨 **Modern UI**: Built with ShadCN components and TailwindCSS
- 📋 **Metadata Support**: Optional manga information and cover images
- 🔤 **OCR & Translation**: Select text on manga pages to get instant Japanese-to-English translations with kanji breakdown

## Folder Structure

```
manga-reader/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core functionality (auth, config)
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── alembic/            # Database migrations
│   └── requirements.txt    # Python dependencies
├── frontend/               # SvelteKit frontend
│   ├── src/
│   │   ├── routes/         # Pages and API routes
│   │   ├── lib/            # Components and utilities
│   │   └── app.html        # Main HTML template
│   └── package.json        # Node dependencies
├── config/                 # Configuration files
├── data/                   # Database and cache
└── manga/                  # Your manga folder (example)
    ├── One Piece/
    │   ├── Chapter 001/
    │   │   ├── 001.jpg
    │   │   ├── 002.jpg
    │   │   └── ...
    │   └── Chapter 002/
    └── Attack on Titan.cbz
```

## Expected Manga Structure

The application supports two main formats:

### 1. Folder Structure
```
manga/
├── [Series Name]/
│   ├── [Chapter Name]/
│   │   ├── 001.jpg
│   │   ├── 002.jpg
│   │   └── ...
│   └── cover.jpg (optional)
└── metadata.json (optional)
```

### 2. Archive Files
- **CBZ/ZIP**: Compressed folders with the same internal structure
- **CBR/RAR**: RAR compressed manga files
- Archives can be at series or chapter level

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- pnpm (recommended) or npm
- Ollama (for OCR translation feature) - [Install from ollama.ai](https://ollama.ai)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
pnpm install
pnpm dev
```

### OCR Translation Setup (Optional)
To enable the OCR translation feature for Japanese manga:

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Pull a Japanese-capable model:
   ```bash
   ollama pull llama3
   ```
3. Start Ollama (if not already running):
   ```bash
   ollama serve
   ```
4. Configure the Ollama settings in `config/settings.json` or via environment variables:
   ```json
   {
     "ollama_host": "http://localhost:11434",
     "ollama_model": "llama3"
   }
   ```

The OCR feature uses:
- **manga-ocr**: For extracting Japanese text from manga images
- **Ollama**: For translating Japanese to English with kanji breakdown and cultural notes

### Configuration
1. Copy `config/settings.example.json` to `config/settings.json`
2. Update the manga directory path in the config file
3. Run database migrations: `alembic upgrade head`

## Development

### Backend Development
- FastAPI with async support
- SQLAlchemy ORM with SQLite/PostgreSQL
- JWT authentication
- Automatic API documentation at `/docs`

### Frontend Development
- SvelteKit with TypeScript
- ShadCN/UI components
- TailwindCSS for styling
- Responsive design patterns

## API Endpoints

- `GET /api/manga` - List all manga series
- `GET /api/manga/{id}` - Get manga details
- `GET /api/manga/{id}/chapters` - List chapters
- `POST /api/auth/login` - User authentication
- `GET /api/progress` - Reading progress
- `POST /api/ocr/process` - Process OCR and translation request

Full API documentation available at `/docs` when running the backend.

## Using the OCR Translation Feature

The OCR translation feature helps you learn Japanese while reading manga:

1. **Open a manga chapter** in the reader
2. **Press 'O' key** or click the OCR button in the top toolbar to activate OCR mode
3. **Select text** by clicking and dragging a rectangle around Japanese text on the page
4. **View translation** in the side panel that appears, including:
   - Original Japanese text
   - Hiragana reading
   - English translation
   - Kanji character breakdown with individual meanings
   - Cultural notes (when applicable)

### Keyboard Shortcuts

- **O**: Toggle OCR mode
- **ESC**: Exit OCR mode or return to manga list
- **← / →**: Navigate between pages
- **F**: Toggle UI controls
- **R**: Switch reading direction
- **+/-**: Zoom in/out
- **0**: Reset zoom

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on both desktop and mobile
5. Submit a pull request

## License

MIT License - see LICENSE file for details.