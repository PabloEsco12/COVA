# Tests v2

Les tests d'intégration utilisent FastAPI v2 et nécessitent une base Postgres dédiée.

1. Créez une base de test (ex. securechat_v2_test).
2. Exportez DATABASE_URL vers cette base avant pytest.
3. Lancer Alembic : py -m alembic -c backend/alembic.ini upgrade head.
4. Exécuter : pytest backend/tests_v2 (en retirant le skip quand la base est prête).
