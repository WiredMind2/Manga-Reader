# Project Overview

## Purpose
Manga reader web app. Browses manga from folders/archives, tracks progress.

## Tech Stack
- **Backend**: Python, FastAPI, SQLAlchemy, Alembic.
- **Frontend**: SvelteKit, TypeScript, TailwindCSS, Vite.

## Structure
- `backend/`: FastAPI app.
    - `app/`: Main code (`api`, `core`, `models`, `services`).
    - `tests/`: Pytest tests.
- `frontend/`: SvelteKit app.
    - `src/`: Source (`routes`, `lib`).
    - `tests/`: Vitest/Playwright tests.
- `config/`: Config files.
- `data/`: Storage.
