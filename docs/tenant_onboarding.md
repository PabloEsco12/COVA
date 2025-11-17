# Provisionner une nouvelle organisation COVA

Chaque entreprise cliente dispose de sa propre base de données PostgreSQL et d’une instance applicative configurée avec ses secrets. Ce document décrit les étapes recommandées pour créer un nouvel environnement de façon reproductible.

## 1. Préparer l’infrastructure

1. Créez une nouvelle base `postgres` (ex : `cova_acme`) sur l’instance choisie ou via `docker-compose.local.yml`.
2. Générez un `.env` dédié (copie de `.env.dev`) en pointant `DATABASE_URL` et `REDIS_URL` vers l’infrastructure du client.
3. Démarrez le backend et le frontend avec ces variables (`docker compose --env-file .env.acme up -d`).
4. Exécutez les migrations sur la base du client (ex : `alembic upgrade head` dans `backend/`).

> Chaque organisation possède son propre fichier `.env` et, par conséquent, sa propre pile de services ; ainsi la ségrégation des données reste totale.

## 2. Créer l’administrateur initial

Le script `backend/scripts/bootstrap_tenant.py` automatise la création d’une organisation, d’un utilisateur confirmé et de l’appartenance correspondante :

```bash
cd backend
python -m scripts.bootstrap_tenant \
  --email admin@acme.com \
  --password "Temp#2024" \
  --display-name "Admin Acme" \
  --organization "Acme Industries" \
  --slug acme \
  --role owner
```

Le script est idempotent : s’il trouve l’utilisateur ou l’organisation, il les réutilise et met simplement à jour le rôle de membre. Distribuez un mot de passe temporaire au client, qui pourra le changer via l’interface.

## 3. Configurer le frontend

1. Définissez `VITE_API_URL` (et `VITE_WS_URL` le cas échéant) vers le backend de l’organisation.
2. Ajoutez `VITE_TENOR_API_KEY` si vous souhaitez activer la recherche GIF Tenor (l’interface fonctionnera sinon avec la bibliothèque locale).
3. Déployez le frontend (`npm run build`) sur l’hébergement retenu.

## 4. Gestion continue

- Les propriétaires/administrateurs peuvent promouvoir d’autres membres via Paramètres → Administration de l’organisation.
- Pour créer une nouvelle organisation, répétez ce processus avec une nouvelle base de données et un nouvel `.env`.
- Surveillez les emojis/GIFs côté frontend : sans clé Tenor, seule la bibliothèque interne est proposée.

En suivant ces étapes, chaque locataire conserve son isolation technique (base de données séparée) tout en profitant des mêmes binaires applicatifs.

