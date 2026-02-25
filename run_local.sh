#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
ENV_FILE="${ENV_FILE:-.env}"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

read_env_value() {
  local key="$1"
  local file="$2"

  local line
  line="$(grep -E "^[[:space:]]*${key}=" "$file" | tail -n 1 || true)"
  if [ -z "$line" ]; then
    echo ""
    return 0
  fi

  local value="${line#*=}"
  value="${value#"${value%%[![:space:]]*}"}"  # ltrim
  value="${value%"${value##*[![:space:]]}"}"  # rtrim

  if [[ "$value" == \"*\" ]]; then
    value="${value:1:-1}"
  elif [[ "$value" == \'*\' ]]; then
    value="${value:1:-1}"
  fi

  echo "$value"
}

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: $ENV_FILE not found. Create it (copy .env.example) and fill secrets." >&2
  exit 1
fi

# Resolve paths used by the script (prefer exported env, else .env, else defaults)
DB_PATH="${SIEM_DB_PATH:-$(read_env_value SIEM_DB_PATH "$ENV_FILE")}"
LOG_DIR="${SIEM_LOG_DIR:-$(read_env_value SIEM_LOG_DIR "$ENV_FILE")}"

DB_PATH="${DB_PATH:-./data/siem.sqlite3}"
LOG_DIR="${LOG_DIR:-./sample_logs}"

# Optional: sanity check that required secrets are present in .env / environment
ADMIN_HASH="${SIEM_ADMIN_PASSWORD_HASH:-$(read_env_value SIEM_ADMIN_PASSWORD_HASH "$ENV_FILE")}"
JWT_SECRET="${SIEM_JWT_SECRET:-$(read_env_value SIEM_JWT_SECRET "$ENV_FILE")}"

if [ -z "$ADMIN_HASH" ] || [ -z "$JWT_SECRET" ]; then
  echo "ERROR: Missing SIEM_ADMIN_PASSWORD_HASH or SIEM_JWT_SECRET in $ENV_FILE" >&2
  exit 1
fi

mkdir -p "$(dirname "$DB_PATH")" "$LOG_DIR"

# create a demo log if none exists
if ! ls "$LOG_DIR"/*.jsonl >/dev/null 2>&1; then
  cat > "$LOG_DIR/demo.jsonl" <<'EOF'
{"ts":"2026-02-19T12:00:00Z","app":"demo","event_type":"test","level":"INFO","message":"hello"}
EOF
fi

echo "=== Smoke test: start server (no-reload), curl /health, stop ==="
python -m uvicorn main:app --host "$HOST" --port "$PORT" >/tmp/mini-siem-uvicorn.log 2>&1 &
PID=$!

cleanup() {
  kill "$PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for i in $(seq 1 50); do
  if curl -fsS "http://$HOST:$PORT/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

echo ">>> GET /health"
curl -fsS "http://$HOST:$PORT/health" | python -m json.tool || true

kill "$PID" >/dev/null 2>&1 || true
wait "$PID" >/dev/null 2>&1 || true
trap - EXIT

echo
echo "=== Dev server: start with --reload (CTRL+C to stop) ==="
# exec python -m uvicorn main:app --reload --host "$HOST" --port "$PORT"
exec python -m uvicorn main:app --host "$HOST" --port "$PORT"

