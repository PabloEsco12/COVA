#!/usr/bin/env bash
# Deploiement simple de la stack docker-compose en production.
set -euo pipefail

ENV_FILE=".env.prod"
COMPOSE="docker compose --env-file ${ENV_FILE} -f docker-compose.prod.yml"

if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE, aborting."
  exit 1
fi

echo "Pull Git..."
git pull origin main

echo "Down..."
$COMPOSE down

echo "Build (no cache)..."
$COMPOSE build --no-cache

echo "Up..."
$COMPOSE up -d

echo "Prune images dangling..."
docker image prune -f

echo "Deployment OK"
