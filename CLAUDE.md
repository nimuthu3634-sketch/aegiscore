# AegisCore — Claude Code Operational Guide

## Project summary

AegisCore is an AI-integrated Security Operations Center (SOC) web platform built as a university capstone project (ECU CSG3101.2, Group 36). It is a working system — not a demo shell — with real ingestion pipelines, real ML scoring, real auth/RBAC, and real alert/incident workflows.

Stack: FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis (backend), Next.js 15 + TypeScript + TailwindCSS (frontend), scikit-learn (ML), RQ (background jobs), Docker Compose (runtime), Alembic (schema migrations), Playwright + pytest (tests).

---

## Running the system

```bash
# Full stack (first boot, no data)
docker compose up --build

# With seed demo data (creates users, alerts, incidents, trains model)
docker compose --profile seed up --build

# Dev mode (hot reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Access: http://localhost:8080 (web via nginx), http://localhost:8080/api/v1/docs (Swagger).

Default demo credentials (seed only):
- admin@example.com / Admin123!
- analyst@example.com / Analyst123!
- viewer@example.com / Viewer123!

---

## Key architecture facts

### Auth
- JWT (HS256) issued as HTTP-only cookie on login
- `JWT_SECRET_KEY` env var — change from default in production
- Rate limiting on login: Redis sliding-window backed, falls back to in-memory if Redis unreachable
- Three roles: Admin > Analyst > Viewer — enforced at FastAPI dependency layer

### Database schema
- **Alembic migration:** `apps/api/alembic/versions/20260329_0001_initial.py` uses explicit `op.create_table()` DDL — safe to add subsequent migrations
- **Incident references:** Generated from PostgreSQL sequence `incident_reference_seq` — collision-safe under concurrent creates
- **All tables:** roles, users, assets, integrations, integration_runs, alerts, response_recommendations, alert_comments, incidents, incident_events, incident_alert_links, log_entries, audit_logs, risk_model_metadata, job_records

### Ingestion pipeline
`parsers.py → normalization.py → domain.create_alert()` — supports Wazuh (HTTP pull), Suricata (HTTP pull), Nmap (file import only), Hydra (file import only). Fingerprint deduplication prevents exact duplicate log entries.

### ML scoring
- `apps/api/app/ml/scoring.py` — 24-feature extraction, Isolation Forest + Logistic Regression ensemble, 0–100 risk score with top-5 explainability factors
- Model trained via RQ background job (`run_retrain_job`); no blocking at API startup
- Model artifact stored at `apps/api/app/ml/runtime/alert-risk-model.pkl`

### Rate limiting
- `apps/api/app/core/rate_limit.py` — Redis sorted-set sliding window via Lua script
- Falls back to in-memory `_InMemoryRateLimiter` if Redis unavailable (e.g., tests)
- Namespaces: `auth-login`, `integration-write`, `realtime`

### Background jobs
- RQ queue named `ml`, worker in `apps/worker/`
- Only job type: `model_retrain` → trains model, rescores all alerts, writes `ModelMetadata` row
- Job status polled via `GET /api/v1/admin/jobs/{job_id}`

### Integration connectivity test
- `POST /api/v1/integrations/{slug}/test` — sends HEAD/GET to configured endpoint URL, returns `{reachable, status, http_status, latency_ms, detail}`
- Does not ingest data; safe to call anytime
- Lab-only integrations (nmap, hydra) return `status: "import_only"` immediately

### Response actions
- `block_ip`, `isolate_asset`, `disable_user`, `contain_alert` — all return `status: "recorded"`
- These record analyst intent into the audit log and alert comments; they do NOT contact external systems
- The follow_up array gives the analyst the manual steps to execute in their actual tooling

### Asset risk score
- Computed via SQL aggregation on active (non-resolved, non-suppressed) alerts for the asset
- Updated on every `create_alert` and `update_alert` call
- `_refresh_asset_risk(asset, db)` — always pass `db` to use the SQL path; omitting `db` falls back to a Python list comprehension over already-loaded relationships

### Audit log
Covered operations: auth.login, auth.login_failed, auth.logout, auth.profile_updated, user.created, user.updated, alert.created, alert.updated, alert.comment_added, alert.response_executed, incident.created, incident.updated, incident.event_added, integration.config_updated, integration.ingested, integration.connection_tested, ml.scores_recalculated, ml.retrain_queued

---

## Running tests

```bash
cd apps/api
pytest tests/ -v
```

Tests use SQLite in-process (not PostgreSQL). Rate limiter uses the in-memory fallback automatically. Redis is not required for tests.

Test files:
- `tests/conftest.py` — fixtures (bootstrap DB, login helpers, token fixtures)
- `tests/test_auth_and_users.py` — auth, session, user management
- `tests/test_alerts_and_incidents.py` — alert lifecycle, response actions, incident creation
- `tests/test_ingestion_and_dashboard.py` — file import, sync, dashboard aggregations
- `tests/test_ml_scoring.py` — feature extraction, model scoring, training
- `tests/test_health_and_permissions.py` — health checks, RBAC enforcement
- `tests/test_security_hardening.py` — security headers, rate limiting, CORS
- `tests/test_new_features.py` — incident reference uniqueness, asset risk SQL path, recorded response actions, integration test endpoint, rate limiter fallback, retrain audit entry

---

## What NOT to do

- Do not add offensive security automation (active scanning, exploitation, exfiltration).
- Nmap and Hydra must remain lab import-only — no live execution.
- Do not rewrite the ingestion pipeline from scratch — it is domain-complete.
- Do not rewrite the ML scoring pipeline — it is a real implementation with explainability.
- Do not mock the database in tests unless unavoidable — integration tests use a real SQLite DB.

---

## Environment variables (key ones)

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL DSN | `postgresql+psycopg://aegiscore:aegiscore@localhost:5432/aegiscore` |
| `REDIS_URL` | Redis DSN (rate limiting + RQ) | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | JWT signing key — **change in production** | `change-me-in-production` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000,http://localhost:8080` |
| `MODEL_VERSION` | Version prefix on trained model artifacts | `2026.03` |
| `MAX_UPLOAD_SIZE_BYTES` | Max integration file import size | `5242880` (5 MB) |
| `LOGIN_RATE_LIMIT_ATTEMPTS` | Max login attempts per window | `5` |
| `LOGIN_RATE_LIMIT_WINDOW_SECONDS` | Login rate limit window | `60` |

Full list in `apps/api/.env.example`.
