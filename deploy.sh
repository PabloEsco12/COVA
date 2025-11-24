#!/usr/bin/env bash
# Deploiement simple de la stack docker-compose en production.
set -euo pipefail

echo "Pull Git..."
git pull origin main

echo "Down..."
docker compose -f docker-compose.prod.yml down

echo "Build (no cache)..."
docker compose -f docker-compose.prod.yml build --no-cache

echo "Up..."
docker compose -f docker-compose.prod.yml up -d

echo "Prune images dangling..."
docker image prune -f

echo "Deployment OK"
