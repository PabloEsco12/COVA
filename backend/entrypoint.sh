#!/bin/sh
set -e

export FLASK_APP=${FLASK_APP:-app}

# 0) Attendre que Postgres soit prêt
/wait-for-it.sh db:5432 --timeout=60 --strict -- echo "✅ Postgres est prêt !"

# 1) Appliquer les migrations (si elles existent déjà dans le repo)
if [ -d "/app/migrations" ]; then
  echo "⬆️  Upgrade BDD (Alembic)…"
  flask db upgrade || echo "⚠️ Aucun upgrade appliqué"
else
  echo "⚠️ Pas de dossier migrations/ → skip flask db upgrade"
fi

# 2) Lancer Gunicorn (au lieu du serveur Flask intégré)
echo "🚀  Lancement API Flask avec Gunicorn…"
exec gunicorn "app:create_app()" \
    -b 0.0.0.0:5000 \
    --workers ${WORKERS:-4} \
    --threads ${THREADS:-2} \
    --timeout ${TIMEOUT:-120}
