# Desktop Navigation Design Decisions

*Decided: Sprint 6, 2026-05-28*

## The Split: Sidebar vs Settings

**Sidebar** = pages with structured data records, dates, and history. Things you actively use to view and manage over time.

**Settings** = pick lists and app configuration. Things you set up once and rarely touch.

## Sidebar Pages

| Page | Purpose |
|---|---|
| Milestones | Vet visits, weight log, travel, training — dated records per dog |
| Meal Config | Per-dog, per-slot meal composition with effective dates (free-form text) |
| Medications Config | Per-dog medication records with dose schedule, start/end dates, dosage |
| Dry Food Forecast | Purchase log, consumption tracking, reorder schedule |
| Settings | All configuration (see below) |

## Settings Tabs

| Tab | Purpose |
|---|---|
| Dogs | Add/edit/archive dogs (name, birthdate, breed, active, track_pee) |
| Meal Slots | Pick list of meal slot names — drives Meals tab on mobile |
| Meal Ingredients | Pick list of ingredients — drives mobile logging checklist |
| Medications | Pick list of medication names — used in Medications Config sidebar page |
| Health Types | Pick list of health event types — drives mobile Health tab |
| Milestone Types | Pick list of milestone event types (Life/Travel/Vet/Train/Experience) |
| App | Backend URL display + Pull Prod DB |

## Key Design Principles

- **Pick lists belong in Settings.** If it's just a list of names with no dates or per-record attributes, it's a Settings tab.
- **Dated records belong in the sidebar.** Meal Config and Medications Config have start/end dates and versioned history — they're sidebar pages, not Settings tabs.
- **Settings feeds Sidebar.** The Medications pick list (Settings) provides the name options used when building a record in Medications Config (sidebar). Same relationship between Meal Ingredients (Settings) and Meal Config (sidebar).
- **Meal Ingredients is the fallback checklist.** The mobile meal edit sheet uses per-dog-slot items from Meal Config when a config exists; it falls back to the global Meal Ingredients ini list otherwise. Meal Config item descriptions are free-form text — they are not drawn from the Meal Ingredients pick list.
- **Dogs is in Settings** because it's simple config (no dated versions, no history). Dog management is infrequent — set up once.
- **"All" in Milestone dog picker is hardcoded**, not a configurable entry. The dog picker always shows active dogs + "All" appended. No separate Milestone Dogs settings tab needed.
