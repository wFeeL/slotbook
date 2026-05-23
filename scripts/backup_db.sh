#!/usr/bin/env bash
# scripts/backup_db.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env.production ]; then
  echo "ERROR: .env.production not found."
  exit 1
fi

mkdir -p backups
ts=$(date +%Y%m%d_%H%M%S)
out="backups/booking_${ts}.sql.gz"

# Read just POSTGRES_USER / POSTGRES_DB if set; defaults are baked into compose env.
POSTGRES_USER=$(grep -E '^POSTGRES_USER=' .env.production | cut -d= -f2- | head -1)
POSTGRES_DB=$(grep -E '^POSTGRES_DB=' .env.production | cut -d= -f2- | head -1)

docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-booking}" -d "${POSTGRES_DB:-booking}" | gzip > "$out"

echo "Backup written to $out ($(du -h "$out" | cut -f1))"
