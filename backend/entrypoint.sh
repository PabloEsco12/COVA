#!/bin/sh
set -e
export FLASK_APP=${FLASK_APP:-app}

# 0) Attendre que Postgres soit prêt !
/wait-for-it.sh db:5432 --timeout=60 --strict -- echo "✅ Postgres est prêt !"

# 1) Crée migrations/ si absent
if [ ! -d "/app/migrations" ]; then
  echo "📁  Pas de dossier migrations/ → initialisation"
  python -m flask db init
fi

# 2) Génère une révision auto si des changements ORM sont détectés
echo "🔍  Vérification des changements de schéma"
python -m flask db migrate -m "auto" || true   # 'true' si aucun changement

# 3) Upgrade
echo "⬆️   Upgrade BDD (Alembic)…"
python -m flask db upgrade

# 4) Démarrage de l’API
echo "🚀  Lancement API Flask…"
exec python -m app
