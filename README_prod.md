Guide de mise en production (VPS OVH)
=====================================

Objectif
--------
Déployer backend + frontend sur `covamessagerie.be` avec Docker, Nginx et TLS.

Pré-requis VPS
--------------
- DNS : `covamessagerie.be` pointe vers l’IP du VPS.
- OS avec Docker et docker compose plugin installés.
- Nginx et certbot (ou équivalent) pour le reverse-proxy et le HTTPS.

Étapes
------
1) Récupérer le code sur le VPS :
```bash
git clone <repo> messagerie-securisee
cd messagerie-securisee
```

2) Créer `.env.prod` (copie de `.env.example`) et définir au minimum :
```
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/securechat
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=securechat
JWT_SECRET_KEY=une_chaine_aleatoire_de_32_car_minimum
PUBLIC_BASE_URL=https://covamessagerie.be
FRONTEND_ORIGIN=https://covamessagerie.be
REDIS_URL=redis://redis:6379/0
# Optionnel stockage S3 : STORAGE_ENDPOINT, STORAGE_ACCESS_KEY, STORAGE_SECRET_KEY, STORAGE_BUCKET…
```

3) Lancer la stack :
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```
- Backend écoute en local sur 127.0.0.1:8000, frontend sur 127.0.0.1:8080.

4) Configurer Nginx (exemple) :
```
server {
  listen 80;
  server_name covamessagerie.be;

  location / {
    proxy_pass http://127.0.0.1:8080;
  }

  location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }

  location /api/ws {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
  }
}
```
- Activer le site, recharger Nginx, puis générer le certificat : `certbot --nginx -d covamessagerie.be`.

5) Créer les comptes de démo (depuis `backend/` sur le VPS) :
```bash
python -m scripts.bootstrap_tenant \
  --email admin@example.com \
  --password "Temp#2024" \
  --display-name "Admin Demo" \
  --organization "DemoOrg" \
  --slug demo \
  --role owner

python -m scripts.bootstrap_tenant \
  --email user@example.com \
  --password "Temp#2024" \
  --display-name "User Demo" \
  --organization "DemoOrg" \
  --slug demo \
  --role member
```

6) Vérifier :
- Front : https://covamessagerie.be
- API santé : `curl https://covamessagerie.be/api/healthz`
- Connexion admin : admin@example.com / Temp#2024
- Connexion membre : user@example.com / Temp#2024

Notes
-----
- Le déploiement est single-tenant : une instance = une organisation.
- Les rôles owner/admin/member sont gérés côté API (`/api/organizations/current/...`).
- Pour répliquer sur un autre domaine/organisation : nouveau `.env.prod`, nouveau DNS et relancer le compose.
# Messagerie sécu (prod)
<!--
############################################################
# Fichier : README_prod.md (racine)
# Auteur  : Valentin Masurelle
# Date    : 2025-05-04
#
# Description:
# - Instructions pour le déploiement/ops en production.
############################################################
-->
