# SlotBook Backend

MVP backend for SlotBook Telegram booking system. See `docs/superpowers/specs/` for the design spec.

## Quick start (development)

```bash
docker compose up -d postgres redis
cd backend
cp .env.example .env
uv sync --all-groups
uv run uvicorn app.main:app --reload
```

Open <http://localhost:8000/health> — should return `{"status":"ok"}`.

## Tests

```bash
cd backend
uv run pytest
```
