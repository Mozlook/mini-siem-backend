#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

export SIEM_DB_PATH="${SIEM_DB_PATH:-./data/siem.sqlite3}"
export SIEM_LOG_DIR="${SIEM_LOG_DIR:-./sample_logs}"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

mkdir -p "$(dirname "$SIEM_DB_PATH")" "$SIEM_LOG_DIR"

if ! ls "$SIEM_LOG_DIR"/*.jsonl >/dev/null 2>&1; then
  cat > "$SIEM_LOG_DIR/demo.jsonl" <<'EOF'
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
exec python -m uvicorn main:app --reload --host "$HOST" --port "$PORT"

