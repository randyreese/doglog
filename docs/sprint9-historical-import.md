# Sprint 9 — Historical Import Working Doc

This is a planning document for the Sprint 9 discussion, not a spec. Its purpose is to
capture what we already know so the sprint can start with design decisions rather than
rediscovering context.

---

## Why this matters

Pickles had a significant health crisis in late March 2026. He visited the vet on 3/24 —
eating issues were discussed but assessed as non-critical. A few days later he crashed badly.
The owner scrambled to change his diet (effective 4/1) and has been trying to identify root
causes: stress, activities, food composition, vomiting frequency.

The next vet appointment is **July 2026** (~30 days away). The goal of Sprint 9 + Sprint 10
is to produce a polished, impactful vet report covering the full Jan–present timeline —
particularly the March crisis window and the diet transition. The vet needs to see:

- What Pickles was eating (and refusing) day by day
- When vomiting occurred and how frequently
- What changed on 4/1 and how eating improved afterward
- Activities and stress events correlated with symptoms

This context explains several decisions:

- **Retroactive health logging ships in Sprint 9**, not later — the owner needs to manually
  enter Stomach Gurgles, Dry Heaves, Grass Eating events for late March before the vet visit
- **Vomit events from the sheet are imported** — they're clinical data, not noise
- **The vet report (Sprint 10) is the primary deliverable**, not just a nice-to-have
- **The 4/1 effective_date on meal configs** is load-bearing — the report must clearly show
  pre- and post-diet-change eating patterns

---

## What we're importing

Meal history for Tess and Pickles from **January 1, 2026 through May 31, 2026** (inclusive).
Source: user-exported Google Sheets data (CSV or xlsx) — legacy sheet maintained through 5/31.

**Hard boundary:** June 1, 2026 is go-live. All prod data from 6/1 forward is recorded live
in the app and must not be touched by the import script. The import covers 1/1–5/31 only,
with no overlap.

Goal: populate `meal_logs` with accurate per-dog-per-slot-per-day records so the **Vet Report
(Sprint 10)** reflects real eating history — particularly Pickles' diet change on 4/1/2026.

---

## What we already know

### Meal configs are already in the DB with effective dates

The desktop Meal Config page was used to enter dated configs for both dogs before go-live.
The import script does **not** need hardcoded ingredient definitions — it can query the DB:

```
For each (dog, slot, date):
  Find the meal_config with the latest effective_date ≤ date
  Use that config's items as the ingredient snapshot for the meal_log record
```

This means the ingredient snapshots in historical records will automatically reflect the
correct diet for each date range.

### Pickles' config history (already in DB)

| Slot | Effective date | Foods |
|---|---|---|
| Breakfast | 2026-01-01 | Purina One Chicken & Duck, EN Gastroenteric, Turkey & Rice |
| Breakfast | 2026-04-01 | Chicken Boiled, Rice White Boiled, Bone Broth |
| AM Snack | 2026-02-15 | Peanut Butter |
| Lunch | 2026-01-01 | EN Gastroenteric, Turkey & Rice |
| Lunch | 2026-04-01 | Chicken Boiled, Rice White Boiled, EN Gastroenteric, Bone Broth |
| Dinner | 2026-01-01 | EN Gastroenteric, Turkey & Rice |
| Dinner | 2026-04-01 | Chicken Boiled, Rice White Boiled, EN Gastroenteric, Bone Broth |
| PM Snack | 2026-01-01 | EN Gastroenteric, Turkey & Rice |
| PM Snack | 2026-04-01 | Chicken Boiled, Rice White Boiled, Bone Broth |

**No AM Snack config before 2026-02-15** — the "no config = no record" rule means January
AM Snack rows will simply not be imported. This is correct.

### Tess's config (already in DB)

One config per slot, effective 2026-01-01 throughout (no diet change):
- Breakfast: Turkey & Rice, Canned Pumpkin
- AM Snack (2026-02-15): Peanut Butter, Yogurt
- Lunch/Dinner/PM Snack: Turkey & Rice

### Rule: no config found = no record

If no config exists for a dog+slot on a given date, skip that slot entirely. Do not create
a record with an empty ingredient list.

### Dummy records need to be purged first

There are ~3 test `meal_log` records in prod from the dev testing period (May dates). These
must be deleted before importing real history, or they'll appear in the vet report.

**Pre-requisite:** Add a `DELETE /meal-logs/{id}` endpoint (or a bulk delete endpoint) to
the backend before Sprint 9 starts. This can be a one-off server-side script or a proper
endpoint depending on preference.

---

## Decisions made (session 2026-06-01)

### Source data format confirmed

The legacy sheet has two rows per date (one per dog). Meal columns: `Bfast / Lunch / Dinner /
9p snack`. Columns D (Diet), I (Outcomes), and M (Activities) shift in heading and purpose
month to month — script must detect columns by header name, not position.

### AM Snack — default 100%

AM Snack (lick mats) has no dedicated column in the source. Both dogs default to 100% for all
days where a config exists (Tess from 2/15, Pickles from 2/15). Pickles' occasional misses
are noted in Outcomes free text but not worth parsing — the lick mat isn't the clinical focus.

### Input format — Option C (direct from sheet)

Meal % values come directly from the sheet columns. Values are mostly 0 or 100 with occasional
partials (25, 50, 70, 80). No manual authoring needed.

### Health events — Vomit import + retroactive logging

- Import V=x rows as `health_events` type="vomit" for the sheet date. Script handles this
  directly — no UI needed.
- Add **log-with-past-date** to the mobile Health tab: a toggle/checkbox that reveals a date
  picker before logging, so the owner can retroactively enter Stomach Gurgles, Dry Heaves,
  Grass Eating, etc. for specific dates. This ships in Sprint 9.
- Backend: `PATCH /health-events/{id}` does NOT need to be extended — new records with past
  dates are created via POST; existing records don't need date/type edits.

### Outcomes and Activities columns — not imported

Too varied and free-form across months for reliable structured import. The retroactive
log-with-past-date feature covers manual entry of the most clinically significant events.

### Diet column (D) — ignored

Already captured by meal configs in the DB with effective_date. No import needed.

### Streak column — ignored

Calculated field, not source data.

---

## Column map — confirmed (session 2026-06-01)

All five 2026 tabs share the same core structure. Two rows per date (Pickles row, Tess row).

| Col | Header | Import? | Notes |
| --- | ------ | ------- | ----- |
| B | Start 7am | Yes — date | Excel date serial; pandas reads as datetime automatically. First day of month is hardcoded, subsequent days are `=B_prev+1` formulas — openpyxl reads cached values, no manual conversion needed. |
| C | Pup | Yes — dog name | "Tess" or "Pickles" |
| D | Diet | No | Shorthand label (e.g. "Rx/PP + brk top"); redundant with meal configs in DB. Blank for Pickles Apr–May. |
| E | Bfast | Yes | Integer %, maps to `breakfast` slot |
| F | Lunch | Yes | Integer %, maps to `lunch` slot |
| G | Dinner | Yes | Integer %, maps to `dinner` slot |
| H | 9p snack | Yes | Integer %, maps to `snack_pm` slot |
| I | Outcomes | No | Free-form clinical notes; too varied to parse reliably |
| K | NoV | No | "No vomit today" checkbox; inverse of what we need |
| L | V | Yes — health event | "x" → create `health_events` record, type="vomit", for that date |
| M | varies | Conditional | Jan–Feb: "7a tomorrow" (sleep metric) → ignore. Mar: "Activities" → user enters manually via desktop Diary. Apr–May: "Notes" (Sucralfate dosing) → parse into `medication_logs` |
| N | Streak | No | Calculated field |

### AM Snack (lick mat) — no column in source

Synthesized by the script: 100% for all dates where a config exists (both dogs from 2/15).
No exceptions tracked — Pickles' occasional misses are in Outcomes free text, not worth parsing.

### Sucralfate Notes parsing (Apr–May only)

Column M header = "Notes". Values observed:

- `"Sucralfate am"` → morning dose given
- `"Sucralfate am, pm"` → both doses given
- `"Sucralfate 1000mg am, 500mg pm"` → both doses, dose detail in text
- `"no Sucralfate"` → no doses given (skip — don't create a record)
- blank → no entry (Tess rows are always blank here)

Parse logic: if "am" in value → include dose 1; if "pm" in value → include dose 2.
Look up Sucralfate medication_id and dose IDs from DB at script start (don't hardcode).
Create `medication_logs` record with `doses_given` JSON array matching the dose IDs found.
Only applies to Pickles rows — Tess has no Sucralfate.

---

## Script design — final

```
scripts/import_history.py

Inputs:
  --file      path to Sprint9input.xlsx
  --tabs      comma-separated tab names, default "Jan,Feb,Mar,Apr,May"
  --dog       "Tess" or "Pickles" or "all" (default: all)
  --dry-run   print what would be imported without writing

Startup:
  1. Load meal configs from DB → date-range lookup per (dog, slot)
  2. Load Sucralfate medication from DB → medication_id, dose_id list (am=dose[0], pm=dose[1])
  3. Purge check: assert no existing meal_logs in 1/1–5/31 range (or --force to skip)

Per tab:
  4. Read tab with pandas (engine="openpyxl"), detect column M header by name
  5. Skip header rows (row 4 is header; rows 1–3 are summary stats)
  6. For each data row:
       a. Parse date (col B), dog (col C)
       b. For each meal slot (Bfast/Lunch/Dinner/9p snack):
            - Look up config; skip if none
            - Upsert meal_log with pct from cell, ingredient snapshot from config
       c. Synthesize AM Snack: if config exists for (dog, date) → upsert 100%
       d. If col L = "x" → upsert health_event type="vomit" for that date
       e. If col M header = "Notes" and value non-empty and not "no Sucralfate":
            → parse doses, upsert medication_log for that date

Output:
  Meal logs created: N
  AM Snack records created: N
  Slots skipped (no config): N
  Vomit events created: N
  Medication logs created: N
  Already existed (skipped): N
```

The script runs locally against the dev DB first, verified visually in the app, then
the verified DB is copied to prod (or script re-run against prod DB directly).

---

## Sprint 9 dependencies

- Sprint 5 complete (meal_logs, medication_logs, meal_configs all in prod) ✓
- Mobile: log-with-past-date feature on Health tab (ships in Sprint 9)
- Purge 3 dummy test meal_log records before import — direct DB delete (sqlite3 CLI or a
  one-liner in the script startup), not a REST endpoint; upsert would overwrite same-day
  records anyway but this ensures a clean slate regardless
- Confirm `snack_pm` is the correct slot key for "9p snack" (check meal_slots.ini)
- Confirm Sucralfate dose ordering in DB matches "am" = dose[0], "pm" = dose[1]
- Source file at: `D:\$user\dev\Folders\ObsidianVault\doglog\working\Sprint9input.xlsx`
