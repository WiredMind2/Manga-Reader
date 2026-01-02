# Suggested Commands

## Backend
- **Run**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` (in `backend/`)
- **Test**: `pytest` (in `backend/`)
- **Install Deps**: `pip install -r requirements.txt`

## Frontend
- **Run**: `pnpm dev` (in `frontend/`)
- **Build**: `pnpm build`
- **Test (Unit)**: `pnpm test` (Vitest)
- **Test (E2E)**: `pnpm test:e2e` (Playwright)
- **Check**: `pnpm check` (Svelte Check)
- **Install Deps**: `pnpm install`

## Database
- **Migrations**: `alembic upgrade head` (in `backend/`)
