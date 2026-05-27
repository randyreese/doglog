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
- `backend/models.py` — full data model (MealLog + legacy placeholder tables)
- `backend/routers/` — dogs, events, status, health, meals (all routers)
- `backend/routers/health.py` — POST/GET/PATCH/DELETE for /health-events/; GET /health-types (reads ini); photos as base64 in/out, LargeBinary in DB
- `backend/routers/meals.py` — GET /meal-slots, GET /meal-ingredients, GET/POST /meal-logs/ (upsert by dog+slot+date); GET /meal-logs/range/?dog_id=X&days=30 (multi-day summary)
- `backend/health_types.ini` — user-editable health event types; edit on Mint, no rebuild needed
- `backend/meal_slots.ini` — user-editable meal slot names
- `backend/meal_ingredients.ini` — user-editable ingredient checklist items
- `mobile/src/ConfigContext.jsx` — shared config context: dogs + health types + meal slots + ingredients; fetched once at startup, cached in localStorage, refreshed on sync
- `mobile/src/components/HamburgerMenu.jsx` — slide-out drawer: backend URL (tappable), build timestamp
- `mobile/src/components/SwipeableRow.jsx` — swipe-left-to-delete wrapper; used on Walk + Health history rows
- `mobile/src/pages/WalkPage.jsx` — primary UI: status matrix, carousels, today history + inline 7-day history toggle (History button); dogs from ConfigContext
- `mobile/src/pages/HealthPage.jsx` — Health tab: filter bar (date/dog/type), row-tap edit sheet, type list from ConfigContext
- `mobile/src/pages/MealsPage.jsx` — Meals tab: date pager, per-dog slot grids, tap-to-edit; Multi Day toggle for 30-day bar summary
- `mobile/src/SyncContext.jsx` — sync orchestration, syncInProgressRef guard, syncVersion counter, queue badge (all three queues)
- `mobile/src/sync.js` — WiFi-gate sync, localISOString(), queue/delete functions for all event types
- `mobile/src/api.js` — api.get/post/patch/delete, localGet offline fallback (events + health-events)
- `mobile/src/db.js` — Dexie v3: dogs, events, eventQueue, meta, healthEvents, healthQueue, mealLogs, mealQueue
- `mobile/vite.config.js` — proxy config, PWA manifest (scope: /doglog/), build timestamp
- `mobile/public/icons/doglog.svg` — dog emoji PWA icon (SVG, referenced in manifest)
- `mobile/scripts/generate-icons.cjs` — generates solid-color PNG fallback icons

## Architecture & technique docs (canonical source: claude repo)

- `D:\Users\mail\Documents\GitHub\claude\docs\dev-workflow\vite-pwa-dev-proxy.md` — why the Vite proxy is required for any PWA tested on a physical device; pattern for all future apps
- `D:\Users\mail\Documents\GitHub\claude\docs\dev-workflow\dev-prod-workflow.md` — dev/prod split pattern (shared with grow)
- `D:\Users\mail\Documents\GitHub\claude\docs\dev-workflow\offline-queue-idempotency.md` — how the offline queue creates a double-POST race, and the UNIQUE constraint + idempotent endpoint fix; applies to any app using flushQueue() pattern (doglog + grow)

## History row design (Walk + Health shared pattern)

Three-segment flex layout: `[timeBlock] [label]`. Row uses `gap: 8`. Wrapped in `SwipeableRow` — swipe left to reveal red Delete button, tap to confirm.
Time block: `width: 68, flexShrink: 0, flexDirection: column` — `mm/dd/yy` date (`fontSize: 11, color: '#999'`) stacked over time string (`fontSize: 14, color: '#555'`).
Health tab rows: same time block, label segment (`flex:1, flexDirection:column`) holds main line + italic notes preview. Row tap opens edit sheet.

## SwipeableRow pattern

`mobile/src/components/SwipeableRow.jsx` — reusable swipe-to-delete wrapper. Tracks touch delta, reveals 80px red Delete zone past 72px threshold, snaps back otherwise. Suppresses child `onClick` when tapping to dismiss a revealed delete zone (via `suppressNextClick` ref). Apply `marginBottom: 2, borderRadius: 4` on the outer SwipeableRow wrapper — remove from the inner row style.

## Health tab design decisions

- Photo add is post-log only (via edit sheet, not on main log screen) — you log first, then annotate
- History filtered by default to 30d; filter bar (7d/30d/90d/All + dog chips + type picker) always visible above list
- Health event types driven from `health_types.ini` via ConfigContext — no hardcoded list in frontend
- Bottom sheet type picker: full-screen overlay, sheet slides from bottom, `^` button opens it
- Photo compressed client-side before upload: max 1200px, JPEG 0.85 — avoids nginx 1MB body limit
- Photo stored as LargeBinary in SQLite, transported as base64 string in JSON
- Lightbox fills full screen: `width: 100vw, height: 100vh, objectFit: contain`

## Meals tab design decisions

- Date pager at top (← Mon May 25 →); forward disabled on today
- Per-dog sections with all meal slots always shown (pre-built from `meal_slots.ini`) — no Log button, no carousels
- null = not yet logged (shows —); 0% = explicitly skipped (shows red); >0% = consumed (shows green)
- Tap any row → edit sheet: % chips [0][25][50][75][100] + notes textarea + ingredient checklist
- Ingredients from `meal_ingredients.ini`; stored as JSON snapshot per record (preserves history when ini changes)
- Offline: mealQueue + Dexie mealLogs; upsert on flush; queue badge includes meal queue
- Desktop admin UI for ini-managed lists (health types, meal slots, ingredients) deferred to Sprint 6

## Edit sheet pattern (Health + Meals)

Slide-up overlay (`sh.overlay` / `sh.sheet`). Health: textarea + photo thumbnail (tappable → lightbox) + file input. Meals: % chips + textarea + ingredient checklist. Both: Save/Cancel, inline error on failure.

## Duplicate event prevention

`pee_poo_events` has UNIQUE constraint on `(dog_id, type, timestamp)` (migration 0002).
`log_event` catches `IntegrityError` and returns the existing event — idempotent POST.

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

### Timestamp storage — client always supplies the timestamp
The server (Docker on Mint) runs in UTC, so `datetime.now()` returns UTC — not local time.
Never let the server generate a timestamp. Always send `timestamp: localISOString()` in the
POST body for both online (`api.post('/events/', { ..., timestamp: localISOString() })`) and
offline (`queueEvent`) paths. The `since=` filter in `loadEvents` also uses
`localISOString(today)` (local midnight), not `today.toISOString()` (UTC midnight).
Without this, timestamps display 4h ahead on EDT and the today-filter may be off.

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
- Timestamp format: "ddd h:mma" e.g. "Sun 8:49am" — day prefix matters for multi-day history context
- Hamburger menu: slide-out drawer (not a route). Backend URL is tappable → ConnectPage (reconfigure only).
  ConnectPage is first-run setup only — not a named menu item. Build date+time shown in footer.
- History screen: rolling 7-day grid; poo=0 highlighted red (health signal)

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
- **Deploy from Claude Code via SSH directly** — never run `deploy_to_prod.bat` from the Bash tool;
  it has `pause` and hangs in non-interactive contexts. Use:
  `ssh mini@mint.local "cd ~/doglog && git pull"` then
  `ssh mini@mint.local "cd ~/doglog && docker compose up -d --build"`

## Offline patterns
- Online POST success (walk + health) also writes the server response to `db.events` / `db.healthEvents` via `db.events.put(event)` — prevents history gap if connectivity drops immediately after a successful POST. Without this, the event appears in React state (status matrix) but is invisible to the Dexie offline fallback in the history rows.
- `queueEvent` writes to both `db.eventQueue` AND `db.events` (same timestamp, local ISO format)
  so history shows queued events immediately without a sync
- `queueHealthEvent` same pattern — writes to `db.healthQueue` AND `db.healthEvents`
- `deleteEvent` / `deleteHealthEvent` handle both queued (remove from queue + local store) and
  synced (server DELETE + local store) events; always removes locally regardless
- `api.js localGet` applies the `since=` query param when filtering `db.events` offline — uses
  `db.events.where('timestamp').aboveOrEqual(since)` (timestamp is indexed). Without this, the
  offline fallback returns all historical events, defeating the today-only filter on Walk tab.
- Health events offline fallback: `db.healthEvents.orderBy('timestamp').reverse().limit(50)` — no since filter (health history is always unfiltered)
- `refreshQueueCount()` counts both `db.eventQueue` and `db.healthQueue` — call after log AND delete to keep badge accurate
