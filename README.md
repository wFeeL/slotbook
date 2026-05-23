# SlotBook

> Online booking system over Telegram — sell as a template to barbershops, salons, tutors, photographers, etc.

A complete six-part product:

| # | What | Status |
|---|---|---|
| 1 | FastAPI backend with race-protected booking | ✅ |
| 2 | aiogram Bot with admin notifications | ✅ |
| 3 | Telegram Mini App (React) with Soft/Organic aesthetic | ✅ |
| 4 | Admin panel inside the Mini App | ✅ |
| 5 | Reminders worker (24h + 2h notifications) | ✅ |
| 6 | Production deployment with Caddy + auto-HTTPS | ✅ |

For **production deployment**: see [DEPLOY.md](./DEPLOY.md).

---

## What this delivers

- Telegram `initData` → JWT authentication (HMAC-SHA-256 validation).
- Slot calculation that respects working hours, exceptions, buffer, and timezone.
- Booking creation with `SELECT FOR UPDATE` + unique partial index race protection.
- Client and admin REST endpoints under `/api/v1`.
- Postgres schema via Alembic, structured logging, domain error envelope.
- aiogram-driven bot for the start menu, admin notifications, and cancellation buttons.
- React Mini App (Vite + Tailwind 4 + React Router 7) with the full booking flow + admin panel.
- APScheduler worker for 24h / 2h reminders.
- Docker Compose for local dev and `docker-compose.prod.yml` + Caddy for production.

## Architecture

```
Internet ──► Caddy (TLS) ──► api / bot / miniapp           (all in compose)
                                │
                                ▼
                          PostgreSQL
                                ▲
                                │
                              worker (separate process)
```

Times are stored as `TIMESTAMP WITH TIME ZONE` (UTC) end-to-end. Conversion to the business' IANA timezone happens only at edges (slot calc and response rendering).

## Local development

### Prerequisites

- Docker + Docker Compose
- [uv](https://github.com/astral-sh/uv) for Python deps
- Node 20+ for the Mini App
- Python 3.12+ (only needed for running outside Docker)

### Bring up everything

```bash
git clone <repo> slot_book_bot
cd slot_book_bot

cp backend/.env.example backend/.env
# Edit backend/.env — at minimum: BOT_TOKEN, JWT_SECRET, BOT_ADMIN_TELEGRAM_IDS.

docker compose up -d postgres
cd backend
uv sync --all-groups
uv run alembic upgrade head
uv run python seed.py --demo
docker compose up -d api bot worker miniapp
```

- API: <http://localhost:8000/health> · <http://localhost:8000/docs>
- Mini App: <http://localhost:5174>

The Mini App in dev supports a `?devToken=<jwt>` query param to bypass Telegram-only auth in a normal browser.

### Frontend dev server (hot reload)

```bash
cd miniapp
npm install
cp .env.example .env
npm run dev   # http://localhost:5173 with proxy to :8000
```

## Tests

```bash
cd backend
docker compose up -d postgres
export TEST_DATABASE_URL=postgresql+asyncpg://booking:booking@localhost:5432/booking_test
uv run pytest
```

```bash
cd miniapp
npx vitest run
```

The backend suite includes a real-Postgres race-condition test (`tests/integration/test_race_condition.py`) that proves concurrent booking attempts yield exactly one success.

## Migrations

```bash
cd backend
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

## Bot setup

Polling mode is the default for local dev. For prod, the bot runs in webhook mode behind Caddy — see [DEPLOY.md](./DEPLOY.md).

`/start`, `/help`, `/my_bookings` are wired. Admin notifications include `[❌ Отменить]` and `[📋 Открыть в панели]` inline buttons.

## Repository layout

```
backend/
  app/
    main.py
    core/                 # config, security, errors, telegram_auth, time
    api/                  # routes + deps
    bot/                  # aiogram routers + texts + keyboards
    db/                   # models + repositories + session
    schemas/              # Pydantic DTOs
    services/             # business logic
    workers/              # reminders tick + APScheduler runner
  alembic/                # migrations
  tests/
  seed.py
  main_bot.py
  main_worker.py
miniapp/
  src/
    app.tsx
    pages/                # routes (incl. /admin/*)
    features/             # cross-cutting flows (auth, booking-flow, admin-*)
    entities/             # API hooks + presentational components
    shared/               # UI primitives, API client, stores, Telegram wrappers
infra/
  caddy/Caddyfile         # production reverse-proxy config
  postgres/init-test-db.sql
docs/
  superpowers/specs/      # design specs (one per sub-project)
  superpowers/plans/      # implementation plans
scripts/
  deploy.sh
  backup_db.sh
docker-compose.yml        # dev (source bind mounts, exposed ports)
docker-compose.prod.yml   # prod (immutable, Caddy front, no host DB port)
.env.production.example
DEPLOY.md
```

## Defending against double-booking

The booking-creation transaction runs:

1. `SELECT … FROM bookings WHERE staff_id = ? AND status IN ('pending','confirmed') AND tstzrange(starts_at, ends_at, '[)') && tstzrange(new_start, new_end, '[)') FOR UPDATE`.
2. If any rows return → `409 slot_already_taken`.
3. Otherwise revalidate against working hours and insert.

A unique partial index `bookings_active_by_staff (staff_id, starts_at) WHERE status IN ('pending','confirmed')` catches the empty-table race where two concurrent INSERTs both passed step 1.

## API surface (under `/api/v1`)

- `POST /auth/telegram` — exchange `initData` for a JWT.
- Client: `GET /services`, `GET /staff?service_id=…`, `GET /slots?service_id=…&staff_id=…&date=YYYY-MM-DD`, `POST /bookings`, `GET /bookings/my`, `POST /bookings/{id}/cancel`.
- Admin: `GET /admin/dashboard`, `GET /admin/bookings`, `POST /admin/bookings`, `PATCH /admin/bookings/{id}`, `POST /admin/bookings/{id}/cancel`.
- Admin CRUD: `POST/PATCH/DELETE /admin/services{,/:id}`, `POST/PATCH/DELETE /admin/staff{,/:id}`, `PUT /admin/staff/:id/services`, `GET/PUT /admin/staff/:id/working-hours`, `POST/DELETE /admin/staff/:id/exceptions`.

## Plans and specs

Design specs and implementation plans for each sub-project live in `docs/superpowers/`. Each sub-project is a self-contained slice with its own spec → plan → review → merge cycle.

## Selling the template

Pitch line: «Система онлайн-записи через Telegram». Configurable via env vars; replace `BUSINESS_NAME` and you have a new tenant. Aesthetic and Russian copy work out of the box; English/i18n is left as an exercise.
