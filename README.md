# Dog Log

Daily dog care tracking — mobile PWA + desktop app.

## What it does

- **Walk tab**: Log pee/poo events per dog with one tap. Status matrix shows time-since and count-today for each dog, replacing the fridge whiteboard.
- **Health tab**: Log vomit, diarrhea, other events with camera *(Sprint 3)*
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
