# Dog Log

Daily dog care tracking — mobile PWA + desktop app.

## What it does

- **Walk tab**: Log pee/poo events per dog with one tap. Status matrix shows time-since and count-today for each dog, replacing the fridge whiteboard.
- **Health tab**: Log health events (6 types), add notes + photo post-log via edit sheet. History unfiltered for vet reference.
- **Meals tab**: Track food consumption % per meal slot *(Sprint 4)*
- **Desktop**: Milestones, vet visits, weight log, dry food reorder *(Sprint 6+)*
- **Google Sheets**: Daily export for vet log, one-time history import *(Sprint 9-10)*

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI + SQLAlchemy + SQLite, Docker on Mint (port 8001) |
| Mobile | Vite + React PWA, WiFi-gate sync (silent on cellular) |
| Desktop | PySide6 *(Sprint 6+)* |

## Dev setup

```bat
start_dev.bat
```

Starts backend on `0.0.0.0:8001` (new window) and Vite dev server on `:5173` (current window).

On mobile, navigate to `http://[dev-machine-ip]:5173/doglog/` and enter `http://[dev-machine-ip]:5173` as the backend URL. The Vite dev server proxies API calls to port 8001.

## Deploy

```bat
deploy_to_prod.bat
```

SSH git pull + docker compose rebuild on Mint. First deploy: add the `/doglog` nginx location block from `nginx/doglog-location.conf` to Mint's nginx config, then reload nginx.

## Dogs

Tess and Pickles are seeded on first run. Dogs are configurable via the API.

---

## Version History

### v0.7.1 (2026-05-27)
- Fixed: online-posted walk and health events now written to Dexie immediately after a successful POST — previously, if connectivity dropped after the POST succeeded, the event appeared in the status matrix (React state) but was missing from the history rows (which fall back to Dexie when offline)

### v0.7.0 (2026-05-26)
- New: Swipe left to delete on Walk and Health tabs — replaces checkbox delete; swipe reveals red Delete button, tap to confirm; snap-back if threshold not met
- New: `SwipeableRow` shared component (`mobile/src/components/SwipeableRow.jsx`)
- Fixed: Lightbox photo now fills full screen correctly — was clipped to edit sheet due to `position:fixed` inside `transform`. Fixed with `ReactDOM.createPortal` to `document.body`
- Fixed: `flushQueue` no longer deletes queue entries on 5xx responses — `fetch()` resolves on 502 without throwing; added `res.ok` check before delete across all three queues (events, health, meals). Same fix applied to grow
- Fixed: nginx `proxy_pass` changed from `localhost` to `127.0.0.1` — after clean reboot Linux resolves `localhost` to `::1` (IPv6) but Docker only binds IPv4; caused all requests to 502 after power outage
- New: ConnectPage pre-fills `https://mint.local` on fresh install
- New: `mint.local` dashboard — landing page at `https://mint.local/` with prod app links + container start times + dev step instructions
- New: `/doglog/version` endpoint returns container start time
- New: `docs/android-site-settings-shortcut.md` — plain-English guide to the Chrome Site Settings shortcut for PWA cache management

### v0.6.0 (2026-05-25)
- New: Meals tab — date pager (← Mon May 25 →), per-dog slot grids built from `meal_slots.ini`; tap any row to open edit sheet
- New: Meal edit sheet — % chips (0/25/50/75/100), notes, ingredient checklist (from `meal_ingredients.ini`); upsert by (dog, slot, date)
- New: null = not yet logged (—), 0% = skipped (red), >0% = consumed (green)
- New: Ingredients stored as JSON snapshot per record — history preserved when ini changes
- New: Offline meal queue (mealQueue in Dexie v3); queue badge includes meal queue
- New: `health_types.ini`, `meal_slots.ini`, `meal_ingredients.ini` — edit on Mint, no rebuild needed
- New: ConfigContext — dogs + health types + meal slots + ingredients fetched once at startup, cached in localStorage, refreshed on sync; eliminates per-tab fetch delay
- Changed: Health row tap opens edit sheet; `…` button removed
- Changed: Health history rows show `mm/dd/yy` date instead of day abbreviation
- Changed: Health filter bar — 7d/30d/90d/All date pills + dog chips + type picker (defaults to 30d)
- Changed: Health lightbox fills full screen (was max 100% of container)
- Changed: Health history limit increased to 200 records
- New: PWA icon — dog emoji 🐶 SVG on blue background

### v0.5.0 (2026-05-24)
- New: Health tab fully implemented — 6-type slide-up picker (^), dog carousel, LOG button
- New: Health history rows — stacked time block, notes preview, `…` edit sheet (notes + photo via PATCH)
- New: Photo storage — blob in SQLite, base64 over the wire, compressed client-side to max 1200px / JPEG 0.85 before upload
- New: Tap photo thumbnail in edit sheet to view full screen (lightbox)
- New: Offline queue support for health events (same pattern as pee/poo)
- New: Sync includes health events; queue badge counts both queues
- Sprint plan hygiene: Sessions 2–5 consolidated into Sprint 2; letter-suffix convention for unplanned sprints

### v0.4.1 (2026-05-24)
- Fixed: duplicate events on Walk tab — server now enforces UNIQUE(dog_id, type, timestamp); migration deduplicates existing rows; server returns existing event on conflict (idempotent POST)
- Changed: history rows now stack day label over time ("Sun" / "5:43pm") — consistent tall-row design shared with upcoming Health tab

### v0.4.0 (2026-05-24)
- New: hamburger menu — slide-out drawer replacing direct ConnectPage link; shows backend URL + build date+time
- New: History screen — rolling 7-day pee/poo grid per dog; poo=0 highlighted red for health tracking
- New: `/doglog/history/?days=7` backend endpoint (daily counts grouped by dog)
- Fixed: Walk tab offline fallback now applies `since=today` filter (previously showed all historical events when offline)
- Changed: history row timestamps now show day-of-week prefix ("Sun 8:49am")

### v0.3.1 (2026-05-23)
- Fixed: event timestamps displayed 4h ahead on EDT — Docker/Mint server runs in UTC so `datetime.now()` was UTC; client now always sends `timestamp: localISOString()` in the POST body, server no longer generates timestamps
- Fixed: `since=` filter in history used `toISOString()` (UTC midnight) instead of local midnight

### v0.3.0 (2026-05-23)
- Fixed: 3× event duplication on WiFi connect — concurrent `doSync()` calls each flushed the queue before any deleted entries; fixed with `syncInProgressRef` guard
- Fixed: status strip showed stale "none today" after offline logging — `syncVersion` counter now triggers WalkPage to re-fetch after background sync
- Fixed: tab bar pushed off screen when status strip rendered — tab bar is now `position: fixed; bottom: 0`
- Renamed: Adverse tab → Health (route `/adverse` → `/health`, new `HealthPage.jsx`)
- Style: carousel `›` and Log buttons now outline-only, white fill, black non-bold text

### v0.2.0 (2026-05-22)
- First production deploy to Mint — live at `https://mint.local/doglog/`
- Installed as standalone PWA alongside Grow (separate scopes, no conflict)
- Walk tab UI overhaul: history fills middle, carousels + LOG at bottom (thumb-friendly)
- Dogs sorted reverse-alpha (Tess first); Poo → Poop; tab order Walk | Meals | Adverse
- Signal dot on white circle for visibility; history rows boxed; haptic on LOG tap
- Offline event display: queued events now show in history immediately
- Offline delete: removes from queue and local DB atomically; badge updates instantly
- Build timestamp on connect screen for version verification
- Fixed Grow service worker scope (was intercepting `/doglog/` navigation requests)

### v0.1.0 (2026-05-20)
- Sprint 1: Full scaffold shipped and tested on Android
- Backend: FastAPI, dogs/events/status endpoints, SQLite, Docker
- Mobile: Walk tab with status matrix, dog+event carousels, offline queue, WiFi-gate sync
- Vite dev proxy routes API through :5173 (avoids cross-origin caching on mobile)
