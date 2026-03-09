# Mini-SIEM Backend

A FastAPI backend that continuously ingests JSONL logs from a host directory, normalizes them into a unified event schema, stores them in SQLite, and exposes a JWT-protected API for querying events and operational status.

## High-level architecture

- FastAPI API service
- Background ingestion loop (thread started in application lifespan)
- SQLite database for normalized events and ingestion offsets
- Host log directory mounted read-only into the container

Data flow:

JSONL files -> ingestor -> validation/normalization -> SQLite -> API -> frontend

## Requirements

- Docker
- docker-compose (v1) or Docker Compose v2
- Nginx (for HTTPS + reverse proxy in production)

## Configuration

The backend uses environment variables (typically via a `.env` file).

### Required secrets

You must set these in `.env`:

- `SIEM_ADMIN_PASSWORD_HASH`
  - bcrypt hash of the admin password
  - bcrypt uses only the first 72 bytes of the password

- `SIEM_JWT_SECRET`
  - long random secret used to sign/verify JWT

- `SIEM_CORS_ORIGINS`
  - JSON array of allowed origins
  - example: `["http://localhost:5173","https://siem.example.com"]`

### Common settings

Auth / JWT:

- `SIEM_JWT_TTL_SECONDS` (default 604800 = 7 days)
- `SIEM_JWT_ALG` (default HS256)

Paths:

- `SIEM_DB_PATH` (default `./data/siem.sqlite3`; in Docker use `/data/siem.sqlite3`)
- `SIEM_LOG_DIR` (default `./sample_logs`; in Docker use `/logs`)

Ingestion:

- `SIEM_INGEST_ENABLED` (default true)
- `SIEM_INGEST_POLL_SECONDS` (default 2)
- `SIEM_INGEST_BATCH_SIZE` (default 200)
- `SIEM_INGEST_MAX_BATCHES_PER_FILE` (safety limit per file per ingest cycle)

Retention:

- `SIEM_RETENTION_ENABLED`
- `SIEM_RETENTION_DAYS`
- `SIEM_RETENTION_RUN_EVERY_SECONDS`

Payload caps (protect DB and UI against huge strings):

- `SIEM_MAX_MESSAGE_LEN`
- `SIEM_MAX_USER_AGENT_LEN`
- `SIEM_MAX_HTTP_PATH_LEN`
- `SIEM_MAX_DATA_JSON_LEN`
- `SIEM_MAX_RAW_JSON_LEN`

Reverse proxy prefix support (recommended when serving under `/siem`):

- `SIEM_ROOT_PATH=/siem`

## API overview

Auth:

- `POST /auth/login` with body `{ "password": "..." }`
  - returns `{ access_token, token_type, expires_in }`

Metadata:

- `GET /metadata/apps`
- `GET /metadata/event-types?app=...`

Query:

- `GET /events` (filters + cursor pagination)
- `GET /events/{id}` (full detail including raw_json and data_json)

Operational:

- `GET /health`
- `GET /ready`
- `GET /metrics`

### Cursor pagination behavior

- Sort order: `ts DESC, id DESC`
- Next page cursor is taken from the last returned event:
  - `before_ts=<last.ts>&before_id=<last.id>`
- `before_ts` and `before_id` must be provided together.

## Local development (Docker)

Create `.env` in repo root.

Example:

```env
SIEM_ADMIN_PASSWORD_HASH=...
SIEM_JWT_SECRET=...
SIEM_CORS_ORIGINS=["http://localhost:5173"]

SIEM_DB_PATH=/data/siem.sqlite3
SIEM_LOG_DIR=/logs
SIEM_ROOT_PATH=/siem
```

Start:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

Check:

```bash
curl -i http://127.0.0.1:8011/health
```

## Production deployment (VPS)

This section matches a typical VPS layout used in this project:

- Repo path: `/root/mini-siem-backend`
- Host logs: `/srv/app_logs/`
- SQLite persistence: `/srv/siem/data/`
- Backend bound to localhost: `127.0.0.1:8011 -> container:8000`
- Nginx exposes HTTPS and proxies under `/siem`

### docker-compose.prod.yml

Example:

```yaml
services:
  siem-api:
    build: .
    container_name: mini-siem-backend
    restart: unless-stopped

    ports:
      - "127.0.0.1:8011:8000"

    env_file:
      - .env

    environment:
      SIEM_DB_PATH: /data/siem.sqlite3
      SIEM_LOG_DIR: /logs
      SIEM_ROOT_PATH: /siem

    volumes:
      - /srv/siem/data:/data
      - /srv/app_logs:/logs:ro
```

Notes:

- The database is preserved because `/srv/siem/data` is a bind mount.
- Avoid `docker-compose down -v` unless you intentionally want to destroy volumes.

### Nginx reverse proxy under /siem

Inside your `server { ... }` block for the API host:

```nginx
location = /siem {
    return 301 /siem/;
}

location ^~ /siem/ {
    proxy_pass http://127.0.0.1:8011/;  # trailing slash strips /siem/
    include proxy_params;
    proxy_set_header X-Forwarded-Prefix /siem;
}
```

### Deploy script (pull -> rebuild -> restart, DB preserved)

Store this in the repo as `scripts/deploy.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH="${BRANCH:-main}"
PROJECT="${PROJECT:-mini-siem}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

cd "$APP_DIR"

echo "==> Updating repo ($BRANCH)"
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

echo "==> Building image"
docker-compose -p "$PROJECT" -f "$COMPOSE_FILE" build

echo "==> Restarting container (DB preserved via /srv/siem/data:/data)"
docker-compose -p "$PROJECT" -f "$COMPOSE_FILE" down --remove-orphans || docker-compose -p "$PROJECT" -f "$COMPOSE_FILE" down
# IMPORTANT: no 'down -v'
docker-compose -p "$PROJECT" -f "$COMPOSE_FILE" up -d

echo "==> Status"
docker-compose -p "$PROJECT" -f "$COMPOSE_FILE" ps
```

Make it executable:

```bash
chmod +x scripts/deploy.sh
```

Run:

```bash
cd /root/mini-siem-backend
./scripts/deploy.sh
```

## Operational notes

- Ingestor runs in-process (thread). Avoid multiple Uvicorn worker processes unless you implement coordination; otherwise multiple ingest loops can race.
- When using `uvicorn --reload`, consider setting `SIEM_INGEST_ENABLED=false` to avoid duplicate ingestor threads during reload.
