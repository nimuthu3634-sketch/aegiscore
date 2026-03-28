# AegisCore Architecture Notes

## Monorepo shape

- `frontend/`: React + TypeScript + Vite SOC interface
- `backend/`: FastAPI API, persistence, ingestion, and ML services
- `assets/`: shared brand assets including the AegisCore logo
- `docs/`: sample payloads and project notes
- `data/`: local dataset workspace for imports and ML preparation

## Platform purpose

- AegisCore is a lab-based AI-integrated SOC web application for small organizations.
- The project is intentionally built for a university VM lab and academic demo, not for enterprise deployment.
- Core detections are limited to four demo-friendly threat categories:
  brute-force attacks, file-integrity violations, port scans, and unauthorized user-account creation.
- Wazuh and Suricata perform the primary detection work. The custom web app prioritizes, explains, and tracks those detections.

## Five-layer workflow

- Data collection: Wazuh agents collect endpoint telemetry and Suricata monitors network traffic.
- Detection: Wazuh handles endpoint and account-focused detections, while Suricata covers network-focused detections such as reconnaissance and port scans.
- AI prioritization: FastAPI services use Python, pandas, numpy, and scikit-learn to assign anomaly and risk context to incoming alerts.
- Web application: React, Tailwind CSS, Recharts, FastAPI, PostgreSQL, Redis, WebSockets, JWT auth, and NGINX provide the dashboard, APIs, and live updates.
- Automated response: lab-safe simulated actions such as incident creation, temporary source-IP blocking, account disabling, and asset isolation can be triggered for high-risk alerts.

## Frontend approach

- Route-based pages for `dashboard`, `alerts`, `incidents`, `logs`, `analytics`,
  `integrations`, `settings`, and `login`
- Shared layout and reusable cards, charts, tables, badges, and detail panels
- Dark sidebar, light content area, orange accent system from the project guide
- Simple state handling with page-level data fetching from the FastAPI backend

## Backend approach

- FastAPI routers under `backend/app/routers`
- Shared configuration under `backend/app/core`
- SQLAlchemy models under `backend/app/models`
- Pydantic schemas under `backend/app/schemas`
- Reusable business logic under `backend/app/services`
- Parser and normalization logic under `backend/app/ingestion`
- Explainable anomaly logic under `backend/app/ml`
- WebSocket handlers under `backend/app/ws`

## Supported platform workflow

- Authentication with `Admin`, `Analyst`, and `Viewer`
- Dashboard summaries and charts
- Alert triage and detail drill-down
- Incident workflow and assignment
- Log review
- Integration status and sample imports for Wazuh, Suricata, Nmap, and Hydra
- Explainable anomaly summaries and model results
- Lab-safe automated and analyst-triggered response actions

## Scope boundaries

- No LANL workflow
- No VirtualBox inventory subsystem
- No enterprise reporting module
- No offensive execution of Nmap, Hydra, or related tools
- No scan launching, brute-force execution, exploitation, or active targeting workflows

## Recommended lab deployment

- Minimum workable lab: `4` VMs
- Recommended demo lab: `5` VMs
- Primary SOC OS: Ubuntu Server `24.04 LTS`
- Practical topology: SOC core VM, monitored Linux endpoint, second monitored endpoint, attacker VM, and optionally a separate app VM
- Preferred network shape: internal lab network for attack traffic, NAT for updates, and host-only access for the dashboard demo

## Development guidance

- Keep the project easy to demo and easy to explain.
- Prefer readable files and explicit API contracts over deep abstraction.
- Keep frontend, backend, ingestion, and ML responsibilities separated.
- Update the README whenever setup, routes, or supported workflows change.
