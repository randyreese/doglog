# Dexie Offline Architecture — Walk/Health vs Meals

## What this is

Doglog uses Dexie (a wrapper around the browser's IndexedDB) as a local offline store so the app
keeps working when the backend is unreachable. But the three main data types — Walk events, Health
events, and Meal logs — use Dexie differently. Walk and Health get a full rolling cache from the
server; Meals do not. Understanding the difference matters when you're debugging why past records
do or don't show up offline.

---

## Walk and Health — full rolling cache

Every time the app syncs with the backend (`syncFromBackend` in `mobile/src/sync.js`), it:

1. Clears `db.events` (walk) and `db.healthEvents` entirely
2. Fetches the latest 200 records from the server for each
3. Writes them into Dexie

This means Dexie always holds a recent snapshot of the server's data for these two types. When the
server is sleeping and the app tries to load walk history or health history, the API call fails and
`api.js` falls back to the local Dexie store. The user sees real historical data — not a queue,
not a workaround — because the last sync populated it.

**Key file:** `mobile/src/api.js` → `localGet()` — the fallback that reads from Dexie when the
server is unreachable.

---

## Meals — queue-only, no cache

`syncFromBackend` does **not** touch `db.mealLogs`. The only way a meal record gets into Dexie is
through `queueMealLog` in `sync.js`, which runs when the server is unreachable at log time:

```
user logs meal offline
  → mealQueue entry added (pending sync)
  → mealLogs entry added with _queued: true
```

When the server comes back and `flushQueue` runs, the `mealQueue` entry is posted to the server and
deleted. But `db.mealLogs` is left untouched — the record with `_queued: true` stays.

**Consequence:** If you browse to a past date while offline, you only see meal entries that were
*originally logged offline*. Meals logged while online went straight to the server; they're not in
Dexie. Those slots show `—`.

---

## The stale queue-dot bug

Because `_queued: true` is never cleared from `db.mealLogs` after a successful sync, Dexie records
from old offline sessions still carry the flag indefinitely. When the server is down and `loadLogs`
falls back to Dexie, those records render with a red queue dot — even though they synced days ago.

**Fix:** In `flushQueue` (sync.js), after `db.mealQueue.delete(entry.id)`, also clear the flag:

```js
await db.mealLogs
  .where({ dog_id: entry.dog_id, slot: entry.slot, meal_date: entry.meal_date })
  .modify(record => { delete record._queued })
```

This is tracked in **GitHub Issue #4**.

---

## Why Meals weren't given a full cache

Walk and health events are time-series records — a fixed fetch of the latest 200 covers everything
relevant. Meal logs are keyed by `(dog_id, slot, meal_date)` and span an open-ended date range.
A full cache would require fetching an unbounded set of dates on every sync, which wasn't
implemented. The practical impact is small: the Meals tab is primarily used for today, and the
date pager back through past dates is a secondary review feature.

If full offline browsing of past meal dates ever becomes important, the fix is to add a meal-log
range fetch to `syncFromBackend` (e.g., last 30 days), writing results to `db.mealLogs` without
`_queued`.

---

## Quick reference

| Data type | Dexie table | Populated by | Offline fallback? |
|---|---|---|---|
| Walk events | `db.events` | `syncFromBackend` (200 records) + `queueEvent` | Yes — full recent history |
| Health events | `db.healthEvents` | `syncFromBackend` (200 records) + `queueHealthEvent` | Yes — full recent history |
| Meal logs | `db.mealLogs` | `queueMealLog` only | Partial — offline-logged records only |
| Pending walks | `db.eventQueue` | `queueEvent` | Flushed on next sync |
| Pending health | `db.healthQueue` | `queueHealthEvent` | Flushed on next sync |
| Pending meals | `db.mealQueue` | `queueMealLog` | Flushed on next sync |
