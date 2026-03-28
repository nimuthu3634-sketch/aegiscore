# AegisCore Architecture Notes

## Monorepo shape

- `frontend/`: React + TypeScript + Vite SOC interface
- `backend/`: FastAPI API, persistence, ingestion, and ML services
- `assets/`: shared brand assets including the AegisCore logo
- `docs/`: sample payloads and project notes
- `data/`: local dataset workspace for imports and ML preparation

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
- Manual, lab-safe guided response actions

## Scope boundaries

- No LANL workflow
- No VirtualBox inventory subsystem
- No enterprise reporting module
- No autonomous response automation
- No offensive execution of Nmap, Hydra, or related tools

## Development guidance

- Keep the project easy to demo and easy to explain.
- Prefer readable files and explicit API contracts over deep abstraction.
- Keep frontend, backend, ingestion, and ML responsibilities separated.
- Update the README whenever setup, routes, or supported workflows change.
