# Sprint 9 — Historical Import Working Doc

This is a planning document for the Sprint 9 discussion, not a spec. Its purpose is to
capture what we already know so the sprint can start with design decisions rather than
rediscovering context.

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

## Open questions (answer at sprint start)

### 1. Input format for meals

Three options — pick one before building the script:

**A. One row per meal (manual authoring)**
CSV/xlsx with columns: `date, dog, slot, percent_consumed`. Author manually or from memory.
Pros: simple script, flexible. Cons: 5 months × 2 dogs × 5 slots = ~1,500 rows to author.

**B. Bulk fill with defaults + exceptions**
Assume 100% consumed for all logged slots, only record exceptions (skips, partial). Much
less to author — typical days are all 100%.
Pros: fast to produce. Cons: script is slightly more complex (merge defaults + exceptions).

**C. Direct from existing records**
If the legacy Google Sheet already has per-meal % columns, extract directly.
Pros: accurate. Cons: depends on sheet format — confirm column layout.

**Question for the user:** What does the source data actually look like? Do you have a
sheet export to look at, or is this from memory?

### 2. Google Sheets column layout

From a prior session, the April sheet had these columns (needs confirmation for all months):
- `Bfast`, `Lunch`, `Dinner`, `9p snack` → map to meal slots
- `No Vomit` / `Vomit` → health events
- `Outcomes` → diary entries (free text)
- `Notes` column — contains medication notes (e.g. "Sucralfate") → TBD: diary or medication table?
- `Diet` column — unclear; confirm what it encodes

Confirm whether this layout is consistent Jan–May, or if earlier months differ.

### 3. The "9p snack" slot

Does `9p snack` map to the existing `snack_pm` slot key, or is it a distinct fifth slot?
Check `meal_slots.ini` — if `snack_pm` = "Snack PM" is the right label, confirm the mapping.

### 4. Notes / medication column

The `Notes` column apparently contains text like "Sucralfate" on dosing days. Decide:
- Import as diary entries (one per day, raw text)?
- Parse and create `medication_logs` records?
- Both?

---

## Proposed script design (strawman)

```
scripts/import_history.py

Inputs:
  --file     path to exported CSV/xlsx
  --dog      "Tess" or "Pickles" (or "all")
  --dry-run  print what would be imported without writing

Logic:
  1. Load meal configs from DB (build date-range lookup per dog+slot)
  2. Parse input file row by row
  3. For each (date, dog, slot, pct):
       - Look up active config for that dog+slot on that date
       - If no config → skip
       - Build ingredients snapshot from config items (all checked = True)
       - Upsert meal_log record
  4. Report: N records created, M slots skipped (no config), K already existed
```

The script runs locally against the dev DB first, verified visually in the app, then
re-run against prod (or DB is copied to prod after verification).

---

## Sprint 9 dependencies

- Sprint 5 complete (meal_logs, medication_logs, meal_configs all in prod) ✓
- DELETE endpoint for meal_logs (to purge dummy records)
- User exports Google Sheets data and provides the file
- User confirms column layout and input format before script is built
