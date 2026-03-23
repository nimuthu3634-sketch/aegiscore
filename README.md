# AegisCore

AegisCore is a final-year university project: an AI-integrated Security
Operations Center (SOC) web application for lab-based cybersecurity
monitoring, alert triage, incident management, reporting, and safe classroom
data ingestion.

The repository is organized as a monorepo with:

- a React + TypeScript + Vite frontend
- a FastAPI backend
- PostgreSQL and Redis for local infrastructure
- WebSockets for live alert updates
- a small scikit-learn anomaly detection module for explainable demo insights

## Repository structure

```text
.
|-- frontend/
|-- backend/
|-- docker/
|-- docs/
|-- assets/
|-- docker-compose.yml
|-- .env.example
|-- README.md
|-- AGENTS.md
```

## Prerequisites

### Local development

- Python 3.12
- Node.js 20+
- npm 10+
- PostgreSQL 16 if you want local database persistence outside Docker
- Redis 7 if you want local Redis outside Docker

### Docker development

- Docker Desktop with `docker compose`

## Quick overview

- The UI is demo-ready out of the box with seeded in-memory alerts,
  incidents, logs, integrations, lab assets, and reports.
- On backend startup, AegisCore now:

  - creates SQLAlchemy tables when the database is reachable
  - syncs demo records into the database for supported models
  - prepares the anomaly detection model
- When the database is available, alerts, logs, incidents, and reports are now
  read back from persisted records as well, so core analyst workflow changes
  survive backend restarts instead of existing only in memory.
- Response-action audit history and integration import timestamps/messages also
  persist through the database-backed runtime path when the database is available.
- Seeded user accounts and VirtualBox lab inventory now follow that same
  database-backed runtime path, so login, analyst name lookups, and VM tracking
  continue to work after a restart when PostgreSQL is available.
- Live alert stream readiness and anomaly summaries now read from the merged
  persisted alert view too, so newly imported alerts still appear in those demo
  flows after a restart.
- Imported alert/log context such as integration references, parser status,
  lab-only markers, and finding metadata now persists too, so restart-safe
  workflows keep the same enrichment they had before the reload.
- The Alerts page now supports event-type filtering, and both Alerts and Logs
  detail views expose the preserved import context for analyst review.

- This means a fresh setup already looks populated for presentations.

## Environment files

Copy the example files before running the project.

### Root `.env` for Docker Compose

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

### Frontend and backend env files

```bash
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
```

PowerShell:

```powershell
Copy-Item frontend/.env.example frontend/.env
Copy-Item backend/.env.example backend/.env
```

### Environment variables used

#### Root `.env`

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
- `VITE_API_BASE_URL`
- `VITE_WS_URL`

#### `backend/.env`

- `APP_NAME`
- `APP_ENV`
- `API_PREFIX`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `DATABASE_URL`
- `REDIS_URL`
- `CORS_ORIGINS`

#### `frontend/.env`

- `VITE_APP_NAME`
- `VITE_API_BASE_URL`
- `VITE_WS_URL`

## Local setup

### 1. Backend setup

```bash
cd backend
python -m venv .venv
```

PowerShell:

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional manual demo bootstrap:

```bash
python -m app.seeds.demo_seed
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend URLs:

- API: [http://localhost:8000](http://localhost:8000)
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

- App: [http://localhost:5173](http://localhost:5173)

## Docker setup

### 1. Copy the root env file

```bash
cp .env.example .env
```

### 2. Start the stack

```bash
docker compose up --build
```

Services:

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API: [http://localhost:8000](http://localhost:8000)
- FastAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

Docker notes:

- PostgreSQL and Redis now have health checks.
- Backend waits for PostgreSQL and Redis.
- Frontend waits for the backend.
- The backend bootstraps demo data at startup when the database is reachable.

## Run commands

### Local backend

```bash
cd backend
uvicorn app.main:app --reload
```

### Local frontend

```bash
cd frontend
npm run dev
```

### Optional local demo seed

```bash
cd backend
python -m app.seeds.demo_seed
```

### Docker

```bash
docker compose up --build
```

## Demo credentials

- `admin@aegiscore.local` / `password`
- `analyst@aegiscore.local` / `password`
- `viewer@aegiscore.local` / `password`

Public self-registration is disabled by default for the demo deployment. Use the seeded
accounts above unless you intentionally enable `ALLOW_SELF_REGISTRATION=true` in
`backend/.env`.

## Demo workflow

1. Start the stack locally or with Docker.
2. Sign in with one of the demo users.
3. Open the Dashboard to see seeded alerts, incidents, charts, AI insights,
   and recent activity.
4. Open Alerts and Incidents to review the seeded workflow data.
5. In Alerts, open an alert to review the response-action panel. High-risk imported alerts
   now auto-escalate into investigation and incident workflow, while manual containment
   actions such as IP blocking and asset isolation are recorded as lab-safe simulated
   responses with audit history.
6. Use the alert event-type filter to focus on categories such as authentication,
   file integrity, scan results, or credential assessment, then review the
   preserved parser/import context in the detail panel.
7. Open Integrations and use `Import sample data` on:

   - Wazuh
   - Suricata
   - Nmap
   - Hydra

8. Watch the live alert toast and notification badge update through
   WebSockets when new alerts are imported.
9. Open Reports to generate a report snapshot and export JSON if needed.

## Sample data sources available

The project includes demo/sample sources for:

- Wazuh alert import
- Suricata event import
- Nmap authorized lab-only result ingestion
- Hydra authorized lab-only result ingestion
- Generic log ingestion payloads
- VirtualBox lab environment tracking

Reference files in `docs/`:

- `docs/sample-wazuh-alerts.json`
- `docs/sample-suricata-events.json`
- `docs/sample-nmap-results.json`
- `docs/sample-hydra-results.json`
- `docs/sample-log-ingest-payloads.json`

## How to import sample data

### Recommended demo path

Use the **Integrations** page in the frontend:

- Wazuh card -> `Import sample data`
- Suricata card -> `Import sample data`
- Nmap card -> `Import sample data`
- Hydra card -> `Import sample data`

Use the **Logs** page to inspect log entries and compare raw vs normalized data.

### Important safety boundary

Nmap and Hydra support is limited to:

- importing previously generated authorized lab results
- parsing safe structured outputs
- converting them into alerts/findings
- visualizing them inside the SOC workflow

No offensive execution, automation, remote control, or attack launching is implemented.

## AI anomaly detection

AegisCore includes a small, explainable anomaly detection layer built with scikit-learn.

### What features are used

- alert severity
- hour of day
- after-hours indicator
- source frequency
- source-tool frequency
- service or port activity
- keyword counts from login, credential, network, and service-related text

### How the anomaly score is generated

- the backend trains an `IsolationForest` model on demo SOC events
- each alert is converted into a simple numeric feature set
- the model generates an outlier score
- the score is normalized into a clear demo-friendly anomaly score between
  `0.0` and `1.0`
- short explanations are attached, such as:

  - `unusual login volume`
  - `abnormal source frequency`
  - `unusual service/port activity`

### Where it appears

- Dashboard AI insights widget
- Alerts list and alert detail panels
- Reports summary and anomaly sections

### Why it fits a student project

- easy to explain during a viva or demo
- lightweight enough for local development
- simple to retrain on demo data
- readable output instead of opaque model responses

## Backend overview

Main backend modules:

- `auth`
- `dashboard`
- `alerts`
- `incidents`
- `logs`
- `reports`
- `integrations`
- `ml`
- `websocket`

Important routes:

- `GET /health`
- `POST /auth/login`
- `GET /dashboard/summary`
- `GET /alerts`
- `GET /incidents`
- `POST /logs/ingest`
- `GET /reports/summary`
- `POST /reports/generate`
- `POST /integrations/wazuh/import`
- `POST /integrations/suricata/import`
- `POST /integrations/nmap/import`
- `POST /integrations/hydra/import`
- `WS /ws/alerts`

## Frontend overview

Main frontend pages:

- Login
- Dashboard
- Alerts
- Incidents
- Logs
- Reports
- Integrations
- Settings

Shared UI includes:

- branded sidebar and header
- live alert toast
- summary cards
- charts
- data tables
- filters and detail panels

## Validation checklist

Useful commands while developing:

```bash
cd backend
python -m compileall app
```

```bash
cd frontend
npm run build
```

## Notes for students

- Start with Docker if you want the easiest setup for PostgreSQL and Redis.
- Start with local `uvicorn` + `npm run dev` if you want faster
  frontend/backend iteration.
- The app already includes seeded demo content, so you do not need to build
  business logic first to get a good presentation flow.
- If PostgreSQL is not available locally, the frontend and most backend demo
  flows still work because the main presentation data is seeded in memory.
