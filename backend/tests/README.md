Tests
=====

Tests d'integration FastAPI v2; necessitent une base Postgres dediee.

1. Creer une base (ex. `securechat_v2_test`).
2. Exporter `DATABASE_URL` vers cette base avant pytest.
3. Appliquer les migrations : `py -m alembic -c backend/alembic.ini upgrade head`.
4. Lancer : `pytest` (les tests resident dans `backend/tests`; lever le skip quand la base est prete).
