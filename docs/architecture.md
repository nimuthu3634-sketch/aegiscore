# AegisCore Architecture

## Monorepo layout

```text
/
|-- apps/
|   |-- web/
|   |-- api/
|   |-- worker/
|-- packages/
|   |-- ui/
|   |-- config/
|-- infra/
|   |-- nginx/
|   |-- docker/
|-- docs/
|-- scripts/
|-- docker-compose.yml
|-- .env.example
|-- README.md
```

## Platform responsibilities

- `apps/web`: analyst-facing frontend, branded auth shell, dashboard pages, and shared app-shell navigation.
- `apps/api`: REST API, auth, DB models, migrations, telemetry ingest, and explainable alert scoring.
- `apps/worker`: background queue consumer for long-running jobs such as model retrains.
- `packages/config`: shared brand tokens and static product constants.
- `packages/ui`: shared branded frontend components reusable across web surfaces.
- `infra/nginx`: reverse proxy rules for the web app, API, and authenticated websocket endpoints.
- `infra/docker`: Docker initialization files such as PostgreSQL extensions.

## Initial boot path

1. `postgres` and `redis` start first.
2. `api` runs Alembic migrations, then starts FastAPI.
3. `worker` uses the same Python application code and listens for queued jobs.
4. `web` starts the Next.js application.
5. `nginx` fronts the web UI, API, and websocket endpoints on a single entrypoint.

## Shared branding

Brand tokens live in `packages/config/src/index.ts` and are currently consumed by the login experience and app metadata.
