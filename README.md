# AegisCore

AegisCore is a greenfield monorepo for a defensive Security Operations Center platform built as a production-minded final-year project and portfolio piece.

This starter wires the new platform around:

- `apps/web`: Next.js 15, TypeScript, Tailwind CSS, shadcn-style primitives
- `apps/api`: FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis-ready job hooks
- `apps/worker`: background worker entrypoint for queued model jobs
- `packages/config`: shared branding constants
- `packages/ui`: shared branded UI building blocks
- `infra/nginx`: reverse proxy config
- `infra/docker`: Docker bootstrap assets
- `docs`: architecture and setup notes
- `scripts`: seed and sample import helpers

## What boots today

- branded login shell in the web app
- API health endpoints at `/api/v1/health` and `/api/v1/health/ready`
- SQLAlchemy database wiring plus Alembic initial migration
- Redis-backed worker entrypoint for future background tasks
- NGINX reverse proxy for `/`, `/api`, and `/ws`
- Docker Compose base path for `web`, `api`, `worker`, `postgres`, `redis`, and `nginx`

## Quick start

1. Copy `.env.example` to `.env` if you want to override defaults.
2. Start the stack:

```bash
docker compose up --build
```

3. Open:

- `http://localhost:8080` for the proxied app
- `http://localhost:8000/docs` for the API docs

4. Seed starter data after the API container is up:

```bash
docker compose exec api python -m app.seeds.seed_demo
```

5. Optional sample imports:

```bash
python scripts/load_sample_data.py
```

## Local app commands

### Web

```bash
npm --prefix apps/web install
npm run web:dev
```

### API

```bash
cd apps/api
..\..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\..\.venv\Scripts\python.exe -m alembic upgrade head
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Worker

```bash
cd apps/worker
..\..\.venv\Scripts\python.exe main.py
```

## Tests

### Backend

```bash
.\.venv\Scripts\python.exe -m pytest apps/api/tests
```

### Frontend unit tests

```bash
cd apps/web
npm run test
```

### Frontend build

```bash
cd apps/web
npm run build
```

## Branding

- Primary orange: `#FF7A1A`
- Primary black: `#111111`
- White: `#FFFFFF`
- Surface: `#F7F7F7`
- Border: `#E8E8E8`

## Notes

- The old demo-era structure has been replaced by the monorepo layout above.
- Defensive telemetry imports remain lab-safe and file-based only.
- The current UI is an initial branded shell and operations starter, not the full finished SOC workflow suite yet.
