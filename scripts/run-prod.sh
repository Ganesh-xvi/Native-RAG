#!/usr/bin/env bash
# Production server (Linux/Docker — uses gunicorn)
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export API_HOST="${API_HOST:-0.0.0.0}"
export API_PORT="${API_PORT:-8000}"
export GUNICORN_BIND="${GUNICORN_BIND:-0.0.0.0:${API_PORT}}"

echo "Starting gunicorn on ${GUNICORN_BIND} (timeout=${GUNICORN_TIMEOUT:-120}s) ..."
exec gunicorn src.api.main:app -c gunicorn.conf.py
