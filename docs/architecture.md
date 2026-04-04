# Detailed Working Document
## AI-Integrated SOC Web Application

How the system operates, how data flows, and how each project component fits together.

Document basis: the project starts with initiation, literature review, requirements definition, tool selection, proposal preparation, and proposal submission. This document extends that planning phase into a practical explanation of how the implemented AegisCore system operates.

## 1. Executive Summary

This project delivers a small Security Operations Center (SOC) platform that combines security monitoring tools with a web application and an AI-based alert prioritization module. Its goal is to collect security data from monitored systems, detect suspicious activity, rank alerts by risk, and present actionable views in a dashboard analysts can triage quickly.

In operational terms, endpoints and network sensors generate events, monitoring tools detect activity, the backend ingests and stores normalized records, the AI module assigns risk scores, and the frontend presents incidents, trends, and priority-focused alert queues.

## 2. What the System Is Meant to Do

- Collect security-relevant events from monitored endpoints and network traffic.
- Detect suspicious behavior (for example brute-force patterns, integrity anomalies, unusual account activity, and scanning indicators) using upstream detections plus normalized rules.
- Centralize alerts so analysts do not have to pivot across disconnected tools.
- Use machine-learning scoring to rank alerts so high-risk incidents are addressed first.
- Provide a dashboard with alerts, risk scores, asset status, incident history, and reporting views.

## 3. Main Building Blocks

| Layer | Main Technology | Role in the Project |
| --- | --- | --- |
| Infrastructure | Docker Compose + NGINX | Hosts and routes the SOC platform services through one entrypoint (`web`, `api`, `worker`, `postgres`, `redis`). |
| Host Monitoring | Wazuh (sync/import pipeline) | Provides endpoint telemetry and host-related detections ingested into normalized records. |
| Network Monitoring | Suricata (sync/import pipeline) | Provides network telemetry and IDS-style detections for suspicious traffic behavior. |
| Attack Simulation | Lab-safe imports and controlled tests | Generates realistic validation events in a controlled environment; Nmap/Hydra remain import-only in AegisCore. |
| Backend | FastAPI + SQLAlchemy 2.0 | Pulls integration data, normalizes records, applies business logic, and serves APIs to the frontend. |
| Database | PostgreSQL | Stores alerts, incidents, assets, users, audit history, integration runs, and model metadata. |
| AI Module | Python + scikit-learn | Produces alert risk scores and explainability factors for prioritization. |
| Frontend | Next.js + TypeScript | Presents dashboards, alert and incident workflows, filters, and analyst-facing views. |

## 4. End-to-End System Flow

1. **Step 1 - Event Generation:** monitored endpoints or network paths produce raw security events.
2. **Step 2 - Collection:** Wazuh and Suricata generate source detections from host logs and network traffic.
3. **Step 3 - Alert Creation:** source detections include metadata such as timestamp, source, severity, and event context.
4. **Step 4 - Backend Ingestion:** integration connectors (`sync` or `import`) parse and normalize source payloads into common fields.
5. **Step 5 - AI Risk Scoring:** the ML layer scores each alert using feature extraction and model inference.
6. **Step 6 - Dashboard Presentation:** frontend views request processed data from API endpoints and render alerts, incidents, assets, and trends.
7. **Step 7 - Analyst Action:** analysts triage highest-risk alerts first, investigate evidence, update statuses, and record response workflow actions.

## 5. How Each Subsystem Works

### 5.1 Wazuh Host Monitoring

- Wazuh-related telemetry is ingested through configured integration pipelines.
- Host-focused detections and integrity signals are normalized into the platform alert model.
- Output contributes directly to alert queues, asset risk context, and incident workflows.

### 5.2 Suricata Network Monitoring

- Suricata detections are ingested through source parsers and normalized fields.
- Network-centric events become first-class alerts in the same triage workflow as host events.
- This gives SOC users visibility into suspicious traffic patterns that host logs may not show alone.

### 5.3 Backend Service Layer

- The backend is the bridge between detection sources and analyst-facing workflows.
- It handles authentication, RBAC, filtering, search, persistence, and API responses.
- It normalizes source-specific payloads so frontend clients consume one stable contract.

### 5.4 AI Alert Prioritization Module

- AI augments, not replaces, detection tools by ranking urgency after detections are created.
- The current scoring pipeline produces a numeric risk score with top contributing factors.
- Retraining runs asynchronously through RQ worker jobs, then applies refreshed scores platform-wide.

### 5.5 Frontend Dashboard

- The dashboard is the user-facing operations layer.
- It summarizes alert volume, critical items, trend signals, and incident state.
- Detail views expose source, event type, normalized evidence, model score, and analyst workflow status.

## 6. Data Flow and AI Logic

The AI component is a scoring layer after detection.

- **Detection answers:** "Did something suspicious happen?"
- **Scoring answers:** "How important is this alert compared with others?"

Practical scoring pipeline:

1. Collect historical and incoming alerts from supported integrations.
2. Build features (for example event category, severity, frequency, asset context, and time patterns).
3. Train/update the model in background jobs.
4. Score incoming alerts and generate explainability factors.
5. Persist outputs so the dashboard can sort/filter by predicted importance.

## 7. Project Lab Environment

This project is demonstrated best as a compact virtual SOC lab.

| VM / Device | Purpose | Typical Contents |
| --- | --- | --- |
| SOC Server VM | Central server | API, web, worker, PostgreSQL, Redis, and reverse proxy stack. |
| Monitored Client VM | Endpoint telemetry source | Host activity that generates security-relevant events. |
| Optional Second Client | Additional endpoint | Multi-host comparison and cross-asset alert behavior. |
| Attacker/Test VM | Controlled event generation | Safe test activity used to trigger detections in the lab. |
| Analyst Browser | Dashboard access | Investigation, triage, status updates, and reporting. |

## 8. Example Incident Walkthrough

1. A controlled suspicious action is generated in the lab.
2. Suricata and/or Wazuh create source detections.
3. Backend ingestion normalizes and stores related evidence.
4. AI scoring increases priority for repeated/high-impact patterns.
5. Dashboard ranks the alert near the top of analyst queues.
6. Analyst opens the incident, reviews context, and updates workflow state.

## 9. Why the Web Application Layer Is Important

Without the web layer, the project remains a set of disconnected tools. The application layer turns those sources into one SOC workflow by:

- Unifying triage, evidence review, and incident lifecycle tracking.
- Making AI prioritization actionable through sorting, filtering, and queueing.
- Enabling clear presentation and reporting for operational and academic use.

## 10. Recommended Dashboard Modules

- Overview Page - total alerts, high-risk alerts, open incidents, and trend summaries.
- Alerts Page - searchable alert table with severity, status, source, timestamp, and model score.
- Incident Detail Page - linked evidence, event timeline, analyst notes, and workflow updates.
- Assets/Endpoints Page - monitored asset list, current risk, and recent activity.
- Reports Page - exportable summaries for reviews and demonstrations.
- Model Insights Page - concise explanation of scoring behavior and key contributing factors.

## 11. Limitations and What to Keep Realistic

- Student projects should prioritize correctness and clarity over enterprise-scale volume.
- AI should support prioritization, not claim complete or perfect detection.
- Demonstration activities must be controlled and lab-safe.
- Strong normalization, labeling quality, and feature choices matter more than model complexity.

## 12. Conclusion

The AI-Integrated SOC Web Application connects monitoring tools, backend processing, persistent alert storage, ML prioritization, and analyst-facing dashboards into one continuous pipeline. Its strength is showing the full security event lifecycle: generation, collection, detection, enrichment, prioritization, presentation, and analyst response.

This produces a coherent implementation that combines cybersecurity operations, software engineering, data handling, and practical AI in one system.

## Reference Note

The original project artifact focused on planning and proposal-stage milestones. This working document extends that context into an operational description of the implemented system behavior and data flow.
