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
- A real-world dataset workflow is now available for the LANL Comprehensive
  dataset, so you can upload official `auth.txt.gz`, `dns.txt.gz`, and
  `flows.txt.gz` slices without committing the raw dataset into Git.
- The Alerts page now supports event-type filtering, and both Alerts and Logs
  detail views expose the preserved import context for analyst review.
- Incident details now include linked alert intelligence such as event type,
  AI score, parser/import context, and a quick jump back to the originating
  alert.

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

## Hosting recommendation

For this repository, the cleanest deployment split is:

- **Frontend:** Vercel
- **Backend API:** Render Web Service
- **Database:** Render PostgreSQL
- **Cache / pub-sub:** Render Key Value

This repo now includes:

- [render.yaml](/Users/nimuthusil99460/Documents/GitHub/aegiscore/render.yaml) for the Render backend stack
- [backend/Dockerfile.render](/Users/nimuthusil99460/Documents/GitHub/aegiscore/backend/Dockerfile.render) for the Render API image
- [frontend/vercel.json](/Users/nimuthusil99460/Documents/GitHub/aegiscore/frontend/vercel.json) for Vercel SPA routing

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

## Deploying to Render and Vercel

### 1. Deploy the backend on Render

1. Push the repo to GitHub.
2. In Render, create a new **Blueprint** and point it to this repository.
3. Render will detect [render.yaml](/Users/nimuthusil99460/Documents/GitHub/aegiscore/render.yaml) and provision:

   - `aegiscore-api`
   - `aegiscore-postgres`
   - `aegiscore-redis`

4. In the Render Blueprint form, set `CORS_ORIGINS` to your frontend URL.

Recommended first value:

- `https://<your-vercel-project>.vercel.app`

If you later attach a custom domain, use:

- `https://<your-vercel-project>.vercel.app,https://app.yourdomain.com`

Render-managed backend values from the Blueprint:

- `APP_NAME=AegisCore`
- `APP_ENV=production`
- `API_PREFIX=`
- `ACCESS_TOKEN_EXPIRE_MINUTES=60`
- `ALLOW_SELF_REGISTRATION=false`
- `SECRET_KEY` is auto-generated by Render
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT` are wired from Render Postgres
- `REDIS_URL` is wired from Render Key Value

The backend health check path is:

- `/health`

After the first deploy, note the backend URL. It will look similar to:

- `https://aegiscore-api.onrender.com`

### 2. Deploy the frontend on Vercel

1. In Vercel, import the same GitHub repository.
2. Set the **Root Directory** to `frontend`.
3. Vercel will use [frontend/vercel.json](/Users/nimuthusil99460/Documents/GitHub/aegiscore/frontend/vercel.json) for SPA rewrites and [frontend/package.json](/Users/nimuthusil99460/Documents/GitHub/aegiscore/frontend/package.json) for the build.
4. Add these environment variables in Vercel:

- `VITE_APP_NAME=AegisCore`
- `VITE_API_BASE_URL=https://aegiscore-api.onrender.com`
- `VITE_WS_URL=wss://aegiscore-api.onrender.com/ws/alerts`

Replace `aegiscore-api.onrender.com` with your actual Render backend hostname.

### 3. Final cross-platform wiring

After Vercel gives you the frontend URL:

1. Go back to Render.
2. Update `CORS_ORIGINS` to the exact Vercel domain.
3. Redeploy the backend if Render does not do it automatically.

If you later add custom domains, use:

- Backend: `https://api.yourdomain.com`
- Frontend: `https://app.yourdomain.com`

Then update the frontend Vercel env vars to:

- `VITE_API_BASE_URL=https://api.yourdomain.com`
- `VITE_WS_URL=wss://api.yourdomain.com/ws/alerts`

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

## Real-world LANL workflow

Use this when you want a public real-world enterprise dataset instead of the
seeded demo payloads.

1. Download the official LANL Comprehensive dataset files outside this repo:
   `auth.txt.gz`, `dns.txt.gz`, or `flows.txt.gz`.
2. Optionally download `redteam.txt.gz` if you want auth imports to recognize
   known compromise paths from the LANL ground-truth file.
3. Open the **Integrations** page and find the **LANL Comprehensive dataset**
   section.
4. Choose a dataset type:

   - `Authentication` for `auth.txt.gz`
   - `DNS` for `dns.txt.gz`
   - `Network flows` for `flows.txt.gz`

5. Set a reasonable `Max records` value such as `1000` for the first import.
6. Upload the dataset file. For auth imports, optionally upload the red-team
   file as well.
7. Review the generated alerts in **Alerts**, the normalized records in
   **Logs**, and the aggregated source counts in **Dashboard** and **Reports**.

LANL import notes:

- raw LANL files are not bundled into this repository
- AegisCore preserves the LANL event ordering by anchoring imported relative
  times at import time
- imported LANL records are marked as real-world imports, not lab-only demo
  artifacts
- a small prep utility is available at `scripts/lanl_prepare.py` for download
  and slicing workflows

## Sample data sources available

The project includes demo/sample sources for:

- Wazuh alert import
- Suricata event import
- Nmap authorized lab-only result ingestion
- Hydra authorized lab-only result ingestion
- Generic log ingestion payloads
- VirtualBox lab environment tracking

The project also supports importing the real-world **LANL Comprehensive**
dataset through the Integrations page, but those raw files are intentionally
not stored in the repository because of their size.

Reference files in `docs/`:

- `docs/sample-wazuh-alerts.json`
- `docs/sample-suricata-events.json`
- `docs/sample-nmap-results.json`
- `docs/sample-hydra-results.json`
- `docs/sample-log-ingest-payloads.json`

## Local raw dataset folders

The repository now includes a tracked `data/` scaffold so you have a clear
place to keep raw datasets locally without committing the files themselves.

Use:

- `data/lanl/raw/` for official LANL raw files
- `data/lanl/prepared/` for smaller LANL slices and summaries
- `data/imports/wazuh/` for local Wazuh JSON payloads
- `data/imports/suricata/` for local Suricata JSON payloads
- `data/imports/nmap/` for local Nmap JSON payloads
- `data/imports/hydra/` for local Hydra JSON payloads
- `data/unsw_nb15/raw/` for local UNSW-NB15 source CSV files
- `data/unsw_nb15/prepared/` for merged or cleaned UNSW-NB15 outputs
- `data/cicids2017/raw/` for local CICIDS2017 source CSV files
- `data/cicids2017/prepared/` for merged or cleaned CICIDS2017 outputs

Only the folder placeholders and README files are tracked. Actual dataset files
remain ignored by Git.

## Preparing UNSW-NB15 and CICIDS2017

Use the public-dataset prep script when you want clean, merged CSV files for
defensive analytics, presentation-friendly slices, or future ML experiments.

If your files live outside the repo, register them once in the local manifest:

```powershell
py scripts/register_local_datasets.py `
  --path "E:\New\NUSW-NB15_features.csv" `
  --path "E:\New\UNSW_NB15_training-set.csv" `
  --path "E:\New\UNSW_NB15_testing-set.csv" `
  --path "E:\New\UNSW-NB15_1.csv" `
  --path "E:\New\UNSW-NB15_2.csv" `
  --path "E:\New\UNSW-NB15_3.csv" `
  --path "E:\New\UNSW-NB15_4.csv" `
  --path "E:\New\UNSW-NB15_LIST_EVENTS.csv" `
  --path "E:\Monday-WorkingHours.pcap_ISCX.csv" `
  --path "E:\Tuesday-WorkingHours.pcap_ISCX.csv" `
  --path "E:\Wednesday-workingHours.pcap_ISCX.csv" `
  --path "E:\Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv" `
  --path "E:\Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv" `
  --path "E:\Friday-WorkingHours-Morning.pcap_ISCX.csv" `
  --path "E:\Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv" `
  --path "E:\Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"
```

Prepare both dataset families from that manifest:

```powershell
py scripts/prepare_public_datasets.py all --max-rows-per-label 3000
```

Or prepare them individually:

```powershell
py scripts/prepare_public_datasets.py unsw_nb15 --source auto --max-rows-per-label 3000
py scripts/prepare_public_datasets.py cicids2017 --max-rows-per-label 3000
```

Outputs:

- `data/unsw_nb15/prepared/unsw_nb15_prepared.csv`
- `data/unsw_nb15/prepared/unsw_nb15_prepared.summary.json`
- `data/cicids2017/prepared/cicids2017_prepared.csv`
- `data/cicids2017/prepared/cicids2017_prepared.summary.json`

Notes:

- `UNSW-NB15` auto mode prefers the labeled training/testing splits when they
  are available in the manifest. If they are not present, the script falls back
  to the raw split files plus the feature reference CSV.
- `CICIDS2017` headers are normalized into stable lowercase snake_case columns.
- `--max-rows-per-label` is optional but recommended for student-demo workflows
  so the merged outputs stay manageable.

## How to import sample data

### Recommended demo path

Use the **Integrations** page in the frontend:

- Wazuh card -> `Import sample data`
- Suricata card -> `Import sample data`
- Nmap card -> `Import sample data`
- Hydra card -> `Import sample data`

Use the **Logs** page to inspect log entries and compare raw vs normalized data.

## LANL preparation utility

Use the LANL prep utility when you want a smaller upload-friendly slice of the
real-world dataset instead of a huge raw file.

Important note:

- the script does not bypass the official LANL request/download flow
- get the direct official file URL from the LANL dataset page first, then use
  the `download` command below

Activate the backend virtual environment first so the script can reuse the same
LANL parsers as the API.

### Download an official LANL file

```bash
python scripts/lanl_prepare.py download \
  --dataset-type auth \
  --url "<direct official LANL file URL>"
```

PowerShell:

```powershell
py scripts/lanl_prepare.py download `
  --dataset-type auth `
  --url "<direct official LANL file URL>"
```

By default, downloads are stored in `data/lanl/raw/`, which is ignored by Git.

### Prepare a smaller LANL auth slice

```bash
python scripts/lanl_prepare.py prepare \
  --dataset-type auth \
  --input data/lanl/raw/auth.txt.gz \
  --output data/lanl/prepared/auth-alert-candidates-1500.txt.gz \
  --redteam-input data/lanl/raw/redteam.txt.gz \
  --only-alert-candidates \
  --max-records 1500 \
  --summary-json data/lanl/prepared/auth-alert-candidates-1500.summary.json
```

PowerShell:

```powershell
py scripts/lanl_prepare.py prepare `
  --dataset-type auth `
  --input data/lanl/raw/auth.txt.gz `
  --output data/lanl/prepared/auth-alert-candidates-1500.txt.gz `
  --redteam-input data/lanl/raw/redteam.txt.gz `
  --only-alert-candidates `
  --max-records 1500 `
  --summary-json data/lanl/prepared/auth-alert-candidates-1500.summary.json
```

Useful prep options:

- `--only-alert-candidates`: for `auth`, keeps failed logons and red-team matches;
  for `flows`, keeps sensitive or high-volume records
- `--skip-records`: skips a number of selected rows before writing the slice
- `--summary-json`: writes a quick machine-readable summary you can keep with the slice

Recommended first runs:

- `auth`: use `--only-alert-candidates --max-records 1000`
- `dns`: use `--max-records 1000` first, because DNS alerts are volume-based
- `flows`: use `--only-alert-candidates --max-records 1000`

After preparing a slice, upload the resulting `.txt.gz` file through the
**Integrations** page. For auth imports, upload the prepared red-team file in
the optional red-team field as well.

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
- `GET /integrations/lanl/status`
- `POST /integrations/lanl/import`
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
