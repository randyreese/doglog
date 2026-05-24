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

**Session 4 — Timestamp bug fix** ✓ COMPLETE *(2026-05-23)*

- [x] Fixed: event timestamps displayed 4h ahead on EDT — Docker/Mint runs UTC; client now always sends `timestamp: localISOString()` in POST body
- [x] Fixed: `since=` filter in loadEvents used `toISOString()` (UTC midnight) instead of local midnight
- [x] Exported `localISOString(d?)` from sync.js with optional date argument

**Session 3 — UAT fixes + polish** ✓ COMPLETE *(2026-05-23)*

- [x] Fixed: 3× event duplication — `syncInProgressRef` guard on `doSync()` prevents concurrent queue flushes
- [x] Fixed: status strip stale after offline log — `syncVersion` counter triggers WalkPage refresh after background sync
- [x] Fixed: tab bar pushed off screen when status strip renders — `position: fixed; bottom: 0` on tab bar
- [x] Renamed: Health tab (was Adverse) — route `/health`, new `HealthPage.jsx`
- [x] Style: carousel and Log buttons — outline only, white fill, black non-bold text, "Log" mixed case

**Session 2 — Walk tab polish + prod deploy** ✓ COMPLETE *(2026-05-22)*

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

**Sprint 2 — History screen + hamburger menu** ✓ COMPLETE *(2026-05-24)*

- [x] Backend: `/doglog/history/?days=7` endpoint — rolling daily pee/poo counts per dog
- [x] Frontend: HamburgerMenu slide-out (History nav, backend URL + build date+time footer)
- [x] Frontend: HistoryPage — 7-day grid per dog, poo=0 highlighted red
- [x] Frontend: /history route wired in App.jsx
- [x] api.js localGet: apply since= filter offline (Walk tab today-only fix)
- [x] WalkPage: timestamp format changed to "ddd h:mma" (e.g. "Sun 8:49am")

---

## Backlog

1. **Sprint 3 — Health events tab**
   Spec complete (2026-05-22). Bottom sheet picker (6 types), blob photo storage, comment
   field editable post-log via `…` button, inline comment preview on history row.
   Depends on: Sprint 1

2. **Sprint 4 — Meals tab**
   Spec complete (2026-05-22). Dog carousel, slot bottom sheet picker (meal_slots.json config),
   % consumed carousel (default 100), ingredient checklist post-log via `…`.
   History: one section per dog, cols = slot | % | … | ☐, scrollable.
   Depends on: Sprint 1

3. **Sprint 5 — Medications**
   Config (desktop): add/edit medications per dog — name, dosage, frequency, start/end dates.
   Data model: add `medication_doses` table (dog_id, medication_id, timestamp) for dose events.
   Logging (mobile): integrated into Meals tab — dose logging lives alongside meal logging.
   Current use case: Pickles takes a GI med twice daily (morning + bedtime, with snacks).
   Flea/tick prevention is managed offline — not in scope.
   Vet report: dose history joins to medication config for dated medication records.
   Design note: Meals tab UX will need care to stay crisp with medications added.
   Depends on: Sprint 1, Sprint 4

4. **Sprint 6 — Desktop scaffold + milestones**
   PySide6 desktop app, dog milestones (vet visits, weight log, notable trips).
   Include Pull Prod DB utility (SSH + docker cp pattern from grow) so migrations can be
   tested against real data locally before deploying. Add to Settings widget.
   Depends on: Sprint 1 (shared backend)

5. **Sprint 7 — Desktop: dog config + meal composition**
   Dog add/edit/archive, meal config with dated versions.
   Depends on: Sprint 6

6. **Sprint 8 — Desktop: dry food inventory**
   Dry food purchase log, consumption pattern, reorder schedule display.
   Depends on: Sprint 6

7. **Sprint 9 — Google Sheets import**
   One-time migration script: read existing Google Sheet, map to data model, import to SQLite.
   Depends on: Sprints 1–5 (full data model in place)

8. **Sprint 10 — Google Sheets daily export**
   Daily export job: write to current month tab in new sheet format. Summary tab.
   Depends on: Sprint 9 (sheet format established)

9. **Stretch — Raspberry Pi fridge display**
    Pi Zero W + small display polling `/api/status`, renders status matrix on the fridge.
    Depends on: Sprint 1 (`/api/status` endpoint)

---

## Open Questions

- [ ] Status matrix color thresholds: what elapsed times trigger yellow/red per event type? (defaults: pee 4h/6h, poo 8h/12h — confirm after field use)
- [ ] Google Sheets existing data: what columns/tabs does the current sheet use? (needed for import script)
- [ ] Meal slots: am/pm only, or more granular (breakfast/lunch/dinner/snack)?
- [ ] Photo storage: store on Mint filesystem (path in DB), or encode in DB?

## Sprint 1 Deployment Checklist Note

Before first test on Windows desktop/browser: add `mint.local` static entry to
`C:\Windows\System32\drivers\etc\hosts` (requires admin). Windows delays `.local` resolution
by 1–2s per connection by querying regular DNS first. This killed grow's initial response
time until fixed. Do this before the first "why is it so slow?" moment.
