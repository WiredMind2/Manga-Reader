# Manga Reader Web Application - Project Requirements

## Overview
A web-based manga reader application that allows users to browse and read manga stored locally on the server. The application will use Svelte for the frontend with ShadCN components and a Python backend server.

## Core Features

### 1. Backend Requirements (Python Server)
- **Framework**: FastAPI or Flask (need to clarify preference)
- **File System Access**: Scan local manga directories on the server
- **API Endpoints**:
  - List available manga series
  - Get manga details (title, chapters, pages)
  - Serve manga page images
  - Get directory structure
- **File Support**: Common image formats (JPG, PNG, WebP, etc.)
- **Archive Support**: ZIP, RAR, CBZ, CBR files (need to clarify if required)

### 2. Frontend Requirements (Svelte)
- **Framework**: SvelteKit for routing and SSR capabilities
- **UI Components**: ShadCN/UI components adapted for Svelte
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Pages**:
  - Manga library/browser page
  - Individual manga reader page
  - Settings/preferences page (optional)

### 3. Manga Organization Structure
**Need Clarification on folder structure:**
- How are manga organized? (Series → Chapters → Pages?)
- Expected naming conventions?
- Single folder with all manga or nested structure?
- Example: `/manga/One Piece/Chapter 001/page_001.jpg` vs `/manga/one-piece-ch001-p001.jpg`

### 4. Reader Features
- **Navigation**: Previous/Next page, chapter navigation
- **Display Options**: 
  - Single page view
  - Double page spread (need to clarify if required)
  - Fit to width/height options
- **Reading Direction**: Left-to-right, right-to-left (need to clarify default/options)
- **Zoom**: Zoom in/out functionality
- **Keyboard Shortcuts**: Arrow keys for navigation

### 5. Browser Features
- **Search**: Search manga by title
- **Sorting**: By name, date added, last read (need to clarify requirements)
- **Filtering**: By status, genre (if metadata available)
- **Thumbnails**: Cover images for each manga series
- **Progress Tracking**: Remember last read chapter/page (need to clarify if required)

## Technical Specifications

### Backend API Structure

# Authentication
POST /api/auth/register - User registration
POST /api/auth/login - User login  
POST /api/auth/logout - User logout
GET /api/auth/me - Get current user info

# Manga Management
GET /api/manga - List all available manga series (with pagination)
GET /api/manga/{series_id} - Get specific manga details + metadata
GET /api/manga/{series_id}/chapters - List chapters for a series
GET /api/manga/{series_id}/chapters/{chapter_id}/pages - List pages in a chapter
GET /api/images/{series_id}/{chapter_id}/{page_id} - Serve optimized page image
GET /api/covers/{series_id} - Serve cover image (optimized)

# Progress Tracking
GET /api/progress/{series_id} - Get user's reading progress for a series
PUT /api/progress/{series_id} - Update reading progress
GET /api/progress - Get all user reading progress

# Archive Support
GET /api/manga/{series_id}/extract/{chapter_id} - Extract and serve archive contents


### Data Storage
- **Configuration**: JSON config file for manga directory paths
- **Metadata**: JSON files or simple database for manga information
- **User Preferences**: Local storage or simple database (need to clarify)

## Confirmed Requirements (User Responses)

1. **Backend Framework**: ✅ FastAPI (modern, async support)

2. **Manga Folder Structure**: ✅ `/manga/[Series Name]/[Chapter Folder]/[Images in alphabetical order]`
   - Example: `/manga/One Piece/Chapter 001/001.jpg, 002.jpg, 003.jpg...`

3. **Archive Support**: ✅ Full support for ZIP, RAR, CBZ, CBR files

4. **Reading Direction**: ✅ Right-to-left (Japanese manga) + Top-to-bottom (Korean manhwa)
   - Smart detection or user preference setting needed

5. **Progress Tracking**: ✅ Remember last chapter read + reading progress within chapter

6. **Authentication**: ✅ Full user account/login system required

7. **Manga Metadata**: ✅ Optional metadata support + cover images
   - Must work without metadata (fallback to file scanning)
   - Support for cover images per manga series

8. **Mobile Support**: ✅ CRITICAL - Must be fully responsive (desktop + mobile)

9. **Scale**: ✅ No hard limits - design for variable user base and content size

10. **Server Optimization**: ✅ Required for UX, but NEVER modify original manga files

## Technology Stack

### Frontend
- **SvelteKit**: Main framework
- **ShadCN/UI**: Component library (Svelte port: shadcn-svelte)
- **TailwindCSS**: Styling (comes with ShadCN)
- **TypeScript**: Type safety

### Backend
- **Python 3.9+**
- **FastAPI**: Main web framework
- **SQLAlchemy**: Database ORM
- **Alembic**: Database migrations
- **Pillow**: Image processing and optimization
- **aiofiles**: Async file operations
- **uvicorn**: ASGI server
- **python-multipart**: File upload support
- **passlib[bcrypt]**: Password hashing
- **python-jose[cryptography]**: JWT tokens
- **rarfile**: RAR archive support
- **zipfile**: ZIP/CBZ archive support (built-in)
- **SQLite/PostgreSQL**: Database (SQLite for development)

### Development Tools
- **Vite**: Frontend build tool (SvelteKit default)
- **ESLint + Prettier**: Code formatting
- **Python Black**: Python code formatting

## File Structure (Proposed)
```
manga-reader/
├── backend/
│   ├── main.py
│   ├── api/
│   ├── models/
│   ├── utils/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── static/
│   ├── package.json
│   └── svelte.config.js
├── config/
│   └── settings.json
└── README.md
```
