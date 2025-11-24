<!--
############################################################
# Fichier : README.md (racine)
# Auteur  : Valentin Masurelle
# Date    : 2025-05-04
#
# Description:
# - Vue d'ensemble du projet Messagerie securisee COVA.
# - Composants principaux : backend FastAPI, frontend Vue 3.
############################################################
-->

# Messagerie securisee (COVA)

Plateforme de messagerie sécurisée avec backend FastAPI et frontend Vue 3 (conversations, appels, pièces jointes, notifications temps réel).

## Aperçu du dépôt
- `backend/` : API FastAPI, services métier, migrations Alembic, worker de notifications.
- `frontend/secure_messagerie/` : application Vue 3 (Vite) pour le tableau de bord.
- `docs/` : documentation produit/technique.
- `scripts/` : utilitaires (ex. smoke test Playwright).
- `STRUCTURE.md` : rappel synthétique de l’arborescence.

## Prérequis
- Docker / Docker Compose pour la pile complète, ou Python 3.11+ et Node.js 18+ pour un lancement manuel.
- Services attendus : Postgres, Redis, stockage S3-compatible (MinIO), ClamAV pour l’antivirus.

## Variables d’environnement
1. Copiez le gabarit : `cp .env.example .env.docker` (Compose), `cp .env.example .env.dev` (dev manuel backend), `cp .env.example frontend/secure_messagerie/.env.development` (front).
2. Remplacez les secrets et URLs.

Principales clés :
- Backend : `DATABASE_URL`, `JWT_SECRET_KEY`, `BACKEND_CORS_ORIGINS`, `REDIS_URL`, stockage (`STORAGE_*`), antivirus (`ANTIVIRUS_*`), SMTP (`SMTP_*`), `PUBLIC_BASE_URL`, `FRONTEND_ORIGIN`.
- Frontend : `VITE_API_URL`, `VITE_WS_BASE` (optionnel pour forcer l’URL WS), `VITE_TENOR_API_KEY` (optionnel GIF).
- Compose : `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`.

## Démarrage rapide (Docker Compose local)
```bash
cp .env.example .env.docker
docker compose -f docker-compose.local.yml --env-file .env.docker up -d
```
- API backend : http://localhost:18000/api
- Frontend dev (conteneur) : http://localhost:5176

## Backend en local (sans Docker)
```bash
cd backend
python -m venv .venv && .\.venv\Scripts\activate  # ou source .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend en local (sans Docker)
```bash
cd frontend/secure_messagerie
npm install
cp ../.env.example .env.development   # ou définir VITE_API_URL manuellement
npm run dev -- --host --port 5176
```

## Bootstrap d’un tenant
Création organisation + utilisateur propriétaire via le script CLI :
```bash
cd backend
python -m scripts.bootstrap_tenant \
  --email admin@example.com \
  --password "Temp#2024" \
  --display-name "Admin Example" \
  --organization "Example Corp" \
  --slug example \
  --role owner
```

## Tests et vérifications
- Backend : `pytest` (préparer une base de test et lever le skip dans `backend/tests/test_auth_flow.py`).
- Smoke test front+API : `node scripts/debug-send.js` (Playwright ouvre l’app, se connecte et envoie un message).

