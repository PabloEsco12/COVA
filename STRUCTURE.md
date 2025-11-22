Project tree (rappel)
======================

- `backend/` : API FastAPI, modèles SQLAlchemy, migrations Alembic, tests d'intégration (`backend/tests` via `pytest`).
- `frontend/secure_messagerie/` : application Vue 3, source sous `src/`, scripts npm via `package.json`.
- `docs/` : documentation produit/technique spécifique (ex. tenant_onboarding).
- `scripts/` : scripts utilitaires au niveau racine (ex. `debug-send.js` Playwright pour le front).

Notes
-----
- Tests backend : depuis `backend/`, `pytest` cible automatiquement `backend/tests` (voir `backend/pytest.ini`), prévoir une base Postgres de test (`DATABASE_URL`).
- Scripts front : privilégier `package.json` pour les commandes liées au front; réserver `scripts/` aux utilitaires ponctuels multi-projet.
