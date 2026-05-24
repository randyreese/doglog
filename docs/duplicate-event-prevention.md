# Duplicate Event Prevention — Idempotent POST

## What this is

A server-side guard that prevents the same pee/poo event from being recorded twice, even if the client sends the same POST request more than once. The mechanism is a UNIQUE database constraint combined with conflict-safe handling in the API endpoint.

## Why it exists

The Walk tab logs events offline during walks and flushes them to the server when WiFi reconnects (`flushQueue()` in `sync.js`). The flush loop posts each queued event and then deletes it from the local queue. If anything interrupts that sequence — a page reload mid-flush, a slow network response, a browser crash — the delete never runs. The entry stays in the queue. On the next sync, the same event gets posted again.

The server had no protection against this. Two identical POSTs created two database rows. The duplicates showed up in the Walk tab history and inflated the poo-count-today in the status strip.

The same race can happen on a direct (non-queued) POST: if the server processes the request but the 4-second `AbortController` timeout fires before the response arrives, the client falls through to `queueEvent()`. The server already created the event; the queue creates a second one later.

## How it works

**Database layer** — `pee_poo_events` has a UNIQUE constraint on `(dog_id, type, timestamp)` (added in migration `0002_unique_event_constraint.py`). SQLite enforces this at write time.

**Migration** — Before adding the constraint, the migration deletes any existing duplicates, keeping the row with the lowest id for each `(dog_id, type, timestamp)` group:

```sql
DELETE FROM pee_poo_events
WHERE id NOT IN (
  SELECT MIN(id) FROM pee_poo_events GROUP BY dog_id, type, timestamp
)
```

This ran automatically on the first container restart after deploy and cleaned up the historical dupes.

**API endpoint** — `POST /doglog/events/` (`routers/events.py`) catches `IntegrityError` and returns the existing event instead of raising a 500:

```python
ts = body.timestamp or datetime.now()
event = PeePooEvent(dog_id=body.dog_id, type=body.type, timestamp=ts)
db.add(event)
try:
    db.commit()
    db.refresh(event)
    return event
except IntegrityError:
    db.rollback()
    return db.query(PeePooEvent).filter(...timestamp == ts).first()
```

The POST is idempotent: send it once, get a 201 with the new event. Send it again with the same `(dog_id, type, timestamp)`, get a 201 with the existing event. No duplicate is created.

**Client side** — `flushQueue()` uses a plain `fetch()` that doesn't throw on 4xx/5xx responses. Even if the server somehow returned an error status, the queue entry would still be deleted (the delete runs unconditionally after `fetch` resolves). In practice the server now always returns 201, so the client never needs special handling.

## Edge case: same dog, same type, same second

If you tap Log twice within the same second for the same dog and event type, the second tap is silently discarded — the server returns the first event. In normal use this can't happen: the timestamp has second precision and the Log button disables itself (`logging` state) while the first request is in flight.

## Key files

| File | Role |
|---|---|
| `backend/models.py` | `UniqueConstraint('dog_id', 'type', 'timestamp')` on `PeePooEvent` |
| `backend/alembic/versions/0002_unique_event_constraint.py` | Migration: dedup + add constraint |
| `backend/routers/events.py` | `log_event` — catches `IntegrityError`, returns existing event |
| `mobile/src/sync.js` | `flushQueue()` — posts queue entries; delete runs regardless of response status |
