#!/usr/bin/env bash
# scripts/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env.production ]; then
  echo "ERROR: .env.production not found. Copy .env.production.example first."
  exit 1
fi

# Pull latest if branch tracks a remote; otherwise skip.
if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
  echo "=> Pull latest..."
  git pull --ff-only
else
  echo "=> Branch has no upstream — skipping git pull. Make sure your local state is current."
fi

echo "=> Build images..."
docker compose -f docker-compose.prod.yml --env-file .env.production build

echo "=> Run migrations..."
docker compose -f docker-compose.prod.yml --env-file .env.production run --rm api \
  uv run alembic upgrade head

echo "=> Restart services..."
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

echo
echo "=> Deploy complete. Tail logs with:"
echo "   docker compose -f docker-compose.prod.yml logs -f"
