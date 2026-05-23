# Doglog — Project Notes for Claude

## Stack
- Backend: FastAPI + SQLAlchemy + SQLite, port 8001, Docker on Mint
- Mobile: Vite + React PWA, Dexie.js offline, WiFi-gate sync
- Desktop: PySide6 (Sprint 6+, not started yet)
- Project plan: `docs/project-plan.md`

## Dev commands
- `start_dev.bat` — starts backend (0.0.0.0:8001) + Vite dev server (5173)
- `deploy_to_prod.bat` — git pull + docker compose rebuild on Mint

## Key files
- `backend/main.py` — FastAPI app, migration startup, seeds Tess + Pickles on first run
- `backend/models.py` — full data model (all 8 tables)
- `backend/routers/` — dogs, events, status
- `mobile/src/pages/WalkPage.jsx` — primary UI: status matrix, carousels, history
- `mobile/src/pages/HealthPage.jsx` — Health tab shell (Sprint 3)
- `mobile/src/SyncContext.jsx` — sync orchestration, syncInProgressRef guard, syncVersion counter
- `mobile/src/sync.js` — WiFi-gate sync, localISOString(), queueEvent, deleteEvent
- `mobile/src/api.js` — api.get/post/delete, localGet offline fallback
- `mobile/vite.config.js` — proxy config, PWA manifest (scope: /doglog/), build timestamp
- `mobile/scripts/generate-icons.cjs` — generates PWA icons (run once, outputs to public/icons/)

## Architecture & technique docs (canonical source: claude repo)

- `D:\Users\mail\Documents\GitHub\claude\docs\dev-workflow\vite-pwa-dev-proxy.md` — why the Vite proxy is required for any PWA tested on a physical device; pattern for all future apps
- `D:\Users\mail\Documents\GitHub\claude\docs\dev-workflow\dev-prod-workflow.md` — dev/prod split pattern (shared with grow)

## Critical dev patterns

### Vite proxy (mandatory for mobile dev)
The Vite dev server proxies API routes (`/doglog/dogs`, `/doglog/events`, etc.) to
`http://127.0.0.1:8001`. This means the mobile ConnectPage URL is the Vite server
IP:5173, NOT port 8001 directly. Without this, Android Chrome caches HTML responses
from port 8001 and breaks the app.

### Never build dist/ locally during dev
`mobile/dist/` must not exist when running uvicorn directly. FastAPI's StaticFiles
mount at `/doglog` intercepts ALL paths under that prefix — including API routes like
`/doglog/dogs/` — and returns index.html. dist/ is gitignored. Only build in Docker.

### Timestamp storage — always local time
Backend uses `datetime.now()` (local, naive). Frontend queueEvent uses `localISOString()`
(also local, no Z suffix). Never use `new Date().toISOString()` (UTC) for event
timestamps — it stores UTC but the backend returns it without Z, so the browser
treats it as local time → displays 4 hours ahead (EDT offset).

### api.js fetch pattern
Always `return await res.json()` (not `return res.json()`). Without await, the promise
escapes the try/catch and JSON parse errors propagate uncaught instead of falling back
to the Dexie offline store.

## Sync patterns

### Concurrency guard on doSync
`SyncContext.doSync()` uses `syncInProgressRef` (a `useRef`) to prevent concurrent calls. React state (`setSyncing`) is not sufficient — state updates batch and don't take effect before the next call starts. The ref is synchronous and race-safe. Without this guard, Android's Network Information API fires the connection `change` event 2–3× on WiFi connect, causing `flushQueue()` to POST each queued event multiple times.

### syncVersion — trigger page refresh after background sync
`SyncContext` exposes a `syncVersion` counter (incremented after each successful sync). Pages watch it via `useEffect([syncVersion, ...])` to re-fetch events and status. This ensures the UI reflects server state after a background sync completes — critical for the status strip, which shows server-side computed data that doesn't update from Dexie alone.

## Mobile UI design decisions
- One-handed right-handed: carousel [›] and Log lower-right for thumb reach
- Layout: header → status strip → history (scrollable, flex:1) → carousels → LOG → tab bar
- Three tabs: Walk | Meals | Health (Meals daily use, Health rare — order intentional)
- Dogs sorted reverse-alpha everywhere (Tess first — primary subject)
- Event type: "Poop" not "Poo" (too visually similar to "Pee"); backend still stores 'poo'
- Status matrix: collapsible strip at top of Walk tab, replaces fridge whiteboard
- Poop thresholds: yellow > 8h, red > 12h. Pee: yellow > 4h, red > 6h
- Meals: stepped carousel 0/25/50/75/100%, default 100
- Pickles: track_pee = False (pee column always shows —)
- Signal dot: white circle background so it's visible against blue header
- Build timestamp visible on connect screen (hamburger → connect) for version verification

## ConnectPage URL
Enter `https://mint.local` (NOT `https://mint.local/doglog`). ConnectPage appends
`/doglog/health` to test connectivity, so the stored base URL must not include `/doglog`.

## Dogs
Tess (track_pee=True) and Pickles (track_pee=False) seeded on first run if no dogs exist.
Dogs are configurable — no hardcoding beyond the seed.

## Deployment notes
- Backend port 8001 (grow uses 8000 — don't conflict)
- nginx `/doglog` location block already added to Mint's grow.conf (2026-05-22)
- Add `mint.local` to Windows hosts file before first load test (see global CLAUDE.md)
- Windows Firewall: port 8001 needs an inbound allow rule for dev
- Prod URL: `https://mint.local/doglog/` — installed as PWA on phone

## Offline patterns
- `queueEvent` writes to both `db.eventQueue` AND `db.events` (same timestamp, local ISO format)
  so history shows queued events immediately without a sync
- `deleteEvent` in sync.js handles both queued (remove from eventQueue + db.events) and
  synced (server DELETE + db.events) events; always removes locally regardless
- `api.js localGet` matches `/events/` with `startsWith` to handle `?since=` query params
- `refreshQueueCount()` must be called after log AND delete to keep badge accurate
