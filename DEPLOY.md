# SlotBook — Production Deploy

A single-VPS deploy that ships HTTPS, auto-restart, and a one-command bootstrap.

## Prerequisites

- Linux VPS with at least 2 GB RAM / 1 vCPU / 20 GB disk
- Docker Engine 24+ and Docker Compose plugin (`docker compose version`)
- A registered domain pointing at the server (A record → server IP)
- Open ports: 80 + 443 (and 443/UDP for HTTP/3)
- A Telegram bot — create one via [@BotFather](https://t.me/BotFather) and copy its token

## 1. Clone

```bash
ssh root@your-server
git clone https://github.com/your-org/slotbook.git /opt/slotbook
cd /opt/slotbook
```

## 2. Configure environment

```bash
cp .env.production.example .env.production
```

Edit `.env.production`. Required values:

| Var | How to set |
|---|---|
| `DOMAIN` | Your FQDN, e.g. `slotbook.example.com` |
| `POSTGRES_PASSWORD` | `openssl rand -base64 24` |
| `JWT_SECRET` | `openssl rand -hex 32` |
| `BOT_TOKEN` | from @BotFather |
| `BOT_ADMIN_TELEGRAM_IDS` | your Telegram numeric ID (use [@userinfobot](https://t.me/userinfobot)) |
| `BOT_WEBHOOK_SECRET_TOKEN` | `openssl rand -hex 24` |

The other defaults are sensible. Save the file.

## 3. Bring up the stack

```bash
./scripts/deploy.sh
```

This:
1. Pulls latest commits.
2. Builds the api/bot/worker/miniapp images.
3. Runs Alembic migrations.
4. Starts all 6 services (`api`, `bot`, `worker`, `miniapp`, `postgres`, `caddy`).

First run takes ~3 minutes (image builds). Caddy negotiates a TLS cert from Let's Encrypt automatically on first request to `https://<DOMAIN>`.

## 4. Seed business and demo data

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production \
  run --rm api uv run python seed.py --demo
```

This creates the singleton `Business` row from your env vars and (optionally) demo services/staff/booking. Idempotent — safe to re-run.

## 5. Smoke test

```bash
curl https://<DOMAIN>/health
# {"status":"ok"}
```

Open `https://<DOMAIN>` in a browser — the Mini App should render (the cream background, "Привет, друг" headline).

Send `/start` to your bot in Telegram. You should see the greeting + main menu with the "Открыть SlotBook" button.

## 6. Configure Mini App in @BotFather

1. Open @BotFather → `/mybots` → your bot → "Bot Settings" → "Menu Button" → "Configure Menu Button".
2. Set Button URL to `https://<DOMAIN>`.
3. (Optional) Set the Mini App URL in "Configure Mini App" if you want a separate Mini App entry.

## 7. Schedule daily backups (optional)

```bash
crontab -e
```

Add:

```cron
0 3 * * * cd /opt/slotbook && ./scripts/backup_db.sh >> /var/log/slotbook-backup.log 2>&1
```

Backups land in `/opt/slotbook/backups/booking_YYYYMMDD_HHMMSS.sql.gz`.

## 8. Day-2 operations

- **View logs:** `docker compose -f docker-compose.prod.yml logs -f api bot worker caddy`
- **Restart a service:** `docker compose -f docker-compose.prod.yml restart bot`
- **Apply a new migration:** `./scripts/deploy.sh` (re-runs migrations every deploy)
- **Restore from backup:** `gunzip -c backups/X.sql.gz | docker compose -f docker-compose.prod.yml --env-file .env.production exec -T postgres psql -U booking -d booking`

## Troubleshooting

**Caddy can't get a cert.** Confirm DNS resolves to your server and ports 80/443 are open. Run `docker compose -f docker-compose.prod.yml logs caddy`.

**Bot doesn't respond.** Check `BOT_TOKEN` is correct and `BOT_WEBHOOK_URL` matches `https://<DOMAIN>/webhook/telegram`. Re-run deploy to re-register webhook. Look at `docker compose logs bot` for the `bot.webhook_listening` line.

**`5xx` from `/health`.** Check `docker compose logs api`. Likely DB not migrated; run `./scripts/deploy.sh` again or do the migration manually:
```bash
docker compose -f docker-compose.prod.yml --env-file .env.production run --rm api uv run alembic upgrade head
```

**Mini App shows blank.** Verify `MINI_APP_URL=https://<DOMAIN>` in `.env.production` and rebuild miniapp image (`docker compose -f docker-compose.prod.yml --env-file .env.production build miniapp`).
