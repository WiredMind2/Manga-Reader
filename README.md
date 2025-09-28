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

Full API documentation available at `/docs` when running the backend.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on both desktop and mobile
5. Submit a pull request

## License

MIT License - see LICENSE file for details.