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
- One-handed right-handed operation — all active controls on right side
- Hamburger menu (top-left) for infrequent actions only
- Bottom tab bar for tab navigation (right thumb reach)
- Carousel pattern repeats consistently across all three tabs

**Three tabs:**

**Walk tab (primary):**
```
[≡]                    [Status ▾]   ← collapsible strip, tap to expand
────────────────────────────────
[ ←  Tess  → ]              [>]    ← dog carousel, right button advances
[ ←  Pee   → ]              [>]    ← event carousel
                          [LOG]    ← right-aligned
────────────────────────────────
10:30a  Tess: Poo            [ ]   ← history rows
10:15a  Tess: Pee            [ ]
...                    [Delete]    ← appears when any checkbox checked
```
Status strip (collapsed): one-line summary per dog  
Status strip (expanded): full matrix — last pee time (Tess only) + last poo time + count-today per dog, color-coded green/yellow/red, resets midnight

**Adverse tab:**
- Same dog carousel [>]
- Event type carousel: Vomit / Diarrhea / Other [>]
- Camera button
- [LOG] right-aligned
- History rows with checkbox-to-delete pattern

**Meals tab:**
- Same dog carousel [>]
- Meal slot carousel: AM / PM [>]
- % consumed (TBD: slider or stepped carousel 0/25/50/75/100)
- [LOG] right-aligned
- History rows with checkbox-to-delete pattern

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

*(none yet)*

---

## Current Sprint

**Sprint 1 — Foundation**

Goal: Replace `index.html` with a real persisted mobile app. Dogs configurable, pee/poo
logging works end-to-end, data survives app close.

Design decisions to resolve before building:
- [ ] Confirm grow PWA scaffold branch/commit to copy from
- [ ] API shape for pee_poo_events (POST body, response)
- [ ] Status matrix color thresholds — defaults to use before config screen exists

Stories:
- [ ] Backend: FastAPI scaffold + Docker compose on Mint
- [ ] Backend: `dogs` table + CRUD endpoints
- [ ] Backend: `pee_poo_events` table + POST/GET endpoints
- [ ] Backend: `/api/status` endpoint (returns status matrix data)
- [ ] Mobile: copy grow PWA scaffold, strip grow-specific UI
- [ ] Mobile: dog selector component (from API, not hardcoded)
- [ ] Mobile: Pee/Poo entry buttons → POST to backend
- [ ] Mobile: status matrix component (reads `/api/status`)
- [ ] Mobile: WiFi-gate sync (Network Information API, Android/Chrome)
- [ ] Mobile: offline queue → sync on WiFi connect
- [ ] Dev/Prod: `start_dev.bat`, `deploy_to_prod.bat`
- [ ] QR code LAN discovery (reuse grow pattern)

---

## Backlog

1. **Sprint 2 — Mobile history & daily summary**
   7-day pee/poo history view, daily summary screen, midnight reset for status matrix.
   Depends on: Sprint 1

2. **Sprint 3 — Other events + camera**
   Vomit/diarrhea/other event logging with camera capture, photo storage on backend.
   Depends on: Sprint 1

3. **Sprint 4 — Food consumption**
   Meal logging (% consumed per slot), meal config API, food screen in PWA.
   Depends on: Sprint 1

4. **Sprint 5 — Medications**
   Medication schedule, dose logging, medications screen in PWA.
   Depends on: Sprint 1

5. **Sprint 6 — Desktop scaffold + milestones**
   PySide6 desktop app, dog milestones (vet visits, weight log, notable trips).
   Depends on: Sprint 1 (shared backend)

6. **Sprint 7 — Desktop: dog config + meal composition**
   Dog add/edit/archive, meal config with dated versions.
   Depends on: Sprint 6

7. **Sprint 8 — Desktop: dry food inventory**
   Dry food purchase log, consumption pattern, reorder schedule display.
   Depends on: Sprint 6

8. **Sprint 9 — Google Sheets import**
   One-time migration script: read existing Google Sheet, map to data model, import to SQLite.
   Depends on: Sprints 1–5 (full data model in place)

9. **Sprint 10 — Google Sheets daily export**
   Daily export job: write to current month tab in new sheet format. Summary tab.
   Depends on: Sprint 9 (sheet format established)

10. **Stretch — Raspberry Pi fridge display**
    Pi Zero W + small display polling `/api/status`, renders status matrix on the fridge.
    Depends on: Sprint 1 (`/api/status` endpoint)

---

## Open Questions

- [ ] Grow PWA scaffold: which branch/commit is the cleanest reuse base?
- [ ] Status matrix color thresholds: what elapsed times trigger yellow/red per event type?
- [ ] Google Sheets existing data: what columns/tabs does the current sheet use? (needed for import script)
- [ ] Meal slots: am/pm only, or more granular (breakfast/lunch/dinner/snack)?
- [ ] Photo storage: store on Mint filesystem (path in DB), or encode in DB?

## Sprint 1 Deployment Checklist Note

Before first test on Windows desktop/browser: add `mint.local` static entry to
`C:\Windows\System32\drivers\etc\hosts` (requires admin). Windows delays `.local` resolution
by 1–2s per connection by querying regular DNS first. This killed grow's initial response
time until fixed. Do this before the first "why is it so slow?" moment.
