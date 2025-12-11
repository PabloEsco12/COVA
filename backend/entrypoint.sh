#!/bin/sh
set -e

echo "Initialisation du backend FastAPI..."

# 0) Attendre que Postgres soit prêt
/wait-for-it.sh db:5432 --timeout=60 --strict -- echo "Postgres est prêt !"

# 1) Appliquer les migrations Alembic
if [ -d "/app/migrations" ]; then
  echo "⬆ Upgrade BDD (Alembic)…"
  alembic -c /app/alembic.ini upgrade head || echo "Aucun upgrade appliqué"
else
  echo "Pas de dossier migrations/ → skip alembic upgrade"
fi

# 2) Lancer Gunicorn + UvicornWorker (pour FastAPI)
echo "Lancement API FastAPI avec Gunicorn/Uvicorn…"
exec gunicorn "app.main:app" \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8000 \
    --workers ${WORKERS:-4} \
    --threads ${THREADS:-2} \
    --timeout ${TIMEOUT:-120} \
    --forwarded-allow-ips="*" \
    --proxy-headers
