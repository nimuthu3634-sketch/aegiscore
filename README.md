# AegisCore

AegisCore is a final-year university project: an AI-integrated Security Operations Center (SOC) web application for lab-based cybersecurity monitoring and incident management.

This repository is scaffolded as a production-style monorepo with a React frontend, FastAPI backend, PostgreSQL, Redis, WebSockets, and starter AI/ML modules for anomaly detection. It is intentionally focused on clean structure, theme setup, routing, and API organization rather than full business logic.

## Stack

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Recharts

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- WebSockets

### AI and data
- scikit-learn
- pandas
- numpy

### Auth
- JWT scaffold with roles: `admin`, `analyst`, `viewer`

### Deployment
- Docker Compose

## Repository structure

```text
.
|-- frontend/
|-- backend/
|-- docker/
|-- docs/
|-- assets/
|-- docker-compose.yml
|-- README.md
|-- AGENTS.md
```

## Quick start

### 1. Copy env templates

Create local env files from the examples:

```bash
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
```

If you are on Windows PowerShell:

```powershell
Copy-Item frontend/.env.example frontend/.env
Copy-Item backend/.env.example backend/.env
```

### 2. Start the stack with Docker Compose

```bash
docker compose up --build
```

Services:
- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API: [http://localhost:8000](http://localhost:8000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

## Frontend notes

- The app shell includes a dark sidebar, top navbar, responsive content area, and branded orange accents.
- Placeholder pages are scaffolded for Login, Dashboard, Alerts, Incidents, Reports, Integrations, and Settings.
- The shared logo asset is located at `assets/aegiscore-logo.svg`.
- Theme colors are configured in `frontend/tailwind.config.cjs`.

## Backend notes

- Routes are grouped into `auth`, `dashboard`, `alerts`, `incidents`, `logs`, `reports`, `integrations`, and `websocket`.
- Starter SQLAlchemy models and Pydantic schemas are separated into clean folders.
- Health check endpoint: `GET /health`
- JWT auth, login, registration, and current-user lookup are scaffolded for the demo flow.
- A simple Isolation Forest module scores alerts for anomaly likelihood and generates short explanation text for the dashboard and alerts queue.

Demo users:
- `admin@aegiscore.local` / `password`
- `analyst@aegiscore.local` / `password`
- `viewer@aegiscore.local` / `password`

## Seed and demo data

A starter seed script is included:

```bash
python -m app.seeds.demo_seed
```

Run it from the `backend/` directory after the database is available.

## AI anomaly detection

AegisCore includes a small, explainable anomaly-detection prototype built with scikit-learn.

What features are used:
- alert severity
- hour of day
- after-hours indicator
- source frequency
- source-tool frequency
- service and port activity
- keyword counts from login, credential, network, and service-related text

How the anomaly score is generated:
- the backend trains an `IsolationForest` model on seeded demo SOC events that represent normal classroom activity
- each incoming alert is converted into a small feature set
- the model produces an outlier score, which is normalized into an easy-to-read anomaly score between `0.0` and `1.0`
- simple rules then generate short explanations such as `unusual login volume`, `abnormal source frequency`, or `unusual service/port activity`

Why this fits a student SOC prototype:
- the model is lightweight and easy to retrain on demo data
- the feature set is understandable during presentations and reports
- the explanations stay human-readable instead of relying on opaque AI output
- the implementation is simple enough to extend later with real logs or better training data

## Safety boundary

This project is for defensive, lab-based monitoring only.

- Wazuh and Suricata are intended as ingestion sources.
- Nmap and Hydra support must remain limited to safe lab-only result ingestion, parsing, simulation, and visualization.
- Do not add offensive security automation.

## Recommended next implementation steps

1. Replace the in-memory auth/data store with PostgreSQL-backed persistence.
2. Add CRUD endpoints backed by SQLAlchemy sessions instead of placeholder service data.
3. Implement ingestion parsers for Wazuh, Suricata, and safe lab-result files.
4. Connect dashboard data pages to backend resources beyond auth.
5. Add seed fixtures for presentation-ready alerts, incidents, logs, and reports.
