# Mini-SIEM (JSONL -> SQLite) — Proposed Backlog and Scope

This document proposes the scope and implementation backlog for a small SIEM-like system that:
- Reads structured JSON Lines (JSONL) logs from a host directory (e.g. `/srv/app_logs/**`).
- Normalizes them into a unified event schema.
- Stores events in SQLite for fast filtering, pagination, and future detections.
- Exposes a FastAPI backend secured with an admin password login issuing a JWT.
- Is deployed behind a reverse proxy (HTTPS) and uses CORS restricted to the Netlify frontend origin(s).

## Goals

### MVP Goals (v0.1)
- Ingest JSONL logs continuously (tail-like behavior) without duplicating events on restart.
- Normalize fields into a consistent schema and store them in SQLite.
- Provide an API to query events with filters (time range, app, event_type, level, user_id, src_ip, request_id, HTTP status, free-text).
- Provide an API for metadata lists (apps and event types).
- Secure the API with admin login (password) + JWT and strict CORS.

### Non-goals for MVP
- Multi-tenant access control / RBAC beyond “admin”.
- Advanced detection correlation or ML.
- High-volume ingestion optimizations (Kafka, Elasticsearch, etc.).
- Distributed agents on hosts (we read from the host-mounted log directory).

## Architecture (MVP)

### Components
1. **FastAPI service**
   - Serves query endpoints and auth endpoints.
   - Runs an ingestion loop in the application lifespan (or a background worker started on boot).

2. **SQLite database**
   - Stores normalized events and ingestion offsets.
   - Acts as an index for fast filtering and pagination.
   - Persists via a Docker volume or bind mount (e.g. `/srv/siem/data:/data`).

3. **Log directory mount**
   - Host logs directory mounted read-only into the SIEM container, e.g. `/srv/app_logs:/logs:ro`.
   - SIEM discovers and tails `*.jsonl` files under `/logs/**`.

4. **Reverse proxy**
   - Exposes SIEM API over HTTPS.
   - Optionally serves under a prefix, e.g. `/siem`, with prefix stripping.

### Data flow
JSONL files -> ingestor -> normalization/validation -> SQLite -> query API -> frontend

## Security Model

- **Do not rely on CORS for security.** CORS is browser-side only.
- All data endpoints require a valid **JWT** issued by `POST /auth/login`.
- CORS is restricted to the Netlify frontend origin(s).
- Log directory mount is **read-only**.
- Admin password is stored as a hash in environment variables (`SIEM_ADMIN_PASSWORD_HASH`).
- Token is short-lived or moderate-lived (MVP recommendation: 7 days), with manual logout by clearing storage.

## Unified Event Schema (Normalized)

The SIEM normalizes incoming JSONL entries into fields used by the UI and filters, while preserving the original JSON.

### Core fields
- `id` (integer primary key or UUID)
- `ts` (timestamp from the log entry, UTC)
- `received_at` (timestamp when SIEM ingested it)
- `app` (application name)
- `host` (host/container id)
- `level` (INFO/WARNING/ERROR/...)
- `event_type` (machine-readable type)
- `message` (human-readable message)

### Correlation and actor
- `request_id`
- `user_id`
- `src_ip`
- `user_agent`

### HTTP fields (optional)
- `http_method`
- `http_path`
- `http_status`
- `latency_ms`

### Error fields (optional)
- `error_type`

### Payload
- `data_json` (JSON string; event-specific payload)
- `raw_json` (JSON string; original full event)

### Source tracking
- `source_file`
- `source_offset`

## SQLite Schema (MVP)

### Table: `events`
Recommended columns:
- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `ts TEXT NOT NULL` (ISO 8601 string; store UTC)
- `received_at TEXT NOT NULL`
- `app TEXT`
- `host TEXT`
- `level TEXT`
- `event_type TEXT`
- `message TEXT`
- `request_id TEXT`
- `user_id TEXT`
- `src_ip TEXT`
- `user_agent TEXT`
- `http_method TEXT`
- `http_path TEXT`
- `http_status INTEGER`
- `latency_ms REAL`
- `error_type TEXT`
- `data_json TEXT`
- `raw_json TEXT`
- `source_file TEXT`
- `source_offset INTEGER`

Suggested indices:
- `INDEX events_ts_desc ON events(ts DESC)`
- `INDEX events_app_ts ON events(app, ts DESC)`
- `INDEX events_event_type_ts ON events(event_type, ts DESC)`
- `INDEX events_src_ip_ts ON events(src_ip, ts DESC)`
- `INDEX events_user_id_ts ON events(user_id, ts DESC)`
- `INDEX events_request_id ON events(request_id)`

### Table: `file_offsets`
Tracks ingestion state:
- `path TEXT PRIMARY KEY`
- `inode INTEGER`
- `offset INTEGER`
- `updated_at TEXT`

## API (MVP)

### Auth
- `POST /auth/login`
  - Body: `{ "password": "..." }`
  - Response: `{ "access_token": "...", "token_type": "bearer", "expires_in": 604800 }`

- (Optional) `POST /auth/logout`
  - Can be a no-op; frontend can simply drop the token.

### Metadata
- `GET /apps`
  - Returns distinct `app` values.

- `GET /event-types?app=MoneyControl`
  - Returns distinct `event_type` values; optionally filtered by app.

### Query
- `GET /events`
  Filters:
  - `from` (ISO datetime)
  - `to` (ISO datetime)
  - `app` (repeatable or comma-separated)
  - `event_type` (repeatable or comma-separated)
  - `level` (repeatable or comma-separated)
  - `user_id`
  - `src_ip`
  - `request_id`
  - `http_status`
  - `q` (substring search in `message` and optionally `http_path`)
  - `limit` (default 200)
  - Cursor pagination: `before_ts`, `before_id` (or a single opaque cursor)

- `GET /events/{id}`
  - Returns normalized fields plus `raw_json` and `data_json`.

### Health
- `GET /health`
- `GET /ready` (optional; checks DB and ingestion loop)

## Deployment (MVP)

### Docker compose layout
- `siem-api` container
  - Mount: `/srv/app_logs:/logs:ro`
  - Persist DB: `siem_data:/data` or bind mount `/srv/siem/data:/data`
  - Env: `SIEM_DB_PATH=/data/siem.sqlite3`, `SIEM_ADMIN_PASSWORD_HASH=...`, `SIEM_JWT_SECRET=...`, `SIEM_CORS_ORIGINS=...`

### Reverse proxy
- Expose the SIEM API over HTTPS.
- If using a prefix (e.g. `/siem/`), proxy must strip prefix so FastAPI receives paths without the prefix.
- Set `SIEM_ROOT_PATH=/siem` if you want generated OpenAPI URLs to include the prefix.

## Backlog

This backlog is organized as steps that can be executed sequentially.

### S0 — Project setup and Docker
**S0.1** Create SIEM repo and basic FastAPI app  
**S0.2** Add Dockerfile and docker-compose (siem-api)  
**S0.3** Add volume/bind mount for SQLite persistence (`/data`)  
**S0.4** Mount logs directory read-only (`/logs:ro`)  
**S0.5** `GET /health` endpoint  
**Definition of Done**
- Container starts successfully.
- `/health` returns 200.
- Container can list files under `/logs`.

### S1 — Admin auth (password) + JWT
**S1.1** Add `POST /auth/login`  
**S1.2** Store `SIEM_ADMIN_PASSWORD_HASH` in env (bcrypt recommended)  
**S1.3** JWT issuing with `SIEM_JWT_SECRET`  
**S1.4** JWT verification dependency (`require_admin`) for protected endpoints  
**S1.5** Strict CORS (`SIEM_CORS_ORIGINS`)  
**S1.6** Optional in-app rate limit for login (basic)  
**Definition of Done**
- Without JWT, `/events` returns 401.
- With JWT, `/events` returns data.
- Only allowed origins pass CORS.

### S2 — SQLite schema and persistence
**S2.1** Create tables: `events`, `file_offsets`  
**S2.2** Add indices for time/app/event_type and correlation fields  
**S2.3** Add basic DB access layer (insert batch, query)  
**Definition of Done**
- Database file persists across container restarts.
- Inserting and querying events works.

### S3 — Ingestor: discovery, tail, offsets
**S3.1** Discover files under `/logs/**` matching `*.jsonl`  
**S3.2** Load current offsets from `file_offsets`  
**S3.3** Read new lines since last offset (poll every 2s)  
**S3.4** Handle truncation and rotation:
- if file size < offset -> reset offset to 0
- if inode changed -> reset offset to 0
**S3.5** Dead-letter or counters for invalid JSON lines  
**S3.6** Batch insert normalized events into SQLite (commit every N events)  
**Definition of Done**
- Appending lines to a JSONL file results in new events in `/events`.
- Restarting SIEM does not duplicate already ingested events.

### S4 — Normalization and validation
**S4.1** Define Pydantic model for incoming log entry (tolerant)  
**S4.2** Normalize into unified schema (ts/app/event_type/level/message)  
**S4.3** Extract optional fields (request_id/user_id/src_ip/http fields)  
**S4.4** Sanitize long strings and large payloads (max length caps)  
**Definition of Done**
- Events from MoneyControl appear correctly with expected fields.
- Bad lines do not crash ingestion.

### S5 — Query API
**S5.1** Implement `GET /apps`  
**S5.2** Implement `GET /event-types`  
**S5.3** Implement `GET /events` with filters + pagination  
**S5.4** Implement `GET /events/{id}`  
**Definition of Done**
- UI can build a full “log explorer” using these endpoints.

### S6 — Operational features
**S6.1** Retention job (delete DB events older than N days, e.g. 30)  
**S6.2** `/ready` endpoint checks DB and ingestion loop status  
**S6.3** Basic ingestion metrics (events ingested, parse errors)  
**Definition of Done**
- DB does not grow forever.
- Health/ready endpoints expose status.

### S7 — Alerts and detections (post-MVP)
**S7.1** Rules engine (threshold in time window)  
**S7.2** Table `alerts` + `GET /alerts` endpoint  
**S7.3** Initial rules for MoneyControl:
- repeated `auth_oauth_google_login_failed` by src_ip
- spikes in `permission_denied`
- every `audit_transactions_exported` as a high-visibility alert
- `unhandled_exception` alerts
**S7.4** Optional SSE for live alerts  
**Definition of Done**
- Alerts are generated from ingested events and visible via API.

## MVP Defaults (suggested)
- Ingest polling interval: 2 seconds
- DB retention: 30 days
- Default query limit: 200
- JWT TTL: 7 days
- Log directory mount: read-only

## Open Questions for Review
1. Reverse proxy routing:
   - Prefer `/siem` prefix, or a separate subdomain?
2. Retention period:
   - 14 / 30 / 90 days?
3. Live tail:
   - Needed in MVP, or later?
4. Password storage:
   - Hash only (recommended), or plaintext in env (not recommended)?
