# AegisCore Agent Guide

## Project overview
AegisCore is a final-year university project: an AI-integrated Security Operations Center (SOC) web application for lab-based cybersecurity monitoring and incident management.

This repository should prioritize a working academic demo over enterprise-scale complexity. Build practical, understandable features that are easy for students to present, explain, maintain, and extend.

## Core goals
- Build a working SOC dashboard and analyst workflow system.
- Ingest and visualize logs and alerts from lab tools.
- Support Wazuh and Suricata log ingestion.
- Use Python and scikit-learn for anomaly detection.
- Support safe, lab-only simulation data from Nmap and Hydra outputs.
- Provide role-based access for `Admin`, `Analyst`, and `Viewer`.
- Deliver a clean, modern UI aligned to the AegisCore logo colors.

## Non-negotiable safety boundaries
- Do not add offensive security automation.
- Nmap and Hydra support must be limited to safe lab-only result ingestion, parsing, simulation, and visualization.
- Do not generate features that execute scans, brute-force attacks, exploitation steps, or active targeting workflows.
- Treat this as a defensive monitoring and incident management platform for controlled lab environments only.

## Recommended engineering approach
- Build in phases.
- Scaffold first, then implement features incrementally.
- Ensure each phase compiles or runs before moving to the next.
- Prefer simple, student-friendly architecture over clever abstractions.
- Keep frontend and backend clearly separated.
- Add seed or demo data for academic presentations and screenshots.
- Update `README.md` whenever setup, run steps, environment variables, or architecture assumptions change.

## Primary stack

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

### Deployment
- Docker Compose

## Implementation principles
- Prefer readable code over dense abstractions.
- Use typed schemas and interfaces throughout the stack.
- Keep components reusable, small, and purpose-driven.
- Add concise comments only when they clarify non-obvious logic.
- Avoid unnecessary dependencies.
- Favor predictable folder structure and naming.
- Keep API contracts explicit and stable.
- Use environment variables for secrets and configuration.
- Provide `.env.example` files instead of hardcoding secrets.

## UI and design guidance
- Use the logo file at `assets/aegiscore-logo.svg`.
- Keep the UI professional, minimal, and dashboard-focused.
- Use a dark sidebar, light content area, and orange accent color.
- Make the layout responsive for laptop and presentation-screen use.
- Avoid visual clutter and unnecessary animations.
- Prefer strong information hierarchy, clear charts, and readable tables.

### Design tokens
- Primary orange: `#FF7A1A`
- Primary black: `#111111`
- Dark surface: `#1A1A1A`
- Muted gray: `#D9D9D9`
- Light background: `#F3F3F3`
- White: `#FFFFFF`

## Product scope guidance

### Should exist
- SOC overview dashboard
- Alert list and alert detail views
- Incident workflow or case tracking
- Log ingestion pipelines for Wazuh and Suricata data
- Anomaly detection summaries and model results
- Role-based access control for `Admin`, `Analyst`, and `Viewer`
- Demo or seed datasets for walkthroughs
- Real-time or near-real-time updates where useful

### Should stay simple
- Authentication and authorization
- Ingestion pipelines
- Case management workflow
- ML model lifecycle
- Charting and filtering interactions

### Avoid for this project
- Multi-tenant enterprise architecture
- Complex plugin systems
- Premature microservices
- Advanced orchestration beyond Docker Compose
- Overbuilt design systems

## Suggested development phases
1. Scaffold frontend, backend, database, Docker Compose, and shared environment configuration.
2. Build the base UI shell: sidebar, top bar, dashboard layout, routing, and theme tokens.
3. Add backend models, schemas, and CRUD endpoints for users, alerts, incidents, and log records.
4. Implement lab-log ingestion flows for Wazuh, Suricata, and safe Nmap/Hydra result parsing.
5. Add dashboards, charts, tables, filters, and alert drill-down screens.
6. Add anomaly detection pipelines with explainable output suitable for presentation.
7. Add WebSocket or polling updates for live dashboard behavior.
8. Seed demo data, polish UX, validate Docker setup, and update documentation.

## Backend guidance
- Use FastAPI routers grouped by domain.
- Use Pydantic schemas for request and response typing.
- Keep SQLAlchemy models close to business entities and avoid duplicating schema logic.
- Isolate ingestion and parsing logic from API route handlers.
- Keep anomaly detection code separate from transport or database code.
- Use service modules for reusable business logic when route handlers start to grow.
- Add clear validation around uploaded or imported lab files.
- Fail safely on malformed input and return helpful API errors.

## Frontend guidance
- Use route-based pages for major areas such as dashboard, alerts, incidents, logs, analytics, and settings.
- Keep chart components reusable and presentation-focused.
- Centralize API clients and shared TypeScript types.
- Prefer composable layout and table components over page-specific duplication.
- Keep state management simple unless a clear shared-state need emerges.
- Use loading, empty, and error states on all data-driven screens.

## Data and AI guidance
- Start with simple anomaly detection approaches that are explainable in an academic setting.
- Favor techniques such as Isolation Forest, clustering, or statistical outlier detection before attempting heavier models.
- Keep training and inference workflows reproducible.
- Document the meaning of scores, thresholds, and features.
- Use demo-friendly datasets and deterministic seeds where possible.
- Clearly separate simulated lab data from real operational assumptions.

## Configuration and deployment
- Keep local development centered around Docker Compose.
- Separate config by environment using environment variables.
- Do not commit secrets, credentials, or local database dumps.
- Provide a straightforward local startup path for lecturers, teammates, and reviewers.

## Testing and quality expectations
- Make each new phase runnable before expanding scope.
- Add lightweight tests where they give clear value, especially for parsers, schemas, and core API flows.
- Prefer a few reliable tests over a large brittle suite.
- Verify the frontend builds cleanly and the backend starts cleanly after meaningful changes.

## Documentation expectations
- Keep `README.md` current with setup, architecture, environment variables, demo flow, and run commands.
- Document any seeded accounts, demo scenarios, and sample datasets.
- If adding a new subsystem, include a short explanation of its purpose and how to run it.

## Preferred folder conventions

### Repository root
Use a clear two-app structure with supporting top-level folders:

```text
/
|-- frontend/
|-- backend/
|-- assets/
|-- docs/
|-- docker-compose.yml
|-- .env.example
|-- README.md
|-- AGENTS.md
```

### Frontend conventions
Preferred React app layout:

```text
frontend/
|-- public/
|-- src/
|   |-- app/
|   |-- assets/
|   |-- components/
|   |-- features/
|   |-- layouts/
|   |-- pages/
|   |-- routes/
|   |-- services/
|   |-- hooks/
|   |-- types/
|   |-- utils/
|   |-- styles/
|   |-- data/
|   |-- main.tsx
|-- index.html
|-- package.json
|-- tsconfig.json
|-- vite.config.ts
```

Frontend folder intent:
- `src/app/`: app bootstrap, providers, global config
- `src/components/`: reusable UI components
- `src/features/`: domain-focused UI logic such as alerts, incidents, auth, analytics
- `src/layouts/`: shell layouts such as sidebar and dashboard frames
- `src/pages/`: top-level route screens
- `src/routes/`: route definitions and guards
- `src/services/`: API clients, WebSocket clients, adapters
- `src/hooks/`: reusable React hooks
- `src/types/`: shared TypeScript interfaces and DTOs
- `src/utils/`: pure helpers and formatters
- `src/styles/`: Tailwind entry styles, tokens, or shared CSS
- `src/data/`: seed data or static demo content for the frontend

### Backend conventions
Preferred FastAPI app layout:

```text
backend/
|-- app/
|   |-- api/
|   |-- core/
|   |-- db/
|   |-- models/
|   |-- schemas/
|   |-- services/
|   |-- ingestion/
|   |-- ml/
|   |-- ws/
|   |-- seeds/
|   |-- utils/
|   |-- main.py
|-- tests/
|-- requirements.txt
|-- Dockerfile
```

Backend folder intent:
- `app/api/`: FastAPI routers and endpoint registration
- `app/core/`: settings, security config, constants
- `app/db/`: database session, base model setup, migrations integration
- `app/models/`: SQLAlchemy models
- `app/schemas/`: Pydantic request and response schemas
- `app/services/`: domain business logic
- `app/ingestion/`: Wazuh, Suricata, Nmap, and Hydra lab-result parsing and normalization
- `app/ml/`: anomaly detection pipelines, feature prep, model helpers
- `app/ws/`: WebSocket handlers and real-time event helpers
- `app/seeds/`: demo data loaders and academic presentation fixtures
- `app/utils/`: small shared backend helpers
- `tests/`: parser, schema, service, and API tests

## Naming and structure preferences
- Keep filenames descriptive and consistent.
- Prefer singular or domain-consistent naming for models and schemas.
- Co-locate related logic, but avoid mixing API, ML, and parsing responsibilities in the same module.
- Split files when they become hard to scan, not preemptively.

## Agent instructions for future work
- Respect the student-project scope and avoid unnecessary complexity.
- Preserve clear separation between frontend, backend, ingestion, and ML responsibilities.
- When adding setup steps or new services, update `README.md`.
- When adding new UI, follow the AegisCore color system and dashboard-first layout.
- When handling Nmap or Hydra content, keep support strictly limited to safe lab-result ingestion, parsing, simulation, and visualization.
- Prefer deliverable, working increments over broad unfinished scaffolding.
