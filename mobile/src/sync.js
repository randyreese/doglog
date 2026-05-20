import { db } from './db'
import { getBackendUrl } from './api'

const LAST_SYNCED_KEY = 'doglog_last_synced'

export function getLastSynced() {
  return localStorage.getItem(LAST_SYNCED_KEY)
}

// Only attempt network when on WiFi — preserves battery during walks on cellular
function isWifi() {
  const conn = navigator.connection
  if (!conn) return true  // API unavailable (iOS/desktop) — allow through
  return conn.type === 'wifi'
}

export async function ping() {
  if (!isWifi()) return { ok: false, rtt: null }
  const base = getBackendUrl()
  if (!base) return { ok: false, rtt: null }
  const t0 = Date.now()
  try {
    const res = await fetch(`${base}/doglog/health`, { cache: 'no-store' })
    return { ok: res.ok, rtt: Date.now() - t0 }
  } catch {
    return { ok: false, rtt: null }
  }
}

export function signalFromRtt(rtt) {
  if (rtt === null) return 'offline'
  if (rtt < 300) return 'good'
  return 'weak'
}

export async function syncFromBackend() {
  const base = getBackendUrl()
  if (!base) throw new Error('No backend configured')

  const [dogsRes, eventsRes] = await Promise.all([
    fetch(`${base}/doglog/dogs/`, { cache: 'no-store' }),
    fetch(`${base}/doglog/events/?limit=200`, { cache: 'no-store' }),
  ])
  if (!dogsRes.ok || !eventsRes.ok) throw new Error('Sync fetch failed')

  const [dogs, events] = await Promise.all([dogsRes.json(), eventsRes.json()])

  await db.transaction('rw', [db.dogs, db.events, db.meta], async () => {
    await db.dogs.clear()
    await db.events.clear()
    await db.dogs.bulkPut(dogs)
    await db.events.bulkPut(events)
    const ts = new Date().toISOString()
    await db.meta.put({ key: 'last_synced', value: ts })
    localStorage.setItem(LAST_SYNCED_KEY, ts)
  })
}

export async function flushQueue() {
  const base = getBackendUrl()
  if (!base) return

  const entries = await db.eventQueue.toArray()
  for (const entry of entries) {
    try {
      await fetch(`${base}/doglog/events/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dog_id: entry.dog_id, type: entry.type, timestamp: entry.timestamp }),
      })
      await db.eventQueue.delete(entry.id)
    } catch {
      break
    }
  }
}

export async function queueEvent({ dog_id, type, timestamp }) {
  await db.eventQueue.add({
    dog_id,
    type,
    timestamp: timestamp || new Date().toISOString(),
    created_at: new Date().toISOString(),
  })
  // also write to local events table so history shows immediately
  await db.events.add({
    id: Date.now(),  // temp id, replaced on next sync
    dog_id,
    type,
    timestamp: timestamp || new Date().toISOString(),
    _queued: true,
  })
}
