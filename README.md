# AegisCore

AegisCore is a final-year university project: an AI-integrated Security
Operations Center (SOC) web application for lab-based monitoring, alert triage,
incident handling, explainable anomaly detection, and safe classroom-friendly
data ingestion.

The repository is intentionally scoped for an academic demo. It favors clear
workflows, simple architecture, and features that are easy to present, explain,
and extend.

## Proposal-aligned scope

Included:

- role-based access for `Admin`, `Analyst`, and `Viewer`
- dashboard, alerts, incidents, logs, analytics, integrations, and settings
- Wazuh and Suricata ingestion
- safe lab-only ingestion for Nmap and Hydra result files
- explainable anomaly scoring with scikit-learn
- live updates through WebSockets
- manual, analyst-triggered guided response actions

Not included:

- enterprise reporting workflows
- LANL import workflows
- VirtualBox inventory tracking
- autonomous response automation
- offensive execution of Nmap, Hydra, or any other tooling

## Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, React Router, Recharts
- Backend: FastAPI, SQLAlchemy, PostgreSQL, Redis, WebSockets
- AI/Data: scikit-learn, pandas, numpy
- Local deployment: Docker Compose

## Repository structure

```text
.
|-- frontend/
|-- backend/
|-- assets/
|-- docs/
|-- data/
|-- docker-compose.yml
|-- .env.example
|-- README.md
|-- AGENTS.md
```

## Quick start

### Recommended setup

Use Docker for PostgreSQL and Redis, then run the frontend and backend locally
for faster iteration.

1. Copy environment files.

```powershell
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env
Copy-Item backend/.env.example backend/.env
```

1. Start infrastructure.

```powershell
docker compose up -d postgres redis
```

1. Start the backend.

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

1. Start the frontend in a second terminal.

```powershell
cd frontend
npm install
npm run dev
```

URLs:

- frontend: <http://localhost:5173>
- backend: <http://localhost:8000>
- backend docs: <http://localhost:8000/docs>

### Full Docker startup

```powershell
Copy-Item .env.example .env
docker compose up --build
```

## Demo accounts

- `admin@aegiscore.local` / `password`
- `analyst@aegiscore.local` / `password`
- `viewer@aegiscore.local` / `password`

`Viewer` is read-only. Guided response actions are available only to `Admin`
and `Analyst`.

## Demo flow

1. Sign in with a seeded account.
2. Review the live SOC overview on `/dashboard`.
3. Open `/alerts` to triage alerts, review anomaly scores, and inspect import context.
4. Use manual response actions such as incident creation, simulated asset isolation,
   simulated source IP blocking, and simulated account disable actions.
5. Open `/incidents` to assign analysts, update status, and track notes.
6. Open `/logs` to inspect normalized log records.
7. Open `/analytics` to review explainable anomaly summaries and model outputs.
8. Open `/integrations` and import sample Wazuh, Suricata, Nmap, and Hydra data.
9. Watch WebSocket-driven live alert updates appear in the UI.

## Safety boundaries

- Wazuh and Suricata are used for defensive telemetry ingestion.
- Nmap and Hydra support is limited to parsing and visualizing previously
  generated lab results.
- AegisCore does not launch scans, brute-force attempts, exploits, or active
  targeting workflows.
- Response actions are guided, manual, and lab-safe. They are recorded as
  simulated defensive actions inside the SOC workflow.

## Dataset workflow

This repo keeps a local manifest for public datasets used in analytics and ML
experiments.

- `data/local_datasets.json` is a repo-safe template manifest.
- `scripts/register_local_datasets.py` records local dataset file paths.
- `scripts/prepare_public_datasets.py` prepares `UNSW-NB15` and `CICIDS2017`.

Example:

```powershell
py scripts/register_local_datasets.py `
  --path "C:\datasets\UNSW-NB15_features.csv" `
  --path "C:\datasets\UNSW_NB15_training-set.csv" `
  --path "C:\datasets\UNSW_NB15_testing-set.csv" `
  --path "C:\datasets\Monday-WorkingHours.pcap_ISCX.csv"
```

Then prepare datasets:

```powershell
py scripts/prepare_public_datasets.py all --max-rows-per-label 3000
```

Outputs:

- `data/unsw_nb15/prepared/unsw_nb15_prepared.csv`
- `data/unsw_nb15/prepared/unsw_nb15_prepared.summary.json`
- `data/cicids2017/prepared/cicids2017_prepared.csv`
- `data/cicids2017/prepared/cicids2017_prepared.summary.json`

## Important routes

Backend:

- `POST /auth/login`
- `GET /auth/me`
- `GET /dashboard/summary`
- `GET /dashboard/charts`
- `GET /dashboard/anomaly-summary`
- `GET /alerts`
- `GET /alerts/{id}`
- `GET /alerts/{id}/response-actions`
- `POST /alerts/{id}/response-actions`
- `GET /incidents`
- `GET /logs`
- `GET /integrations/status`
- `GET /integrations/{wazuh|suricata|nmap|hydra}/status`
- `POST /integrations/{wazuh|suricata|nmap|hydra}/import`
- `POST /ml/train-demo`
- `WS /ws/alerts`

Frontend:

- `/login`
- `/dashboard`
- `/alerts`
- `/incidents`
- `/logs`
- `/analytics`
- `/integrations`
- `/settings`

## Testing and validation

Backend:

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m pytest -q
```

Frontend:

```powershell
cd frontend
npm run build
```

`pytest` is included in [backend/requirements.txt](backend/requirements.txt) so the backend test suite can run in a fresh virtual environment.

## Notes

- The app can run with seeded demo data even before you import new sample files.
- PostgreSQL-backed persistence is supported when the database is available.
- Keep the repo focused on the student-project scope described in [AGENTS.md](AGENTS.md).
