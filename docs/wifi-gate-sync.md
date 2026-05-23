# WiFi-Gate Sync — How Offline and Battery-Conscious Sync Works

> **Reusable pattern.** This applies to any mobile app used away from home on cellular
> (walk companion, field logging, etc.). The Network Information API code in `sync.js`
> and `SyncContext.jsx` can be copied directly into future projects.

## What this is

The doglog mobile app works without an internet or WiFi connection. You can log events
during a walk (on cellular, away from home) and they sync to the backend automatically
when you return to WiFi. The app never makes network requests while on cellular, which
preserves battery life.

## The problem it solves

The app is used during walks — up to 2 hours of active screen time, away from home WiFi,
on cellular. A naive approach would try to reach the backend every 30 seconds. On cellular,
every network attempt wakes up the radio, and the radio stays awake for 5–20 seconds after
each attempt (this is called "tail time"). A 30-second ping interval keeps the cellular
radio almost continuously spinning and drains the battery noticeably over a 2-hour walk.

The solution: **do nothing on cellular**. Queue events locally, and sync only when WiFi is
detected.

## How it works

### While on a walk (cellular)

When you tap LOG, the app tries to POST the event directly to the backend. If the backend
is unreachable (no WiFi), the event goes into a local queue stored in IndexedDB (via
Dexie.js) on the phone. The event appears in the history immediately — it doesn't wait for
sync. Zero network activity happens.

### When you get home (WiFi detected)

Android Chrome exposes the Network Information API (`navigator.connection`). The app
listens for connection type changes. The moment `connection.type` switches to `'wifi'`,
the app automatically:

1. Flushes the queue — POSTs any queued events to the backend in order
2. Syncs from the backend — pulls the latest dogs and events into local storage

No manual action needed. The sync just happens.

### The periodic ping

Every 30 seconds, the app pings the backend's `/health` endpoint. But only if on WiFi.
On cellular, the ping is skipped entirely. On WiFi, the ping result sets the signal
indicator (green/yellow/red dot in the header) and triggers a sync if connectivity was
just restored.

### iOS / desktop fallback

The Network Information API only exists on Android Chrome. On iOS Safari and desktop
browsers, `navigator.connection` is undefined. In that case, the app allows network
requests through (it can't tell if you're on WiFi), so the 30-second ping runs normally.
This is fine — iOS isn't a target device, and desktop is never on a walk.

## Key files

| File | What it does |
|---|---|
| `mobile/src/sync.js` | `ping()`, `flushQueue()`, `syncFromBackend()`, `queueEvent()` |
| `mobile/src/SyncContext.jsx` | React context; runs the periodic ping, listens for WiFi connect event |
| `mobile/src/db.js` | Dexie schema; `eventQueue` table holds unsynced events |

## Offline log and delete — how the local DB stays in sync

### Logging while offline

When a LOG tap results in a queued event (backend unreachable), `queueEvent()` writes the
event to **two** places simultaneously:

1. `db.eventQueue` — the outbox. Flushed to the server when WiFi returns.
2. `db.events` — the local mirror of server data. This is what the history display reads.

Both writes use the same `localISOString()` timestamp (local time, no UTC offset). This is
critical — if the timestamps differ, the delete logic can't match them (see below).

The event appears in history immediately. The queue badge increments. No network activity.

### Deleting while offline

Deleting a queued event requires cleaning up both tables. `deleteEvent()` in `sync.js` handles this:

- **Queued event** (`_queued: true` flag on the db.events record): removes from both
  `db.eventQueue` (matched by dog_id + timestamp) and `db.events`. No server call needed —
  the event was never synced.
- **Synced event** (already on the server): attempts a server DELETE, then removes from
  `db.events` locally regardless of whether the server call succeeded. If offline, the
  local copy disappears; it will come back on next sync (a known limitation — offline delete
  of already-synced events is best-effort).

After any delete, `refreshQueueCount()` is called to update the badge immediately.

### Key files (updated)

| File | What it does |
|---|---|
| `mobile/src/sync.js` | `ping()`, `flushQueue()`, `syncFromBackend()`, `queueEvent()`, `deleteEvent()` |
| `mobile/src/SyncContext.jsx` | React context; runs the periodic ping, listens for WiFi connect event |
| `mobile/src/db.js` | Dexie schema; `eventQueue` (outbox) + `events` (local mirror) |
| `mobile/src/api.js` | `localGet()` offline fallback — matches `/events/` with `startsWith` to handle query params |

## What the signal dot means

The colored dot in the top-right of the header reflects the last ping result:

- **Green** — backend reachable, RTT < 300ms
- **Yellow** — backend reachable but slow (RTT ≥ 300ms)
- **Red** — backend unreachable (offline, or cellular with WiFi gate blocking the ping)

During a walk, expect red. That's correct behavior — the app is offline by design.
