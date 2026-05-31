# Doglog — Project Plan

## Vision

Replace spreadsheets and a static HTML tracker with a proper mobile + desktop app for managing
daily dog care activities. Mobile is the primary use case (walk companion); desktop handles
configuration, milestones, and reporting. A Google Sheets integration maintains the ongoing
vet log and converts historical data to the new format.

---

## Architecture

| Layer | Technology |
|---|---|
| Backend | FastAPI + SQLAlchemy + SQLite, Docker on Mint |
| Mobile frontend | Vite + React PWA (reuse grow scaffold) |
| Desktop | PySide6 on Windows |
| Sync | WiFi-gate pattern — silent on cellular, auto-sync on WiFi connect |
| Dev/Prod split | `--dev` flag, `start_dev.bat`, `deploy_to_prod.bat` (same pattern as grow) |
| Excel | Reporting platform for all tabular/printed output; one-time import from user-exported legacy data |

---

## Data Model

| Table | Key fields |
|---|---|
| `dogs` | name, birthdate, breed, active |
| `pee_poo_events` | dog_id, timestamp, type (pee/poo) |
| `other_events` | dog_id, timestamp, type (vomit/diarrhea/other), photo_path, notes |
| `meals` | dog_id, timestamp, meal_slot (am/pm), consumed_pct |
| `meal_configs` | dog_id, meal_slot, food_name, amount, effective_date |
| `medications` | dog_id, name, dosage, frequency, start_date, end_date |
| `milestones` | dog_id, date, type, notes (vet visit, weight, trip, etc.) |
| `dry_food` | product, purchase_date, weight_kg, dog_id |

---

## UI Structure

### Mobile PWA

**Design principles:**

- One-handed right-handed operation — active controls (carousel [>], LOG) lower-right for thumb reach
- Hamburger menu (top-left) for infrequent actions only
- Bottom tab bar: Walk | Meals | Health (Meals daily use, Health rare)
- Carousel pattern repeats consistently across all three tabs
- Dogs sorted reverse-alpha everywhere (Tess first — she is the primary subject)
- Event type labels use "Poop" not "Poo" (too visually similar to "Pee")

**Three tabs:**

**Walk tab (primary):**
```
[≡]  Dog Log              [●]      ← signal dot on white circle for visibility
────────────────────────────────
 Tess poop 2.1h ago ▾             ← collapsible status strip
────────────────────────────────
  10:30a  Tess: Poop       [ ]    ← history fills available space (scrollable)
  10:15a  Tess: Pee        [ ]    ← rows are boxed with thin grey border
  ...                  [Delete]   ← appears when any checkbox checked
────────────────────────────────
Dog      Tess                [>]   ← carousels at bottom for thumb reach
Type     Pee                 [>]
                          [LOG]    ← right-aligned, lower position
────────────────────────────────
[ Walk ]  [ Meals ]  [ Health ]
```
Status strip (collapsed): one-line summary per dog, reverse-alpha order  
Status strip (expanded): full matrix — last pee time (Tess only) + last poop time + count-today per dog, color-coded green/yellow/red, resets midnight

**Health tab:**
- Same dog carousel [>]
- Event type: bottom sheet picker (slides up, full-width rows, scrollable if needed)
  - Options: Vomit / Diarrhea / Grass eating / Stomach gurgles / Dry heaves / Other
- Camera button — photo captured at log time or added via `…` edit post-log
- [LOG] right-aligned
- History rows: timestamp + dog + type, with `…` button (opens edit sheet) and checkbox (delete) coexisting on each row
- Edit sheet (via `…`): free-text comment field + optional photo; saves via PATCH
- Comment previewed inline on row if present (italicized, below main line)
- Photo storage: blob in SQLite (self-contained, no filesystem path management needed)

**Meals tab:**

- Dog carousel [>]
- Slot: bottom sheet picker (configurable list, ordered; defined in `meal_slots.json` backend config)
  - Current values: Breakfast / Snack AM / Lunch / Dinner / Snack PM
- % consumed: stepped carousel 0 / 25 / 50 / 75 / 100 [>], defaults to 100
- [LOG] right-aligned
- History: one section per dog (bold header), rows = logged slots today
  - Columns: slot | % | … | ☐ — fixed structure, section list scrollable
  - `…` opens edit sheet: ingredient checkboxes (all checked by default), editable via PATCH
  - ☐ marks row for delete
  - Scales to any number of dogs without layout changes
- Ingredient detail is optional post-log — fast path is dog + slot + % + LOG only

**Meal config (desktop, not mobile):**

- Ingredient list defined per dog + slot + effective date
- New entry supersedes previous from that date forward — history always reflects the configured meal on the day it was logged
- Slot names are app-wide config (`meal_slots.json`), not per-dog

**Hamburger menu contains:**
- Erase all data (behavior TBD)
- Less-frequent actions TBD

**History screen:** 7-day grid, daily summary, per-dog

**Food screen:** Log meal consumption % per slot per dog

**Medications screen:** Log dose given, view schedule

### Desktop (PySide6)

- Dog management (add/edit/archive)
- Milestones: vet visits, weight log, notable trips
- Meal config: food composition with dated versions
- Dry food inventory + reorder schedule

---

## Reporting (Excel)

Excel is the target platform for all tabular and printed reports. Reports are generated on demand (not on a schedule) as `.xlsx` files using `openpyxl` or similar.

**Vet Report** (Sprint 10 first target): covers a user-specified date range; includes health events, medications, weight entries, and diary entries; formatted for printing or sharing with a vet.

**Historical import** (Sprint 9): user exports legacy Google Sheet data manually (CSV or xlsx); one-time import script maps to current data model and loads to SQLite.

---

## Sprint History

**Sprint 7 — Desktop: Diary polish + dog config + meal composition + medication config** ✓ COMPLETE *(2026-05-30)*

- [x] Milestone Type filter: single-select dropdown on Diary tab toolbar
- [x] Rename "Milestones" → "Diary" throughout UI and desktop files (sidebar, page title, dialogs, `diary_widget.py`); DB table and API endpoints remain `milestones`
- [x] Notes 2 column: URL detection, renders as clickable "View post →" links opening Windows default browser
- [x] Dog add/edit/archive: Settings → Dogs tab full CRUD (name, birthdate, breed, track pee, active); archived dogs shown grey
- [x] Diary Age column: calculated from dog birthdate; 0–16 wks / # mo / # yr(s) format
- [x] Meal Config sidebar page: per-dog QSplitter panes; slot rows show current config + inline history (grey/italic); Add/Edit dialog with items table (▲▼✕ + pick list); right-click copy/paste between slots
- [x] Medications Config sidebar page: per-dog QSplitter panes; Active/Past subsections; Add/Edit dialog with doses table
- [x] Backend: migration 0006 — meal_configs + medications rebuilt as parent/child tables (meal_config_items, medication_doses)
- [x] Mobile: meal edit sheet uses per-dog-slot meal_config items instead of global ini list; falls back to ini when no config exists
- [ ] Diary text search (desktop) — deferred to Sprint 11

**Sprint 6 — Desktop scaffold + milestones** ✓ COMPLETE *(2026-05-28)*

- [x] PySide6 desktop app: sidebar nav (Milestones, Meal Config, Medications Config, Dry Food Forecast, Settings)
- [x] Milestones tab: full CRUD table, Date/Dog/Age/Type/Notes1/Notes2/Weight columns
- [x] Dog filter: three independent checkboxes (Tess / Pickles / All) — five distinct filter states
- [x] Milestones Add/Edit dialog: date picker, dog combo, type combo, notes, weight
- [x] Age column: calculated from dog birthdate + milestone date (blank until birthdates added in Sprint 7)
- [x] Settings page: QTabWidget with Dogs/Meal Slots/Meal Ingredients/Medications/Health Types/Milestone Types/App
- [x] All ini-backed Settings tabs: Add/Edit/Delete/▲ Up/▼ Down/Refresh; delete warns about orphaned records
- [x] Pull Prod DB in Settings → App tab
- [x] Backend: migration 0005 rebuilds milestones table; milestones router full CRUD
- [x] ini CRUD endpoints added to health-types, meal-slots, meal-ingredients, milestone-event-types, medication-names
- [x] milestone_event_types.ini, medication_names.ini added
- [x] scripts/import_milestones.py: Excel→DB import, auto-classifies vet/travel/train/life; 113 records imported to prod
- [x] Bug fixed: PATCH /milestones/{id} 422 — Python 3.13 name-shadowing; `date as Date` import alias

**Sprint 4c — Full mobile UI/UX polish** ✓ COMPLETE *(2026-05-28)*

- [x] Swipe navigation between tabs (Walk↔Meals↔Health); disabled in History/Multi Day sub-views; skips swipeable rows
- [x] Confirm dialog on swipe-delete (Walk + Health)
- [x] Queue dot on pending-sync rows — Walk, Health, Meals; count matches header badge
- [x] Status strip always expanded — removed collapse toggle
- [x] Walk primary rows: day abbreviation ("Thu"); History sub-view keeps mm/dd/yy
- [x] Dog/Type carousel labels removed (Walk + Health)
- [x] History button (Walk + Meals) font matched to Log (20px); "Multi Day" renamed "History"
- [x] Tab bar font size 20px
- [x] Health filter bar: dogs+type row on top, day range on bottom
- [x] Health type defaults to "(select)"; Log disabled until type chosen
- [x] Carousel/type picker buttons: hairline ring style (1.5px blue border, circular); CSS border chevron replaces ^ ASCII caret
- [x] Meals dog section headers: mixed case, pager date style, tightened padding
- [x] Walk History mode hides carousels and Log button — full height for list
- [x] Fixed: Meals empty page on history toggle-off — explicit loadLogs() call
- [x] Fixed: Meal ingredients default to checked on new records

**Sprint 4a — Meals refinements + history views** ✓ COMPLETE *(2026-05-27)*

- [x] Meal row indicators: note icon (✎) when notes non-empty; exception badge (!) when any ingredient unchecked
- [x] Walk tab: History toggle button (bottom-left of Log); inline 7-day view with All/Tess/Pickles dog chips; server-fetched LAN-only
- [x] Walk history rows updated to mm/dd/yy date format
- [x] Meals tab: Multi Day toggle (bottom-left); 30-day colored bar grid; sticky header with abbreviated slot labels (bre/am/lun/din/pm); dog chips required (no All)
- [x] Backend: GET /meal-logs/range/?dog_id=X&days=30
- [x] Retired HistoryPage.jsx and hamburger History link

**Sprint 4b — Maintenance + polish** ✓ COMPLETE *(2026-05-26 → 2026-05-27)*
- [x] Fixed: online-posted walk and health events now written to Dexie immediately — previously, if connectivity dropped after a successful POST, the event appeared in the status matrix (React state) but was invisible in the history rows (offline fallback reads Dexie only)
- [x] Fixed: nginx `proxy_pass localhost` → `127.0.0.1` — after reboot Linux resolves localhost to ::1 (IPv6) but Docker only binds IPv4; caused all requests to 502 after power outage
- [x] Fixed: `flushQueue` deleting queue entries on 5xx — `fetch()` resolves on 502 without throwing; all three queues (events, health, meals) now check `res.ok` before delete
- [x] Fixed: lightbox photo now fills full screen — `position:fixed` inside `transform` was clipping it; fixed with `createPortal` to `document.body`
- [x] New: swipe-to-delete on Walk and Health tabs — replaces checkbox; `SwipeableRow` shared component
- [x] New: ConnectPage pre-fills `https://mint.local` on fresh install
- [x] New: `mint.local` dashboard — app links with container start times + dev step instructions
- [x] New: `/doglog/version` endpoint returns container start time
- [x] New: `docs/android-site-settings-shortcut.md` — plain-English PWA cache management guide
- [x] Infra: Samba mounts on Mint use `x-systemd.automount` + `nofail` — mounts on first access, not at boot

**Sprint 4 — Meals tab + Health tab refinements** ✓ COMPLETE *(2026-05-25)*

Health tab refinements:
- [x] Health event types configurable via `health_types.ini` — edit on Mint, no rebuild
- [x] ConfigContext: dogs + health types + meal slots + ingredients loaded once at startup, cached in localStorage, refreshed on sync
- [x] WalkPage dogs from ConfigContext — eliminates per-tab fetch delay
- [x] Health row tap opens edit sheet; `…` button removed
- [x] Health row date format changed from day abbreviation to `mm/dd/yy`
- [x] Lightbox fills full screen (`width: 100vw, height: 100vh`)
- [x] Filter bar above history: 7d/30d/90d/All date pills + dog chips + type picker (defaults to 30d)
- [x] Health history limit increased to 200 records

Meals tab:
- [x] Backend: `meal_logs` table + migration 0004 (unique on dog_id + slot + meal_date)
- [x] Backend: `meal_slots.ini` + `meal_ingredients.ini` — configurable on server
- [x] Backend: `GET /meal-slots`, `GET /meal-ingredients`, `GET /meal-logs/?meal_date=`, `POST /meal-logs/` (upsert)
- [x] Mobile: MealsPage — date pager, per-dog slot grids from ini
- [x] Mobile: Tap row → edit sheet: % chips (0/25/50/75/100) + notes + ingredient checklist
- [x] Mobile: null = not logged (—), 0% = skipped (red), >0% = consumed (green)
- [x] Mobile: ingredients stored as JSON snapshot per record
- [x] Mobile: offline queue (mealQueue) + Dexie v3; queue badge includes meal queue
- [x] PWA icon: dog emoji SVG on blue background

**Sprint 3 — Health events tab** ✓ COMPLETE *(2026-05-24)*

- [x] Backend: POST/GET `/doglog/health-events/` — dog_id, type, timestamp, notes, photo (blob)
- [x] Backend: PATCH `/doglog/health-events/{id}` — edit notes + photo post-log
- [x] Backend: DELETE `/doglog/health-events/{id}`
- [x] Mobile: HealthPage — dog carousel, type slide-up bottom sheet picker (6 types, ^ button), LOG button
- [x] Mobile: Health history rows — stacked time block + dog + type + notes preview + `…` + checkbox
- [x] Mobile: `…` edit sheet — free-text comment, photo (camera or library), lightbox on tap; saves via PATCH
- [x] Mobile: offline queue support for health events (same pattern as pee/poo)
- [x] Mobile: sync includes health events (syncFromBackend clears + repopulates)
- [x] Mobile: photo compressed client-side (max 1200px, JPEG 0.85) before upload — avoids nginx body limit
- [x] Mobile: queue badge counts both pee/poo and health queues
- [x] Delete AdversePage.jsx (orphaned dead code)
- [x] Design: photo add lives in edit sheet only (post-log) — not on main log screen
- [x] Design: Health history unfiltered (no date cutoff) — all events shown for vet reference

**Sprint 2 — Deploy + stabilization** ✓ COMPLETE *(2026-05-22 → 2026-05-24)*

- [x] Walk tab UI overhaul: history fills middle, carousels + LOG at bottom
- [x] Dogs sorted reverse-alpha (Tess first) in strip and carousel
- [x] Poo → Poop in all display text; backend values unchanged
- [x] History rows boxed with thin grey border
- [x] Signal dot on white circle background (visible against blue header)
- [x] Tab order: Walk | Meals | Health across all three pages
- [x] Haptic feedback (40ms) on LOG tap
- [x] loadDogs + loadStatus converted to api.get(); dogsError debug state removed
- [x] First prod deploy to Mint — nginx, docker compose, both PWAs coexisting
- [x] Fixed Grow service worker intercepting /doglog/ (navigateFallbackAllowlist)
- [x] PWA icons generated; explicit scope in manifests for same-origin coexistence
- [x] Offline event display (queued events show in history immediately)
- [x] Offline delete (removes from eventQueue + db.events atomically; badge refreshes)
- [x] Build timestamp on connect screen for version verification
- [x] Health tab spec finalized (bottom sheet, 6 types, blob photos, comment via `…`)
- [x] Meals tab spec finalized (slot picker, % consumed default 100, ingredient checklist)
- [x] Fixed: 3× event duplication — `syncInProgressRef` guard on `doSync()` prevents concurrent queue flushes
- [x] Fixed: status strip stale after offline log — `syncVersion` counter triggers WalkPage refresh after background sync
- [x] Fixed: tab bar pushed off screen when status strip renders — `position: fixed; bottom: 0` on tab bar
- [x] Renamed: Health tab (was Adverse) — route `/health`, new `HealthPage.jsx`
- [x] Style: carousel and Log buttons — outline only, white fill, black non-bold text, "Log" mixed case
- [x] Fixed: event timestamps displayed 4h ahead on EDT — Docker/Mint runs UTC; client now always sends `timestamp: localISOString()` in POST body
- [x] Fixed: `since=` filter in loadEvents used `toISOString()` (UTC midnight) instead of local midnight
- [x] Fixed: duplicate events via UNIQUE constraint on (dog_id, type, timestamp); server returns existing event on IntegrityError
- [x] Walk tab history rows: stacked day/time in 68px time block — sets shared design language for Health tab rows

**Sprint 1 — Foundation** ✓ COMPLETE *(2026-05-20)*

Goal: Replace `index.html` with a real persisted mobile app. Dogs configurable, pee/poo
logging works end-to-end, data survives app close.

- [x] Backend: FastAPI scaffold + Docker compose on Mint
- [x] Backend: `dogs` table + CRUD endpoints
- [x] Backend: `pee_poo_events` table + POST/GET endpoints
- [x] Backend: `/doglog/status/` endpoint (returns status matrix data)
- [x] Mobile: copy grow PWA scaffold, strip grow-specific UI
- [x] Mobile: dog carousel component (from API, configurable)
- [x] Mobile: Pee/Poo entry via direct POST with offline queue fallback
- [x] Mobile: status matrix collapsible strip (green/yellow/red color bands)
- [x] Mobile: WiFi-gate sync (Network Information API, Android/Chrome)
- [x] Mobile: offline queue → sync on WiFi connect
- [x] Dev/Prod: `start_dev.bat`, `deploy_to_prod.bat`
- [x] Vite dev proxy routes API through :5173 (fixes Android caching issue)
- [x] Tested end-to-end on Android (Pixel 7a) and Desktop Chrome

Notes: QR code endpoint exists but LAN discovery UI deferred. Three-tab layout
(Walk/Health/Meals) shipped; Health and Meals are shells.

---

## Current Sprint

**Sprint 5 — Go-live prep + Mobile Medications** *(2026-05-31)*

Goal: Deploy v1.2.0 to prod, enter real config data, build mobile medication logging, and go live on June 1.

Pre-build (deploy + data):

- [ ] Deploy v1.2.0 to prod (`git pull` + `docker compose up -d --build` on Mint; migration 0006 runs automatically)
- [ ] Enter meal ingredients in prod via desktop app (prod mode)
- [ ] Enter medications in prod via desktop app (prod mode)
- [ ] Delete 3 dummy meal log records from prior testing (visible in Meals tab, May dates)
- [ ] Pull prod DB → dev via Settings → App → "Pull →" for realistic local test data

Mobile build (Sprint 5 proper):

- [ ] Backend: `medication_logs` table + migration; POST/GET/PATCH `/medication-logs/` endpoints
- [ ] Backend: prune `pee_poo_events` older than 7 days on startup
- [ ] Mobile: Medications row per dog on Meals tab (below Snack PM, lightly shaded to distinguish from meal rows)
- [ ] Mobile: row status — "X of Y given" / "Not logged" / "✓ All given"
- [ ] Mobile: slide-up dose sheet — active meds grouped by name, one checkbox per dose entry (label + amount)
- [ ] Mobile: save upserts one `medication_logs` record per medication per day (`doses_given` JSON array of given labels)
- [ ] Mobile: offline queue (`medicationQueue` + Dexie `medicationLogs`); badge includes med queue
- [ ] Go-live ✓

Depends on: Sprint 7

---

## Backlog

*Sprint naming: planned sprints keep their number. Unplanned sprints that jump the queue get a letter suffix (e.g. Sprint 3B) — no renumbering downstream. Backlog is a bullet list — never numbered, so insertions don't require renumbering.*

- **Sprint 5 — Medications (mobile logging)**
  - Meals tab: single "Medications" row per dog, below Snack PM, slightly shaded to distinguish from meal rows
  - Row status: "X of Y given" (counting individual dose entries across all active meds), "Not logged" if no log yet, "✓ All given" if complete
  - Tap → slide-up sheet; all active medications grouped by name; one checkbox per dose entry (label + amount from `medication_doses` config); loads saved state for today, unchecked only if no log exists
  - Save: upserts one `medication_logs` record per medication (dog_id, medication_id, log_date DATE, doses_given JSON array of given labels)
  - Only active medications shown (end_date null or in future); non-daily meds (e.g. Heartgard Monthly) always shown, no due-date logic
  - Offline: `medicationQueue` + Dexie `medicationLogs`; queue badge includes med queue
  - Backend: prune pee/poo events older than 7 days on startup (one SQL DELETE in `main.py`)
  - Flea/tick prevention managed offline — not in scope
  - Depends on: Sprint 7 (medication config must exist before mobile logging is useful)

- **Sprint 5a — Mobile Diary tab**
  - 4th bottom tab (Walk/Meals/Health/Diary); unified list newest-first
  - Filter bar: dog chips (Tess/Pickles, multi-select) + inline type `<select>` (All/Life/Travel/Vet/Train/Experience — labels not keys); not a bottom sheet
  - Rows: date / dog chip / type label / notes1 preview / "View post →" if Notes 2 is a URL
  - Row tap → edit sheet pre-filled; swipe left → delete with confirmation
  - Diary is last tab — right swipe navigates back to Health (extends existing swipe nav from Sprint 4c)
  - Add/Edit sheet: date picker (defaults today), dog dropdown, type dropdown (labels), notes1 textarea, notes2 URL field (optional), weight field with checkbox (optional)
  - Full offline queue: diaryEntries + diaryQueue in Dexie, same pattern as healthQueue; queue badge includes diary queue
  - Depends on: Sprint 7 (dog list stable)

- **Sprint 9 — Historical data import**
  One-time migration script: read a user-exported file from the legacy Google Sheet (CSV or xlsx),
  map to data model, import to SQLite. User handles the Google Sheets export manually; script
  consumes the resulting file.
  Depends on: Sprints 1–5 (full data model in place)

  *Assumptions to confirm at sprint start (based on Apr sheet review):*
  - Bfast / Lunch / Dinner / 9p snack columns → `meal_logs` (% consumed); confirm "9p snack" maps to "Snack PM" slot or is distinct
  - No Vomit / Vomit columns → `health_events`; confirm no other health columns exist across all months
  - Outcomes column → diary entries (one per day, raw text); user may disagree — confirm whether structured parsing is wanted
  - Notes column (Sucralfate etc.) → confirm target: diary entries, or `medications` table, or both
  - Diet column → unclear; confirm what it encodes and whether it needs to be imported
  - Streak column → assumed calculated, not imported; confirm
  - Sheet coverage: confirm which months/tabs exist and which dogs are tracked per tab
  - Lick mat ("LICK" in Outcomes text) → appears to be a separate feeding not captured in column data; confirm whether it should be a meal slot or ignored

- **Sprint 10 — Excel reports**
  Excel is the target presentation platform for all tabular and printed reports. First target:
  Vet Report — generates an xlsx covering the date range of interest, formatted for printing or
  sharing. Additional reports (weight history, medication log, meal history) added as needed.
  Depends on: Sprint 9 (data in place)

- **Sprint 11 — Diary text search (desktop)**
  QLineEdit in Diary toolbar; client-side filter on Notes 1 field on keypress; no server round-trip
  needed at current record volumes. Mobile Diary search remains in Unscheduled Future Work.
  Depends on: Sprint 7

## Unscheduled Future Work

- **Sprint 8 — Desktop: dry food inventory**
  Dry food purchase log, consumption pattern, reorder schedule display.
  Depends on: Sprint 6

- **Diary text search (mobile)**
  Mobile Diary tab search on Notes 1 field. Deferred until demand is established and record volume is understood. Options when ready: server-side LIKE query (WiFi only) or full Dexie scan (offline capable but unindexed). Desktop search is Sprint 11.

- **Stretch — Raspberry Pi fridge display**
  Pi Zero W + small display polling `/api/status`, renders status matrix on the fridge.
  Depends on: Sprint 1 (`/api/status` endpoint)

---

## Open Questions

- [ ] Status matrix color thresholds: what elapsed times trigger yellow/red per event type? (defaults: pee 4h/6h, poo 8h/12h — confirm after field use)
- [x] Google Sheets existing data: user will export manually; import script consumes the exported file (CSV or xlsx)
- [ ] Meal slots: am/pm only, or more granular (breakfast/lunch/dinner/snack)?
- [x] Photo storage: blob in SQLite, base64 over the wire, compressed to max 1200px client-side before upload

## Sprint 1 Deployment Checklist Note

Before first test on Windows desktop/browser: add `mint.local` static entry to
`C:\Windows\System32\drivers\etc\hosts` (requires admin). Windows delays `.local` resolution
by 1–2s per connection by querying regular DNS first. This killed grow's initial response
time until fixed. Do this before the first "why is it so slow?" moment.
