# AegisCore

AegisCore is a final-year university project: a lab-based, AI-integrated
Security Operations Center (SOC) web application for small organizations. The
platform collects endpoint and network security telemetry, detects four core
threat categories, prioritizes alerts with machine learning, and records
lab-safe response actions inside a guided SOC workflow.

This repository is intentionally scoped for a VM lab and academic demo. It
prioritizes clear workflows, understandable architecture, and features that are
easy for students to explain, test, and extend.

## Project scope

Included:

- role-based access for `Admin`, `Analyst`, and `Viewer`
- SOC dashboard, alerts, incidents, logs, analytics, integrations, and settings
- Wazuh endpoint ingestion and Suricata network ingestion
- safe lab-only ingestion for pre-generated Nmap and Hydra result files
- explainable ML-based alert prioritization with scikit-learn
- live updates through WebSockets
- basic lab-safe automated response actions plus analyst-triggered response actions

Not included:

- enterprise-scale deployment or multi-tenant architecture
- offensive execution of Nmap, Hydra, scans, brute-force attempts, or exploits
- real-world autonomous containment against production systems
- complex orchestration beyond Docker Compose for the current academic build

## Core threat coverage

AegisCore is centered on four demo-friendly threat categories:

- brute-force attacks
- file-integrity violations
- port scans
- unauthorized user-account creation

## Five-layer workflow

1. Data collection: Wazuh agents collect endpoint logs while Suricata monitors
   network traffic.
2. Detection: Wazuh handles endpoint and account-focused detections, and
   Suricata handles network detections such as reconnaissance and port scans.
3. AI prioritization: Python, pandas, numpy, and scikit-learn assign anomaly
   and risk context to incoming alerts.
4. Web application: React, Tailwind CSS, Recharts, FastAPI, PostgreSQL, Redis,
   WebSockets, JWT auth, and NGINX provide the dashboard, APIs, and live SOC
   workflow.
5. Automated response: high-risk alerts can trigger lab-safe simulated actions
   such as incident creation, temporary IP blocking, asset isolation, and
   account disabling.

The design can be summarized as:

`Wazuh + Suricata detect -> FastAPI + ML prioritize -> React dashboard explains -> lab-safe response actions record`

## Stack

- Security and lab tools: Ubuntu Server, VirtualBox, Wazuh, Wazuh Agent,
  Suricata, Nmap, Hydra
- Frontend: React, TypeScript, Vite, Tailwind CSS, React Router, Recharts
- Backend: FastAPI, SQLAlchemy, PostgreSQL, Redis, WebSockets, JWT
- AI/Data: scikit-learn, pandas, numpy
- Local deployment: Docker Compose and NGINX

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

## Recommended lab environment

- Host platform: VirtualBox on a strong Windows or Linux host
- Primary SOC OS: Ubuntu Server `24.04 LTS`
- Minimum workable lab: `4` VMs
- Recommended demo lab: `5` VMs

Minimum workable VM layout:

- `SOC Core VM`: Wazuh all-in-one, Suricata, FastAPI backend, PostgreSQL, NGINX, Docker Compose
- `Monitored Linux Endpoint VM`: Wazuh agent for brute-force, FIM, and account-creation scenarios
- `Second Monitored Endpoint VM`: Windows or Ubuntu with Wazuh agent
- `Attacker VM`: Kali Linux or Ubuntu for controlled Nmap and Hydra lab simulations

Recommended network shape:

- internal network for lab traffic
- NAT for package updates
- host-only adapter for dashboard access from the host machine

## Quick start

### Recommended development setup

Use Docker for PostgreSQL, Redis, and NGINX, then run the frontend and backend
locally for faster iteration.

1. Copy environment files.

```powershell
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env
Copy-Item backend/.env.example backend/.env
```

1. Start shared infrastructure.

```powershell
docker compose up -d postgres redis nginx
```

1. Start the backend.

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

If you prefer activation in PowerShell and script execution is blocked, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

1. Start the frontend in a second terminal.

```powershell
cd frontend
npm install
npm run dev
```

URLs:

- frontend dev server: <http://localhost:5173>
- backend API: <http://localhost:8000>
- backend docs: <http://localhost:8000/docs>
- NGINX entrypoint: <http://localhost:8081>

When running through nginx on `8081`, the frontend still talks to the backend API
on `8000` and the WebSocket endpoint on `8000` to avoid route collisions with
frontend pages such as `/alerts`, `/incidents`, and `/logs`.

### Full Docker startup

```powershell
Copy-Item .env.example .env
docker compose up --build
```

## Demo accounts

- `admin@aegiscore.local` / `password`
- `analyst@aegiscore.local` / `password`
- `viewer@aegiscore.local` / `password`

`Viewer` is read-only. `Admin` and `Analyst` accounts can run manual response
actions, while high-risk alerts may also show automated lab-safe response
records in the audit history.

## Demo flow

1. Sign in with a seeded account.
2. Review the SOC overview on `/dashboard`.
3. Open `/alerts` to triage detections from Wazuh, Suricata, Nmap, and Hydra.
4. Inspect anomaly scores and risk context for the four core threat categories.
5. Review automated response history and optionally run manual simulated actions.
6. Open `/incidents` to assign analysts, update status, and track notes.
7. Open `/logs` to inspect normalized endpoint and network events.
8. Open `/analytics` to review explainable anomaly summaries and model outputs.
9. Open `/integrations` and import sample Wazuh, Suricata, Nmap, and Hydra data.
10. Watch WebSocket-driven live alert updates appear in the UI.

## Safety boundaries

- Wazuh and Suricata are used for defensive telemetry ingestion and detection.
- Nmap and Hydra support is limited to parsing, simulating, and visualizing
  previously generated lab results.
- AegisCore does not launch scans, brute-force attempts, exploits, or active
  targeting workflows.
- Automated responses are lab-safe simulated SOC actions recorded for the demo
  workflow only. They are not production containment automation.

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
.\.venv\Scripts\python.exe -m pytest -q
```

Frontend:

```powershell
cd frontend
npm run build
```

`pytest` is included in `backend/requirements.txt` so the backend test suite can
run in a fresh virtual environment.

## Notes

- The app can run with seeded demo data even before you import new sample files.
- PostgreSQL-backed persistence is supported when the database is available.
- Keep the repo focused on the student-project scope described in `AGENTS.md`.
