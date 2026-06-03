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

  const [dogsRes, eventsRes, healthRes, milestonesRes] = await Promise.all([
    fetch(`${base}/doglog/dogs/`, { cache: 'no-store' }),
    fetch(`${base}/doglog/events/?limit=200`, { cache: 'no-store' }),
    fetch(`${base}/doglog/health-events/?limit=200`, { cache: 'no-store' }),
    fetch(`${base}/doglog/milestones/`, { cache: 'no-store' }),
  ])
  if (!dogsRes.ok || !eventsRes.ok || !healthRes.ok || !milestonesRes.ok) throw new Error('Sync fetch failed')

  const [dogs, events, healthEvents, milestones] = await Promise.all([
    dogsRes.json(), eventsRes.json(), healthRes.json(), milestonesRes.json(),
  ])

  await db.transaction('rw', [db.dogs, db.events, db.meta, db.healthEvents, db.diaryEntries], async () => {
    await db.dogs.clear()
    await db.events.clear()
    await db.healthEvents.clear()
    await db.diaryEntries.clear()
    await db.dogs.bulkPut(dogs)
    await db.events.bulkPut(events)
    await db.healthEvents.bulkPut(healthEvents)
    await db.diaryEntries.bulkPut(milestones)
    const ts = new Date().toISOString()
    await db.meta.put({ key: 'last_synced', value: ts })
    localStorage.setItem(LAST_SYNCED_KEY, ts)
  })
}

export async function flushQueue() {
  const base = getBackendUrl()
  if (!base) return

  // Flush pee/poo queue
  const entries = await db.eventQueue.toArray()
  for (const entry of entries) {
    try {
      const res = await fetch(`${base}/doglog/events/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dog_id: entry.dog_id, type: entry.type, timestamp: entry.timestamp }),
      })
      if (!res.ok) break
      await db.eventQueue.delete(entry.id)
    } catch {
      break
    }
  }

  // Flush health queue
  const healthEntries = await db.healthQueue.toArray()
  for (const entry of healthEntries) {
    try {
      const res = await fetch(`${base}/doglog/health-events/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dog_id: entry.dog_id,
          type: entry.type,
          timestamp: entry.timestamp,
          notes: entry.notes,
          photo: entry.photo,
        }),
      })
      if (!res.ok) break
      await db.healthQueue.delete(entry.id)
    } catch {
      break
    }
  }

  // Flush meal queue
  const mealEntries = await db.mealQueue.toArray()
  for (const entry of mealEntries) {
    try {
      const res = await fetch(`${base}/doglog/meal-logs/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dog_id: entry.dog_id,
          slot: entry.slot,
          meal_date: entry.meal_date,
          percent_consumed: entry.percent_consumed,
          notes: entry.notes,
          ingredients: entry.ingredients,
        }),
      })
      if (!res.ok) break
      await db.mealQueue.delete(entry.id)
      await db.mealLogs
        .where({ dog_id: entry.dog_id, slot: entry.slot, meal_date: entry.meal_date })
        .modify(record => { delete record._queued })
    } catch {
      break
    }
  }

  // Flush medication queue
  const medEntries = await db.medicationQueue.toArray()
  for (const entry of medEntries) {
    try {
      const res = await fetch(`${base}/doglog/medication-logs/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dog_id: entry.dog_id,
          medication_id: entry.medication_id,
          log_date: entry.log_date,
          doses_given: entry.doses_given,
        }),
      })
      if (!res.ok) break
      await db.medicationQueue.delete(entry.id)
      await db.medicationLogs
        .where({ dog_id: entry.dog_id, medication_id: entry.medication_id, log_date: entry.log_date })
        .modify(record => { delete record._queued })
    } catch {
      break
    }
  }

  // Flush diary queue
  const diaryEntriesToFlush = await db.diaryQueue.toArray()
  for (const entry of diaryEntriesToFlush) {
    try {
      const res = await fetch(`${base}/doglog/milestones/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dog_id: entry.dog_id || null,
          date: entry.date,
          event_type: entry.event_type,
          notes1: entry.notes1 || null,
          notes2: entry.notes2 || null,
          weight_lbs: entry.weight_lbs || null,
        }),
      })
      if (!res.ok) break
      await db.diaryQueue.delete(entry.id)
    } catch {
      break
    }
  }
}

export function localISOString(d = new Date()) {
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

export async function deleteEvent(id) {
  const local = await db.events.get(id)
  if (local?._queued) {
    await db.eventQueue.where({ dog_id: local.dog_id, timestamp: local.timestamp }).delete()
  } else {
    try {
      const { api } = await import('./api')
      await api.delete(`/events/${id}`)
    } catch { /* offline — server delete skipped, local still removed */ }
  }
  await db.events.delete(id)
}

export async function queueEvent({ dog_id, type, timestamp }) {
  const ts = timestamp || localISOString()
  await db.eventQueue.add({
    dog_id,
    type,
    timestamp: ts,
    created_at: localISOString(),
  })
  await db.events.add({
    id: Date.now(),
    dog_id,
    type,
    timestamp: ts,
    _queued: true,
  })
}

export async function queueHealthEvent({ dog_id, type, timestamp, notes, photo }) {
  const ts = timestamp || localISOString()
  await db.healthQueue.add({
    dog_id,
    type,
    timestamp: ts,
    notes: notes || null,
    photo: photo || null,
    created_at: localISOString(),
  })
  await db.healthEvents.add({
    id: Date.now(),
    dog_id,
    type,
    timestamp: ts,
    notes: notes || null,
    photo: photo || null,
    _queued: true,
  })
}

export async function queueMealLog({ dog_id, slot, meal_date, percent_consumed, notes, ingredients }) {
  await db.mealQueue.add({ dog_id, slot, meal_date, percent_consumed, notes, ingredients, created_at: localISOString() })
  await db.mealLogs.put({ dog_id, slot, meal_date, percent_consumed, notes, ingredients, _queued: true })
}

export async function queueMedicationLog({ dog_id, medication_id, log_date, doses_given }) {
  await db.medicationQueue.add({ dog_id, medication_id, log_date, doses_given, created_at: localISOString() })
  await db.medicationLogs.put({ dog_id, medication_id, log_date, doses_given, _queued: true })
}

export async function queueDiaryEntry({ dog_id, date, event_type, notes1, notes2, weight_lbs }) {
  const queueId = await db.diaryQueue.add({ dog_id: dog_id || null, date, event_type, notes1: notes1 || null, notes2: notes2 || null, weight_lbs: weight_lbs || null, created_at: localISOString() })
  await db.diaryEntries.add({
    id: Date.now(),
    dog_id: dog_id || null,
    date,
    event_type,
    notes1: notes1 || null,
    notes2: notes2 || null,
    weight_lbs: weight_lbs || null,
    _queued: true,
    _queueId: queueId,
  })
}

export async function deleteDiaryEntry(id) {
  const local = await db.diaryEntries.get(id)
  if (local?._queued) {
    await db.diaryQueue.delete(local._queueId)
  } else {
    try {
      const { api } = await import('./api')
      await api.delete(`/milestones/${id}`)
    } catch { /* offline — server delete skipped, local still removed */ }
  }
  await db.diaryEntries.delete(id)
}

export async function deleteHealthEvent(id) {
  const local = await db.healthEvents.get(id)
  if (local?._queued) {
    await db.healthQueue.where({ dog_id: local.dog_id, timestamp: local.timestamp }).delete()
  } else {
    try {
      const { api } = await import('./api')
      await api.delete(`/health-events/${id}`)
    } catch { /* offline — server delete skipped, local still removed */ }
  }
  await db.healthEvents.delete(id)
}
