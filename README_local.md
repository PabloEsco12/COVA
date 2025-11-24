Guide rapide (développement local)
===================================

Prérequis
---------
- Docker et docker compose **ou** Python 3.11 + Node.js 18.
- Copier les variables d’environnement : `cp .env.example .env.dev` (backend) et `cp .env.example frontend/secure_messagerie/.env.development` (front).

Démarrer avec Docker
--------------------
```bash
cp .env.example .env.docker
docker compose -f docker-compose.local.yml --env-file .env.docker up -d
# API: http://localhost:18000/api
# Front: http://localhost:5176
```

Backend seul (sans Docker)
--------------------------
```bash
cd backend
python -m venv .venv && .\.venv\Scripts\activate   # ou source .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# API: http://localhost:8000/api
```

Frontend seul (sans Docker)
---------------------------
```bash
cd frontend/secure_messagerie
npm install
cp ../.env.example .env.development   # sinon définir VITE_API_URL manuellement
npm run dev -- --host --port 5176
# Front: http://localhost:5176
```

Créer des comptes de test
-------------------------
- Inscription via le front (flux normal), ou
- Script CLI depuis `backend/` :
```bash
python -m scripts.bootstrap_tenant \
  --email admin@example.com \
  --password "Temp#2024" \
  --display-name "Admin Demo" \
  --organization "DemoOrg" \
  --slug demo \
  --role owner
```
Ajouter un membre :
```bash
python -m scripts.bootstrap_tenant \
  --email user@example.com \
  --password "Temp#2024" \
  --display-name "User Demo" \
  --organization "DemoOrg" \
  --slug demo \
  --role member
```
Ou plus simple (automatisé) depuis la racine du repo :
```bash
./scripts/create_demo.sh
# Variables optionnelles : ADMIN_EMAIL, ADMIN_PASSWORD, MEMBER_EMAIL, MEMBER_PASSWORD, ORG_NAME, ORG_SLUG
```
# Messagerie sécu (local)
<!--
############################################################
# Fichier : README_local.md (racine)
# Auteur  : Valentin Masurelle
# Date    : 2025-05-04
#
# Description:
# - Instructions de lancement en environnement local.
############################################################
-->
