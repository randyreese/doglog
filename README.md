# Dog Log

Daily dog care tracking — mobile PWA + desktop app.

## What it does

- **Walk tab**: Log pee/poo events per dog with one tap. Status matrix shows time-since and count-today for each dog, replacing the fridge whiteboard.
- **Adverse tab**: Log vomit, diarrhea, other events with camera *(Sprint 3)*
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

### v0.1.0 (2026-05-20)
- Sprint 1: Full scaffold shipped and tested on Android
- Backend: FastAPI, dogs/events/status endpoints, SQLite, Docker
- Mobile: Walk tab with status matrix, dog+event carousels, offline queue, WiFi-gate sync
- Vite dev proxy routes API through :5173 (avoids cross-origin caching on mobile)
