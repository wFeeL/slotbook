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

# shellcheck disable=SC1091
set -a; source .env.production; set +a

docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-booking}" -d "${POSTGRES_DB:-booking}" | gzip > "$out"

echo "Backup written to $out ($(du -h "$out" | cut -f1))"
