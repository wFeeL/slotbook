# SlotBook — MVP Backend Core (sub-project 1 of 6)

> First slice of the SlotBook product: a self-contained FastAPI backend that powers booking via Telegram Mini App.

## What this delivers

- Telegram `initData` → JWT authentication
- Slot calculation (working hours, exceptions, buffer, timezone-correct)
- Booking creation with `SELECT FOR UPDATE` race protection
- Client and admin REST endpoints under `/api/v1`
- Postgres schema via Alembic, structured logging, domain error envelope
- Docker Compose for local development; production deployment lives in sub-project 6

## Architecture (high level)

```
HTTP request
  → FastAPI router (api/routes/*.py)
    → service (services/*.py)              ← all business logic
      → repository (db/repositories/*.py)  ← all SQL
        → PostgreSQL
```

Times are stored as `TIMESTAMP WITH TIME ZONE` (UTC). Conversion to the business' IANA timezone happens only at the edges (slot calculation and response formatting). The `core/time.py` helpers guarantee no naive datetimes leak into the codebase.

## Prerequisites

- Docker + Docker Compose
- [uv](https://github.com/astral-sh/uv) for Python deps
- Python 3.12+ (only needed if you run outside Docker)

## Quick start

```bash
git clone <repo> slot_book_bot
cd slot_book_bot

# Bring up Postgres + Redis (api will start too in the next step)
docker compose up -d postgres redis

cd backend
cp .env.example .env
# Edit .env: set BOT_TOKEN, JWT_SECRET, BOT_ADMIN_TELEGRAM_IDS.

uv sync --all-groups
uv run alembic upgrade head
uv run python seed.py --demo   # populates a Demo Studio business + sample data
uv run uvicorn app.main:app --reload
```

Open <http://localhost:8000/health> — `{"status":"ok"}`.
Open <http://localhost:8000/docs> for the auto-generated OpenAPI UI.

## Bot setup

The Telegram bot runs as its own Docker service (`bot`) using the same image as the API.

### Local development (polling)

1. Create a bot via [@BotFather](https://t.me/BotFather) and copy the token.
2. Put it in `backend/.env`:
   ```
   BOT_TOKEN=123456:ABC...
   BOT_MODE=polling
   MINI_APP_URL=https://your-miniapp.example.com
   ```
3. Start everything:
   ```bash
   docker compose up -d
   ```
4. Send `/start` to your bot in Telegram. You should see the greeting + main menu.

### Production (webhook)

1. Deploy behind HTTPS (nginx/Caddy → port 8001).
2. Set in `.env`:
   ```
   APP_ENV=prod
   BOT_MODE=webhook
   BOT_WEBHOOK_URL=https://your-domain/webhook/telegram
   BOT_WEBHOOK_SECRET_TOKEN=<long-random-string>
   MINI_APP_URL=https://your-miniapp/
   ```
3. `main_bot.py` will call `setWebhook` on startup. Telegram POSTs updates with the secret-token header; the handler verifies and routes them to the dispatcher.

### Adding admins

Put your Telegram numeric ID in `BOT_ADMIN_TELEGRAM_IDS` (comma-separated) in `.env`. The promotion happens the next time you authenticate via `POST /api/v1/auth/telegram` from the Mini App — sending `/start` to the bot does NOT promote you.

### What the bot can do (sub-project 2 scope)

- `/start` — main menu with Mini App buttons
- `/help` — usage info
- `/my_bookings` — list of your upcoming bookings
- Receives admin notifications about new bookings with `[❌ Отменить]` and `[📋 Открыть в панели]` buttons

Reminders (24h / 2h before booking) are coming in sub-project 5.

## Mini App (frontend)

The client interface is a Telegram Mini App served from `miniapp/`. See `miniapp/README.md` for full setup; quick start:

```bash
cd miniapp
npm install
cp .env.example .env
npm run dev   # http://localhost:5173
```

The dev server proxies `/api/*` to `http://localhost:8000` so just `docker compose up -d postgres api` is enough.

To open inside Telegram during development, you need an HTTPS tunnel — `cloudflared` or `ngrok` pointing at `:5173` — and then set the Mini App URL in @BotFather (or set the inline keyboard `web_app` URL in `BOT_TOKEN`'s bot configuration). The local browser-preview supports `?devToken=...` to bypass Telegram auth.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `local` | One of `local`, `test`, `prod` |
| `APP_DEBUG` | `true` | Pretty-print logs and enable echo of SQL |
| `DATABASE_URL` | `postgresql+asyncpg://booking:booking@localhost:5432/booking` | Async DSN |
| `TEST_DATABASE_URL` | `postgresql+asyncpg://booking:booking@localhost:5432/booking_test` | Used only by the test suite |
| `BOT_TOKEN` | — | Telegram bot token. Required for `initData` validation |
| `BOT_ADMIN_TELEGRAM_IDS` | empty | Comma-separated list. On first auth, these Telegram IDs are promoted to `admin` |
| `JWT_SECRET` | — | HS256 secret. Set to a random long string in production |
| `JWT_EXPIRE_MINUTES` | `1440` | Token lifetime |
| `BUSINESS_NAME` | `Demo Studio` | Used to bootstrap the single business row |
| `BUSINESS_TIMEZONE` | `Europe/Moscow` | IANA timezone |
| `BUSINESS_BOOKING_BUFFER_MINUTES` | `0` | Buffer applied on both sides of each booking |
| `BUSINESS_MIN_CANCELLATION_HOURS` | `2` | Earliest a client may cancel themselves |
| `BUSINESS_SLOT_STEP_MINUTES` | `15` | Granularity at which slots are offered |

## Tests

```bash
cd backend
docker compose up -d postgres
export TEST_DATABASE_URL=postgresql+asyncpg://booking:booking@localhost:5432/booking_test
uv run pytest
```

The suite includes a real-Postgres race-condition test under `tests/integration/test_race_condition.py` that verifies concurrent booking attempts deterministically yield exactly one success.

## Migrations

```bash
cd backend
uv run alembic revision --autogenerate -m "describe change"   # author migration
uv run alembic upgrade head
uv run alembic downgrade -1
```

Migration files live under `backend/alembic/versions/`. PG enums are managed by hand — see the existing migrations for the pattern.

## Project layout

See `docs/superpowers/specs/2026-05-22-slotbook-backend-core-design.md` for full architecture rationale.

```
backend/
  app/
    main.py
    core/                 # config, security, errors, telegram_auth, time
    api/                  # routes + deps
    db/                   # models + repositories + session
    schemas/              # Pydantic DTOs
    services/             # business logic
    utils/
  alembic/
  tests/
  seed.py
  pyproject.toml
docker-compose.yml
```

## Defending against double-booking

The booking-creation transaction runs:

1. `SELECT … FROM bookings WHERE staff_id = ? AND status IN ('pending','confirmed') AND tstzrange(starts_at, ends_at, '[)') && tstzrange(new_start, new_end, '[)') FOR UPDATE`.
2. If any rows return → `409 slot_already_taken`.
3. Otherwise revalidate the slot against working hours and insert the booking.

This pattern is verified by `tests/integration/test_race_condition.py` (two concurrent `asyncio.gather` requests; exactly one 201 and one 409).

## API surface (under `/api/v1`)

- `POST /auth/telegram` — exchange `initData` for a JWT.
- `GET /services`, `GET /staff?service_id=…`, `GET /slots?service_id=…&staff_id=…&date=YYYY-MM-DD` — client browsing.
- `POST /bookings`, `GET /bookings/my`, `POST /bookings/{id}/cancel` — client booking flow.
- `GET /admin/dashboard`, `GET /admin/bookings`, `POST /admin/bookings`, `PATCH /admin/bookings/{id}`, `POST /admin/bookings/{id}/cancel` — admin booking management.
- `POST /admin/services`, `PATCH /admin/services/{id}`, `DELETE /admin/services/{id}` — services CRUD.
- `POST /admin/staff`, `PATCH /admin/staff/{id}`, `DELETE /admin/staff/{id}`, `PUT /admin/staff/{id}/services` — staff CRUD.
- `GET /admin/staff/{id}/working-hours`, `PUT /admin/staff/{id}/working-hours`, `POST /admin/staff/{id}/exceptions`, `DELETE /admin/staff/{id}/exceptions/{ex_id}` — schedule administration.

## Where this sub-project ends and the next begins

- **Sub-project 2 (Telegram Bot)** replaces the stub `NotificationService.dispatch_pending_for_booking` with aiogram-driven Bot API calls and adds a `POST /webhook/telegram` endpoint guarded by `X-Telegram-Bot-Api-Secret-Token`.
- **Sub-project 3 (Mini App)** consumes the JWT-protected `/api/v1/*` endpoints from a React SPA served separately.
- **Sub-project 5 (Worker)** reads `notifications` rows with `status='pending'` and `scheduled_for <= now` to send reminders.
- **Sub-project 6 (Deploy)** introduces a production compose file, nginx/Caddy, HTTPS, and CI.

## Plan and spec

- Design spec: `docs/superpowers/specs/2026-05-22-slotbook-backend-core-design.md`
- Implementation plan (this slice): `docs/superpowers/plans/2026-05-22-slotbook-backend-core.md`
