# SlotBook Mini App

Vite + React 19 + TypeScript SPA delivered as a Telegram Mini App. See `../docs/superpowers/specs/2026-05-23-slotbook-miniapp-design.md`.

## Local development

```bash
npm install
cp .env.example .env  # adjust VITE_API_BASE_URL if needed
npm run dev
```

Open <http://localhost:5173>. For now the app expects a backend at `http://localhost:8000` — start it with `docker compose up -d postgres api` from the repo root.

### Dev login (without Telegram)

Pass `?devToken=<valid-jwt>` to bypass `initData` exchange. To obtain a JWT in dev, use the backend's `POST /api/v1/auth/telegram` with a hand-crafted signed `initData` (see `backend/tests/api/test_auth_endpoints.py` for the helper).

## Tests

```bash
npm run test
```

## Build

```bash
npm run build
npm run preview   # serve the built bundle on :4173
```

## Docker

```bash
docker compose build miniapp
docker compose up -d miniapp
# open http://localhost:5174
```

## Aesthetic

Soft / Organic — cream backgrounds, Caveat + Nunito typography, animated SVG blob accents. See `src/styles/globals.css` for tokens.
