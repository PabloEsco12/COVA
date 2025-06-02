FROM python:3.10-slim

# ─── paquets système ─────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev gcc libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ─── dépendances Python ──────────────────────────────────
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ─── code de l’application ──────────────────────────────
COPY . .

# ─── Ajout de wait-for-it.sh ─────────────────────────────
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# ─── entrypoint ─────────────────────────────────────────
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/entrypoint.sh"]
