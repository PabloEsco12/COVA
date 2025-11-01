#!/bin/sh
set -euo pipefail

APP_DIR=${APP_DIR:-/app}
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
ALEMBIC_CONFIG=${ALEMBIC_CONFIG:-${APP_DIR}/alembic.ini}
PORT=${PORT:-8000}

cd "${APP_DIR}"

if [ -x "${APP_DIR}/wait-for-it.sh" ]; then
  "${APP_DIR}/wait-for-it.sh" "${DB_HOST}:${DB_PORT}" --timeout=60 --strict -- echo "[ok] Postgres is ready"
else
  echo "[warn] wait-for-it.sh not found, continuing without database health check."
fi

if [ -f "${ALEMBIC_CONFIG}" ]; then
  echo "[migrate] Running Alembic upgrade"
  if ! alembic -c "${ALEMBIC_CONFIG}" upgrade head; then
    echo "[warn] Alembic upgrade failed. Resetting revision pointer to base and retrying..."
    alembic -c "${ALEMBIC_CONFIG}" stamp base
    alembic -c "${ALEMBIC_CONFIG}" upgrade head
  fi
else
  echo "[warn] Alembic config ${ALEMBIC_CONFIG} not found, skipping migrations."
fi

echo "[start] Starting FastAPI with Uvicorn on port ${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
