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

# Ensure the postgres container is running — cron'd backups on a freshly rebooted
# box otherwise fail silently when the stack hasn't been brought up yet.
if ! docker compose -f docker-compose.prod.yml --env-file .env.production ps --status running --services | grep -q '^postgres$'; then
  echo "WARN: postgres container not running. Starting it..."
  docker compose -f docker-compose.prod.yml --env-file .env.production up -d postgres
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres \
        pg_isready -U "${POSTGRES_USER:-booking}" -d "${POSTGRES_DB:-booking}" >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done
fi

docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-booking}" -d "${POSTGRES_DB:-booking}" | gzip > "$out"

# Protect the dump — it contains all production data.
chmod 600 "$out"

echo "Backup written to $out ($(du -h "$out" | cut -f1))"
