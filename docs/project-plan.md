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
| Google Sheets | One-time import for history; daily export for ongoing vet log |

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

## Google Sheets Format

- One tab per calendar month (e.g. `2026-05`)
- Summary tab per calendar year
- Clean new format — old data converted to match
- Daily export job writes to current month tab
- Import script: one-time migration from existing Google Sheet

---

## Sprint History

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

*(empty — pull from backlog at next session start)*

---

## Backlog

*Numbering convention: planned sprints keep their number. Unplanned sprints that jump the queue get a letter suffix (e.g. Sprint 3B) — no renumbering downstream.*

1. **Sprint 4a — Meals tab refinements**
   After field use from Sprint 4. Two items to design together once patterns are clear:
   - **Meal row indicators**: small visual flags on logged rows hinting at what's in the edit sheet
     (e.g. notes dot, ingredient dot) — design after seeing what's actually useful in practice.
   - **Exception/substitution handling**: how to record when a meal deviates from the default
     (different ingredient, treat substitution, etc.) — design TBD from real use.
   Depends on: Sprint 4

2. **Sprint 5 — Medications**
   Config (desktop): add/edit medications per dog — name, dosage, frequency, start/end dates.
   Data model: add `medication_doses` table (dog_id, medication_id, timestamp) for dose events.
   Logging (mobile): integrated into Meals tab — dose logging lives alongside meal logging.
   Current use case: Pickles takes a GI med twice daily (morning + bedtime, with snacks).
   Flea/tick prevention is managed offline — not in scope.
   Vet report: dose history joins to medication config for dated medication records.
   Design note: Meals tab UX will need care to stay crisp with medications added.
   Depends on: Sprint 1, Sprint 4

3. **Sprint 6 — Desktop scaffold + milestones**
   PySide6 desktop app, dog milestones (vet visits, weight log, notable trips).
   Include Pull Prod DB utility (SSH + docker cp pattern from grow) so migrations can be
   tested against real data locally before deploying. Add to Settings widget.
   Depends on: Sprint 1 (shared backend)

4. **Sprint 7 — Desktop: dog config + meal composition**
   Dog add/edit/archive, meal config with dated versions.
   Depends on: Sprint 6

5. **Sprint 8 — Desktop: dry food inventory**
   Dry food purchase log, consumption pattern, reorder schedule display.
   Depends on: Sprint 6

6. **Sprint 9 — Google Sheets import**
   One-time migration script: read existing Google Sheet, map to data model, import to SQLite.
   Depends on: Sprints 1–5 (full data model in place)

7. **Sprint 10 — Google Sheets daily export**
   Daily export job: write to current month tab in new sheet format. Summary tab.
   Depends on: Sprint 9 (sheet format established)

8. **Sprint 3B — Health tab filtering**
   Health history currently shows all events (no date filter) — correct for vet reference.
   Review whether date range filtering or search is ever needed. Low priority; only add if
   history grows unwieldy in practice.
   Depends on: Sprint 3

9. **Stretch — Raspberry Pi fridge display**
    Pi Zero W + small display polling `/api/status`, renders status matrix on the fridge.
    Depends on: Sprint 1 (`/api/status` endpoint)

---

## Open Questions

- [ ] Status matrix color thresholds: what elapsed times trigger yellow/red per event type? (defaults: pee 4h/6h, poo 8h/12h — confirm after field use)
- [ ] Google Sheets existing data: what columns/tabs does the current sheet use? (needed for import script)
- [ ] Meal slots: am/pm only, or more granular (breakfast/lunch/dinner/snack)?
- [x] Photo storage: blob in SQLite, base64 over the wire, compressed to max 1200px client-side before upload

## Sprint 1 Deployment Checklist Note

Before first test on Windows desktop/browser: add `mint.local` static entry to
`C:\Windows\System32\drivers\etc\hosts` (requires admin). Windows delays `.local` resolution
by 1–2s per connection by querying regular DNS first. This killed grow's initial response
time until fixed. Do this before the first "why is it so slow?" moment.
