# AegisCore

AegisCore is a monorepo for a defensive SOC platform built with:

- `apps/web`: Next.js 15, TypeScript, Tailwind CSS
- `apps/api`: FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis
- `apps/worker`: RQ worker for background ML jobs
- `infra/nginx`: reverse proxy for frontend, API, docs, and websocket traffic

## Local Deployment Modes

### Prod-like local mode

Runs the full stack behind NGINX with production-style container commands:

```bash
docker compose up --build
```

Equivalent npm helper:

```bash
npm run stack:up
```

### Dev mode

Runs the same stack with bind mounts and live-reload for the web and API services:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Equivalent PowerShell helper:

```powershell
.\scripts\dev-up.ps1
```

Equivalent npm helper:

```bash
npm run stack:up:dev
```

## Environment Files

The stack can boot from defaults, but copying the examples is recommended when you want custom ports or secrets:

```bash
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
```

Provided examples:

- [`.env.example`](C:/Users/nimuthusil99460/Documents/GitHub/aegiscore/.env.example)
- [`apps/api/.env.example`](C:/Users/nimuthusil99460/Documents/GitHub/aegiscore/apps/api/.env.example)
- [`apps/web/.env.example`](C:/Users/nimuthusil99460/Documents/GitHub/aegiscore/apps/web/.env.example)

## Services

The production-style compose stack includes:

- `postgres`
- `redis`
- `migrate`
- `api`
- `worker`
- `web`
- `nginx`

Startup order is health-aware:

- `postgres` and `redis` must become healthy first
- `migrate` runs `alembic upgrade head`
- `api` and `worker` wait for `migrate`
- `web` waits for `api`
- `nginx` waits for both `api` and `web`

## URLs

When the stack is up:

- App shell: [http://localhost:8080](http://localhost:8080)
- API health: [http://localhost:8080/api/v1/health](http://localhost:8080/api/v1/health)
- API docs: [http://localhost:8080/docs](http://localhost:8080/docs)
- Direct API in dev mode: [http://localhost:8000/docs](http://localhost:8000/docs)
- Direct web in dev mode: [http://localhost:3000](http://localhost:3000)

## Exact Commands

### Startup commands

Prod-like local:

```bash
docker compose up --build
```

Dev mode:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Stop the stack:

```bash
docker compose down --remove-orphans
```

### Migration commands

Run migrations explicitly:

```bash
docker compose run --rm migrate
```

Alternative against a running API container:

```bash
docker compose exec api alembic upgrade head
```

### Seed commands

Seed the base demo dataset:

```bash
docker compose run --rm api python -m app.seeds.seed_demo
```

Load the richer sample lab dataset:

```bash
docker compose run --rm api python -m app.seeds.load_sample_dataset
```

### Test commands

Backend tests:

```bash
docker compose run --rm api pytest tests
```

Frontend build:

```bash
docker compose run --rm web npm run build
```

Frontend unit tests:

```bash
docker compose run --rm web npm run test
```

Combined local smoke for backend plus frontend build:

```bash
npm run stack:test
```

## Non-Docker Local Commands

### API

```bash
cd apps/api
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

### Worker

```bash
cd apps/worker
python main.py
```

### Web

```bash
cd apps/web
npm install
npm run dev
```

## CI

The workflow at [`.github/workflows/ci.yml`](C:/Users/nimuthusil99460/Documents/GitHub/aegiscore/.github/workflows/ci.yml) runs:

- backend tests
- frontend lint
- frontend unit tests
- frontend build
- optional Docker Compose smoke test on manual dispatch

The smoke job boots the stack and checks:

- `/healthz` on NGINX
- `/api/v1/health`
- `/docs`
- the frontend root response

## Deployment Notes

- The base [docker-compose.yml](C:/Users/nimuthusil99460/Documents/GitHub/aegiscore/docker-compose.yml) is the prod-like local path.
- The dev override in [docker-compose.dev.yml](C:/Users/nimuthusil99460/Documents/GitHub/aegiscore/docker-compose.dev.yml) adds bind mounts, direct ports, and live-reload commands.
- NGINX routes `/`, `/api/`, `/docs`, `/redoc`, `/openapi.json`, `/api/v1/ws/`, and `/ws/`.
- Public websocket URLs now use the API prefix, matching the actual FastAPI websocket route shape.
