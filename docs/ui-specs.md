# Doglog — UI Specs (Confirmed Renderings)

Confirmed ASCII layouts per sprint. These are the locked designs — discarded drafts are not
included. The project plan (`docs/project-plan.md`) is the spec source of truth; this file
is the visual companion.

---

## Sprint 7 — Meal Config (Desktop)

### Page layout

```
Meal Config
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[+ Add]  [Edit]  [Delete]  [Refresh]

  Tess
  ┌───────────────┬──────────────────────┬──────────┬────────────┐
  │ Slot          │ Food                 │ Amount   │ Eff. Date  │
  ├───────────────┼──────────────────────┼──────────┼────────────┤
  │ Breakfast     │ Orijen Senior        │ 1.5 cups │ 2026-01-15 │ ← current
  │               │ Orijen Original      │ 1.5 cups │ 2025-06-01 │ ← history (grey/italic)
  ├───────────────┼──────────────────────┼──────────┼────────────┤
  │ Snack AM      │ Freeze-dried chicken │ 3 pieces │ 2026-03-01 │
  ├───────────────┼──────────────────────┼──────────┼────────────┤
  │ Lunch         │ —                    │          │            │ ← not configured
  ├───────────────┼──────────────────────┼──────────┼────────────┤
  │ Dinner        │ Orijen Senior        │ 1.5 cups │ 2026-01-15 │
  ├───────────────┼──────────────────────┼──────────┼────────────┤
  │ Snack PM      │ Dental chew          │ 1 piece  │ 2025-09-01 │
  └───────────────┴──────────────────────┴──────────┴────────────┘

  Pickles
  ┌───────────────┬──────────────────────┬──────────┬────────────┐
  │ Slot          │ Food                 │ Amount   │ Eff. Date  │
  ├───────────────┼──────────────────────┼──────────┼────────────┤
  │ Lunch         │ Kibble               │ 1/2 cup  │ 2026-05-01 │
  │               │ Boiled rice          │ 2 TBL    │            │
  │               │ Boiled chicken       │ 2 oz     │            │
  │               │ Bone broth           │ to top   │            │
  ├───────────────┼──────────────────────┼──────────┼────────────┤
  │ ...           │                      │          │            │
  └───────────────┴──────────────────────┴──────────┴────────────┘
```

**Layout notes:**
- One QTableWidget per dog inside a QScrollArea > QVBoxLayout
- History rows inline below current row — grey background, italic text
- Slots with no config show — in Food column
- Slot order follows meal_slots.ini
- Delete current record promotes previous history row to current

### Add/Edit dialog

```
┌─────────────────────────────────────────────────┐
│  Add Meal Config                                 │
├─────────────────────────────────────────────────┤
│  Dog          [Pickles          ▾]               │
│  Slot         [Lunch            ▾]               │
│  Eff. Date    [✓] [2026-05-01      ]             │
├─────────────────────────────────────────────────┤
│  Ingredients                                     │
│  ┌─────────────────────┬──────────┬───┬───┬───┐ │
│  │ Food                │ Amount   │ ▲ │ ▼ │ X │ │
│  ├─────────────────────┼──────────┼───┼───┼───┤ │
│  │ Kibble              │ 1/2 cup  │ ▲ │ ▼ │ X │ │
│  │ Boiled rice         │ 2 TBL    │ ▲ │ ▼ │ X │ │
│  │ Boiled chicken      │ 2 oz     │ ▲ │ ▼ │ X │ │
│  │ Bone broth          │ to top   │ ▲ │ ▼ │ X │ │
│  └─────────────────────┴──────────┴───┴───┴───┘ │
│  [+ Add Ingredient]                              │
├─────────────────────────────────────────────────┤
│                          [Cancel]  [Save]        │
└─────────────────────────────────────────────────┘
```

**Dialog notes:**
- Food and Amount cells are directly editable in-place
- [+ Add Ingredient] pops a pick list from meal_ingredients.ini, filtered to exclude already-added items
- In Edit mode: title = "Edit Meal Config"; Dog and Slot dropdowns are read-only
- Save creates/updates meal_configs record and replaces all meal_config_items in one transaction

---

## Sprint 7 — Medications Config (Desktop)

### Page layout

```
Medications Config
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[+ Add]  [Edit]  [Delete]  [Refresh]

  Pickles — Active
  ┌────────────────┬──────────┬──────────┬────────────┬────────────┐
  │ Medication     │ Dose     │ Amount   │ Start      │ End        │
  ├────────────────┼──────────┼──────────┼────────────┼────────────┤
  │ Sucralfate     │ AM       │ 1000mg   │ 2026-03-15 │            │
  │                │ PM       │ 500mg    │            │            │
  ├────────────────┼──────────┼──────────┼────────────┼────────────┤
  │ Heartgard      │ Monthly  │ 68mcg    │ 2025-04-01 │            │
  └────────────────┴──────────┴──────────┴────────────┴────────────┘

  Pickles — Past
  ┌────────────────┬──────────┬──────────┬────────────┬────────────┐
  │ Medication     │ Dose     │ Amount   │ Start      │ End        │
  ├────────────────┼──────────┼──────────┼────────────┼────────────┤
  │ Metronidazole  │ 2x/day   │ 250mg    │ 2026-04-04 │ 2026-04-11 │ ← grey/italic
  └────────────────┴──────────┴──────────┴────────────┴────────────┘

  Tess — Active
  ┌────────────────┬──────────┬──────────┬────────────┬────────────┐
  │ ...            │          │          │            │            │
  └────────────────┴──────────┴──────────┴────────────┴────────────┘
```

**Layout notes:**
- Shared page, both dogs visible; no dog selector
- Per-dog section split into Active / Past subsections
- Past rows grey/italic; active/past derived from end_date vs. today
- Medication name picked from medication_names.ini

### Add/Edit dialog

```
┌─────────────────────────────────────────────────┐
│  Add Medication                                  │
├─────────────────────────────────────────────────┤
│  Dog          [Pickles          ▾]               │
│  Medication   [Sucralfate       ▾]  ← from ini  │
│  Start        [✓] [2026-03-15      ]             │
│  End          [ ] [                ]  ← optional │
├─────────────────────────────────────────────────┤
│  Doses                                           │
│  ┌──────────────────┬──────────┬───┬───┬───┐    │
│  │ Label            │ Amount   │ ▲ │ ▼ │ X │    │
│  ├──────────────────┼──────────┼───┼───┼───┤    │
│  │ AM               │ 1000mg   │ ▲ │ ▼ │ X │    │
│  │ PM               │ 500mg    │ ▲ │ ▼ │ X │    │
│  └──────────────────┴──────────┴───┴───┴───┘    │
│  [+ Add Dose]  ← free text, not a pick list      │
├─────────────────────────────────────────────────┤
│                          [Cancel]  [Save]        │
└─────────────────────────────────────────────────┘
```

**Dialog notes:**
- In Edit mode: Dog and Medication name are read-only
- Label and Amount are free text (dose timing/amounts too varied to standardize)
- [+ Add Dose] appends a blank row; in-place cell editing

---

## Sprint 5a — Mobile Diary Tab

### Diary tab

```
[≡]  Dog Log                        [●]
──────────────────────────────────────
[Tess] [Pickles]    [All types  ▾]   ← inline select, not bottom sheet
──────────────────────────────────────
  May 28  [Pickles]  Vet
  Annual checkup, weight 24.2 lbs

  May 25  [Tess]  Travel
  Weekend trip to the lake  View post →

  May 20  [Pickles]  Life
  First time at the dog park

  ...

──────────────────────────────────────
                              [+ Add]
──────────────────────────────────────
[ Walk ]  [ Meals ]  [Health]  [Diary]
```

**Layout notes:**
- Type filter shows labels (Life / Travel / Vet / Train / Experience), not keys
- Row tap → edit sheet pre-filled; swipe left → delete with confirmation
- Diary is last tab — right swipe navigates back to Health (extends Sprint 4c swipe nav)
- Dog chips multi-select, same style as Health filter bar

### Add/Edit sheet

```
┌───────────────────────────────────┐
│  Edit Diary Entry                 │
├───────────────────────────────────┤
│  Date    [✓] [2026-05-29     ]    │
│  Dog     [Pickles            ▾]   │
│  Type    [Vet                ▾]   │  ← labels: Life/Travel/Vet/Train/Experience
│  Weight  [✓] [24.2       lbs ]    │
│                                   │
│  Notes                            │
│  ┌─────────────────────────────┐  │
│  │ Annual checkup              │  │
│  └─────────────────────────────┘  │
│                                   │
│  Link (optional)                  │
│  ┌─────────────────────────────┐  │
│  │ https://...                 │  │
│  └─────────────────────────────┘  │
├───────────────────────────────────┤
│                [Cancel]  [Save]   │
└───────────────────────────────────┘
```

**Dialog notes:**
- Weight field enabled/disabled via checkbox; unchecked = no weight stored
- Link field is optional free text; if value starts with http, row renders "View post →"
- Date defaults to today; always shown (diary entries always have a date)

---

## Sprint 5 — Medications Mobile (Meals Tab)

### Meals tab with Medications row

```
← Mon May 25 →

  Pickles
  ┌──────────────────────────────────────────┐
  │ Breakfast      —                         │
  │ Snack AM       ████████████████  100%    │
  │ Lunch          ████████████████  100%    │
  │ Dinner         ████████████████  100%    │
  │ Snack PM       —                         │
  │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
  │░ Medications              2 of 3 given ░│  ← shaded, tappable
  └──────────────────────────────────────────┘

  Tess
  ┌──────────────────────────────────────────┐
  │ Breakfast      ████████████████  100%    │
  │ ...                                      │
  │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
  │░ Medications                Not logged ░│
  └──────────────────────────────────────────┘
```

### Dose sheet (slide-up on tap)

```
┌──────────────────────────────────┐
│  Pickles — Medications           │
│  Mon May 25                      │
├──────────────────────────────────┤
│  Sucralfate                      │
│    [ ] AM     1000mg             │
│    [ ] PM     500mg              │
│                                  │
│  Heartgard                       │
│    [ ] Monthly   68mcg           │
├──────────────────────────────────┤
│               [Cancel]  [Save]   │
└──────────────────────────────────┘
```

**Behavior notes:**
- Medications row status: "X of Y given" / "Not logged" / "✓ All given"
- Y = total dose entries across all active medications for that dog
- Sheet loads saved state for today; unchecked only if no log exists yet
- Save upserts one medication_logs record per medication (dog_id, medication_id, log_date DATE, doses_given JSON array of given labels)
- Only active medications shown (end_date null or future)
- Non-daily meds (e.g. Heartgard Monthly) always shown — no due-date logic
- Offline: medicationQueue + Dexie medicationLogs; queue badge includes med queue
