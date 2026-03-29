# AegisCore Integration Layer

## Scope

AegisCore supports four defensive integration sources:

- `wazuh`: defensive endpoint or SIEM telemetry, synchronized from a configured HTTP endpoint or imported from exported files
- `suricata`: defensive network telemetry, synchronized from a configured HTTP endpoint or imported from exported files
- `nmap`: import-only lab results, never executed from AegisCore
- `hydra`: import-only lab results, never executed from AegisCore

## API Contract

### Read integrations

- `GET /api/v1/integrations`
- `GET /api/v1/integrations/{slug}`
- `GET /api/v1/integrations/{slug}/history`

Integration responses include:

- connector identity and health
- connection status and status detail
- sanitized configuration metadata
- supported formats
- sync vs import capabilities
- run history with mode, counts, errors, and lab-import flag

### Update configuration

- `PATCH /api/v1/integrations/{slug}`

Supported request fields for sync-capable sources:

- `enabled`
- `endpoint_url`
- `auth_type`
- `username`
- `password`
- `api_token`
- `verify_tls`
- `timeout_seconds`
- `lookback_minutes`
- `request_headers`
- `query_params`

`nmap` and `hydra` reject remote-sync configuration.

### Run ingestion

- `POST /api/v1/integrations/{slug}/sync`
- `POST /api/v1/integrations/{slug}/import`

`sync` is supported only for `wazuh` and `suricata`.

`import` is supported for all four sources.

## Normalized Fields

All parsed records are normalized into a shared ingestion shape before persistence:

- `external_id`
- `title`
- `description`
- `source`
- `source_type`
- `event_type`
- `severity`
- `occurred_at`
- `detected_at`
- `asset_hostname`
- `asset_ip`
- `operating_system`
- `business_unit`
- `tags`
- `message`
- `level`
- `category`
- `fingerprint`
- `raw_payload`
- `parsed_payload`
- `incident_candidate`
- `imported_lab_data`

Persisted outputs then map into the existing internal models:

- `LogEntry`
- `Alert`
- `Asset`
- `IntegrationRun`

## Supported Formats

- `wazuh`: JSON, NDJSON
- `suricata`: JSON, NDJSON
- `nmap`: JSON, XML
- `hydra`: JSON, NDJSON, TXT

## Safety Rules

- No API endpoint launches `nmap`
- No API endpoint launches `hydra`
- `nmap` and `hydra` are limited to uploaded lab-result parsing only
- lab imports are explicitly tagged and marked in normalized payloads as `lab_imported`
