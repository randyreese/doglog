# Dog Log

Daily dog care tracking — mobile PWA + desktop app.

## What it does

- **Walk tab**: Log pee/poo events per dog with one tap. Status matrix shows time-since and count-today for each dog, replacing the fridge whiteboard.
- **Health tab**: Log health events (6 types), add notes + photo post-log via edit sheet. History unfiltered for vet reference.
- **Meals tab**: Track food consumption % per meal slot *(Sprint 4)*
- **Desktop**: Diary (vet visits, weight log, travel, training — type filter, clickable Instagram links, age column); Settings → Dogs CRUD; **Meal Config** (per-dog-slot food composition, effective-date versioning, copy/paste between slots); **Medications Config** (per-dog active/past, multi-dose) *(Sprint 7)*
- **Google Sheets**: Daily export for vet log, one-time history import *(Sprint 9-10)*

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI + SQLAlchemy + SQLite, Docker on Mint (port 8001) |
| Mobile | Vite + React PWA, WiFi-gate sync (silent on cellular) |
| Desktop | PySide6 (`desktop/main.py --dev` for local) |

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

### v1.8.0 (2026-06-04)
- New: **Desktop Diary text search** (Sprint 11) — "Search notes:" bar below the Diary toolbar; client-side substring filter across Notes 1 and Notes 2 on every keystroke; no server round-trip; case-insensitive
- Removed: `desktop/windows/milestones_widget.py` dead code (superseded by DiaryWidget)
- Updated: `reports/VetReportTemplate.xlsm` — refined presentation layout; vet reports printed through May 2026

### v1.7.0 (2026-06-03)
- New: **Mobile Diary tab** (Sprint 5a) — 4th bottom tab (Walk/Meals/Health/Diary); dog chip filter (multi-select), event type dropdown; rows show mm/dd/yy date / dog·type / notes preview (2 lines) / "View →" link; swipe-left to delete, tap to edit; full offline queue (diaryEntries + diaryQueue in Dexie v5); sync includes milestones on every backend sync
- New: `DiaryPage.jsx` — add/edit sheet with date, dog, type, weight checkbox+field, notes, link fields; offline queued new entries flush on next WiFi sync; edit of synced entries requires connectivity
- New: `milestoneEventTypes` added to ConfigContext (fetched from `/milestone-event-types`, cached in localStorage)
- Fixed: Meals edit sheet ingredient snapshot — historical records now show the stored ingredient list from the log, not the current meal config (fixes pre-April-1 Pickles records showing wrong ingredients)
- Changed: Signal dot on all tabs upgraded from unicode dot + CSS color to emoji (🟢🟡🔴) — larger and more visible
- Changed: All tab headers consistently show "Dog Log"
- Changed: Tab bar font reduced from 20px to 15px to accommodate 4 tabs
- Changed: Swipe navigation extended — left swipe from Health → Diary; right swipe from Diary → Health

### v1.6.0 (2026-06-03)
- New: **Meals tab calendar picker** — tap the date label to open native OS date picker; navigates directly to selected date; forward navigation capped at today
- Changed: **Vet report template simplified** — single-tab template (`VetReportTemplate.xlsm`, tab `Month View`) replaces per-dog-per-year 12-tab workbooks; named range changed from `data_anchor_{month}` to `data_anchor` (workbook-scoped); `keep_vba=True` for future macro support

### v1.5.0 (2026-06-02)
- New: **Desktop Reports page** — sidebar nav item with dog selector, month/year picker, file picker, and Run button; generates Excel vet report
- New: `desktop/vet_report.py` — report generator; fetches meal logs, health events, medication logs for a selected dog + month; writes to named-range data zone in an xlsx template using `data_anchor_{month}` convention
- New: `GET /medication-logs/range/` — date-range query for medication logs (used by report generator)
- New: `GET /meal-logs/range/` — added `start_date`/`end_date` params (backward compatible; `days` still works for mobile)
- New: `GET /health-events/` — added `until` param for date-bounded queries
- New: `health_types.ini` — `[report_columns]` section; each type tagged `activity` or `event` for report column routing
- New: Settings → Health Types tab — third column "Report Column" (—/Activity/Event); Add/Edit dialogs include dropdown
- New: `reports/` folder for generated xlsx output

### v1.4.0 (2026-06-02)
- New: `scripts/import_history.py` — one-time import of 5 months (Jan–May 2026) of legacy Google Sheets data; 1,420 meal logs, 14 vomit events, 60 Sucralfate medication logs loaded to prod; `--purge`, `--dry-run`, `--force`, `--tabs`, `--dog`, `--db` flags
- New: Health tab — "Set time" toggle between type picker and Log button; reveals date + time pickers pre-filled to now; resets after each log; covers both past-date and same-day after-the-fact logging
- Fixed: `/doglog/medication-logs` missing from Vite dev proxy — GET fell through to empty Dexie store, showing all dose checkboxes unchecked in dev regardless of stored data

### v1.3.0 (2026-05-31)
- New: **Mobile medication logging** — Medications row per dog on Meals tab (shaded, below meal slots); tap opens slide-up dose sheet grouped by medication name with one checkbox per dose (label + amount shown)
- New: Row status — "Not logged" / "X of Y given" (amber) / "✓ All given" (green)
- New: `medication_logs` table + migration 0007; POST/GET `/medication-logs/` endpoints (upsert by dog+medication+date)
- New: Offline queue — `medicationQueue` + Dexie `medicationLogs`; queue badge includes med queue
- New: Active medications loaded into ConfigContext from `/medications/`, cached in localStorage
- Changed: Dexie upgraded to version 4 schema
- Changed: `pee_poo_events` older than 7 days pruned on backend startup

### v1.2.1 (2026-05-31)
- Fixed: stale queue dots on Meals tab when browsing past dates offline — `_queued` flag now cleared from `db.mealLogs` after a meal queue entry syncs successfully; previously the flag persisted in Dexie indefinitely (issue #4)
- New: `docs/dexie-offline-architecture.md` — plain-English explanation of the Walk/Health full-cache vs Meals queue-only offline pattern

### v1.2.0 (2026-05-30)
- New: **Meal Config** desktop page — per-dog QSplitter panels; per-slot table with current config + inline history (grey/italic); Add/Edit dialog with inline ingredient table (▲▼✕, pick list from ini, filtered to unused); right-click Copy/Paste between slots
- New: **Medications Config** desktop page — per-dog Active/Past QSplitter panels; Add/Edit dialog with inline dose table (▲▼✕, free-text label + amount)
- New: migration 0006 — rebuilds `meal_configs` (child table `meal_config_items`) and `medications` (child table `medication_doses`)
- New: `/meal-configs/` and `/medications/` REST endpoints (full CRUD, child table transactions)
- Changed: Mobile Meals edit sheet — ingredient checklist now shows only the configured items for that dog+slot (from `meal_configs`); falls back to global ini list if no config exists
- Changed: ConfigContext — meal configs loaded at startup alongside dogs/slots/ingredients; cached in localStorage; independent fetch (failure doesn't block other config data)
- Fixed: ConnectPage URL save now does a full page reload so ConfigContext re-fetches from the new URL

### v1.1.0 (2026-05-29)
- New: Desktop "Milestones" page renamed to **Diary** throughout UI and widget files; DB/API endpoints unchanged
- New: Diary toolbar — single-select Type filter dropdown (all types from ini)
- New: Diary Notes 2 — URLs render as clickable "View post →" links opening Windows default browser
- New: Diary Age column format — `# wks` (0–16), `# mo` (17 wks–11 mo), `# yr(s) [# mo]` (12+ mo)
- New: Settings → Dogs tab — full CRUD (add/edit/archive); archived dogs shown grey; birthdate, breed, track pee all editable
- New: Mobile Diary tab spec finalized (4th tab, full offline queue, build deferred to future sprint)

### v1.0.1 (2026-05-28)
- Fixed: PATCH /milestones/{id} returned 422 — Python 3.13 evaluated `Optional[date]` as `NoneType` because the field name `date` shadowed the imported `datetime.date` type; fixed by aliasing the import to `Date`
- Improved: milestone edit error dialog now surfaces the Pydantic validation detail from the response body

### v1.0.0 (2026-05-28)
- New: PySide6 desktop app — sidebar nav (Milestones, Meal Config, Medications Config, Dry Food Forecast, Settings)
- New: Milestones tab — full CRUD table (Date, Dog, Age calc, Type, Notes 1, Notes 2, Weight); three-checkbox dog filter (Tess / Pickles / All); double-click to edit
- New: Settings page — QTabWidget with Dogs / Meal Slots / Meal Ingredients / Medications / Health Types / Milestone Types / App tabs; all ini-backed lists support Add / Edit / Delete / Reorder
- New: Pull Prod DB button in Settings → App tab (SSH + docker cp pattern from grow)
- New: `milestone_event_types.ini` (Life/Travel/Vet/Train/Experience) and `medication_names.ini`
- New: CRUD endpoints for all ini-managed lists (health-types, meal-slots, meal-ingredients, milestone-event-types, medication-names)
- New: `scripts/import_milestones.py` — one-time Excel→DB import; auto-classifies vet/travel/train/life; 113 historical records imported for Tess + Pickles
- New: Migration 0005 — milestones table rebuilt with nullable dog_id, event_type, notes1, notes2, weight_lbs

### v0.9.0 (2026-05-28)
- New: Horizontal swipe navigation between tabs — swipe left/right to switch Walk↔Meals↔Health; disabled while in History or Multi Day sub-views; skips swipeable delete rows
- New: Confirm dialog before swipe-delete (Walk + Health) — tap Delete reveals confirm prompt instead of deleting immediately
- New: Queue dot — small red circle on any history row (Walk, Health) or meal row that is pending sync; count matches the badge in the header
- New: Walk History mode — carousels and Log button now hidden when History is open, giving the list full height
- Changed: Status strip (Walk) — always expanded; removed collapse/expand toggle
- Changed: Walk primary rows now show day abbreviation ("Thu") instead of mm/dd/yy; History sub-view rows keep mm/dd/yy
- Changed: Dog and Type labels removed from carousel rows (Walk + Health)
- Changed: History button (Walk) and History button (Meals, formerly "Multi Day") — font matched to Log button (20px); renamed "Multi Day" → "History"
- Changed: Tab bar labels — font size increased to 20px to match action buttons
- Changed: Health filter bar — Dogs + Type picker row is now on top; Day range row on bottom
- Changed: Health type picker — defaults to "(select)" instead of first type; Log button disabled until a type is chosen
- Changed: Carousel and type picker buttons (Walk + Health) — restyled to hairline ring (circular, 1.5px blue border, transparent fill); `^` replaced with CSS border chevron for precise centering
- Changed: Meals dog section headers — mixed case, matched to date pager style (16px, weight 600, #1a202c); padding tightened to preserve row height for future medication rows
- Fixed: Meals page occasionally showed empty — `loadLogs()` now called explicitly when toggling back from History view
- Fixed: Meal edit sheet ingredients now default to checked when no prior record exists (`?? true`)

### v0.8.0 (2026-05-27)
- New: Walk tab — "History" toggle button (bottom-left) opens inline 7-day view with All / Tess / Pickles dog filter chips; server-fetched, LAN-only; replaces the separate HistoryPage route
- New: Meals tab — "Multi Day" toggle button (bottom-left) opens 30-day bar grid; one row per date, one bar per slot; 100%=green, 25–75%=yellow, 0%=red, null=grey; dog chips (required, no All); sticky header row with abbreviated slot labels (bre / am / lun / din / pm)
- New: Meal row indicators — note icon (✎) when notes are present; exception badge (!) when any ingredient is unchecked
- New: Backend `GET /meal-logs/range/?dog_id=X&days=30` endpoint
- Changed: Walk history rows now show `mm/dd/yy` date instead of day-of-week abbreviation
- Removed: Standalone HistoryPage route (`/history`) and hamburger History link — history is now inline on the Walk tab

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
