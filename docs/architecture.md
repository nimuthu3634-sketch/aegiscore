# AegisCore Architecture Notes

## Monorepo shape

- `frontend/`: React + TypeScript + Vite application
- `backend/`: FastAPI application with SQLAlchemy, Redis, WebSockets, and ML scaffolding
- `docker/`: local container support assets
- `assets/`: shared branding assets
- `docs/`: project notes and implementation references

## Frontend approach

- Route-based pages for the main SOC workflow
- Reusable shell components for sidebar, navbar, cards, charts, and tables
- Tailwind theme configured to the AegisCore brand palette
- Placeholder views ready to be connected to live endpoints

## Backend approach

- Feature routers under `app/api/routers`
- Shared configuration under `app/core`
- Database setup under `app/db`
- SQLAlchemy models under `app/models`
- Pydantic schemas under `app/schemas`
- Business logic placeholders under `app/services`
- ML helpers under `app/ml`
- WebSocket utilities under `app/ws`

## Development guidance

- Keep the code readable and student-friendly.
- Build features incrementally and keep each phase runnable.
- Favor clear boundaries over premature abstraction.
