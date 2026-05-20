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

## What the signal dot means

The colored dot in the top-right of the header reflects the last ping result:

- **Green** — backend reachable, RTT < 300ms
- **Yellow** — backend reachable but slow (RTT ≥ 300ms)
- **Red** — backend unreachable (offline, or cellular with WiFi gate blocking the ping)

During a walk, expect red. That's correct behavior — the app is offline by design.
