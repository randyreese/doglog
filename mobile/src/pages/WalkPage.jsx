import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { queueEvent, deleteEvent } from '../sync'
import { useSyncContext } from '../SyncContext'

// Color thresholds (hours elapsed)
const PEE_YELLOW_H = 4
const PEE_RED_H = 6
const POO_YELLOW_H = 8
const POO_RED_H = 12

// Display labels vs backend values for event types
const EVENT_TYPES = ['Pee', 'Poop']
const EVENT_TYPE_VALUES = { Pee: 'pee', Poop: 'poo' }
const EVENT_TYPE_LABELS = { pee: 'Pee', poo: 'Poop' }

function elapsedHours(isoTs) {
  if (!isoTs) return Infinity
  return (Date.now() - new Date(isoTs).getTime()) / 3_600_000
}

function timeColor(hours, yellowH, redH) {
  if (hours >= redH) return '#e53e3e'
  if (hours >= yellowH) return '#d97706'
  return '#2f855a'
}

function fmtTime(isoTs) {
  if (!isoTs) return '—'
  const d = new Date(isoTs)
  let h = d.getHours(), m = d.getMinutes()
  const ampm = h >= 12 ? 'pm' : 'am'
  h = h % 12 || 12
  return `${h}:${String(m).padStart(2, '0')}${ampm}`
}

function fmtElapsed(isoTs) {
  if (!isoTs) return ''
  const h = elapsedHours(isoTs)
  if (h < 1) return `${Math.round(h * 60)}m ago`
  return `${h.toFixed(1)}h ago`
}

// ── Status strip ──────────────────────────────────────────────────────────────
function StatusStrip({ dogs, status }) {
  const [expanded, setExpanded] = useState(false)

  if (!status || status.length === 0) return null

  const statusByDog = Object.fromEntries(status.map(d => [d.id, d]))

  if (!expanded) {
    const summary = dogs.map(dog => {
      const s = statusByDog[dog.id]
      if (!s) return null
      const pooH = elapsedHours(s.last_poo)
      const color = timeColor(pooH, POO_YELLOW_H, POO_RED_H)
      return (
        <span key={dog.id} style={{ marginRight: 12 }}>
          <span style={{ fontWeight: 600 }}>{dog.name}</span>
          {' poop '}
          <span style={{ color }}>{fmtElapsed(s.last_poo) || 'none today'}</span>
        </span>
      )
    }).filter(Boolean)

    return (
      <div style={ss.strip} onClick={() => setExpanded(true)}>
        <div style={ss.stripRow}>{summary}<span style={ss.chevron}>▼</span></div>
      </div>
    )
  }

  return (
    <div style={ss.strip} onClick={() => setExpanded(false)}>
      <table style={ss.table}>
        <thead>
          <tr>
            <th style={ss.th}></th>
            <th style={ss.th}>Pee</th>
            <th style={ss.th}>Poop</th>
          </tr>
        </thead>
        <tbody>
          {dogs.map(dog => {
            const s = statusByDog[dog.id]
            if (!s) return null
            const peeH = elapsedHours(s.last_pee)
            const pooH = elapsedHours(s.last_poo)
            return (
              <tr key={dog.id}>
                <td style={ss.tdName}>{dog.name}</td>
                <td style={{ ...ss.td, color: s.track_pee ? timeColor(peeH, PEE_YELLOW_H, PEE_RED_H) : '#999' }}>
                  {s.track_pee ? fmtTime(s.last_pee) : '—'}
                </td>
                <td style={{ ...ss.td, color: timeColor(pooH, POO_YELLOW_H, POO_RED_H) }}>
                  {fmtTime(s.last_poo)}{s.poo_count_today > 0 ? ` ×${s.poo_count_today}` : ''}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      <div style={{ textAlign: 'right', fontSize: 11, color: '#999', marginTop: 2 }}>▲ collapse</div>
    </div>
  )
}

const ss = {
  strip: { background: '#fff', borderBottom: '1px solid #e2e8f0', padding: '8px 12px', cursor: 'pointer', userSelect: 'none' },
  stripRow: { display: 'flex', alignItems: 'center', fontSize: 13, color: '#333', flexWrap: 'wrap', gap: 4 },
  chevron: { marginLeft: 'auto', color: '#999', fontSize: 11 },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 14 },
  th: { textAlign: 'center', fontWeight: 600, padding: '2px 8px', color: '#555', fontSize: 12 },
  td: { textAlign: 'center', padding: '4px 8px', fontWeight: 600 },
  tdName: { textAlign: 'left', padding: '4px 8px', fontWeight: 700, color: '#333' },
}

// ── Carousel ──────────────────────────────────────────────────────────────────
function Carousel({ items, index, onAdvance, label }) {
  return (
    <div style={cs.row}>
      <div style={cs.label}>{label}</div>
      <div style={cs.display}>{items[index]}</div>
      <button style={cs.btn} onClick={onAdvance}>›</button>
    </div>
  )
}

const cs = {
  row: { display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', background: '#fff', borderBottom: '1px solid #e2e8f0' },
  label: { fontSize: 12, color: '#888', width: 36, flexShrink: 0 },
  display: { flex: 1, fontSize: 22, fontWeight: 700, color: '#1a202c', textAlign: 'center' },
  btn: { width: 52, height: 52, fontSize: 28, background: '#fff', color: '#000', border: '2px solid #5b8dd9', borderRadius: 10, cursor: 'pointer', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 400 },
}

// ── History row ───────────────────────────────────────────────────────────────
function HistoryRow({ event, dogName, checked, onCheck }) {
  return (
    <div style={hr.row}>
      <span style={hr.time}>{fmtTime(event.timestamp)}</span>
      <span style={hr.label}>{dogName}: {EVENT_TYPE_LABELS[event.type] || event.type}</span>
      <input type="checkbox" checked={checked} onChange={e => onCheck(event.id, e.target.checked)} style={hr.check} />
    </div>
  )
}

const hr = {
  row: { display: 'flex', alignItems: 'center', padding: '10px 12px', border: '1px solid #e8e8e8', background: '#fff', marginBottom: 2, borderRadius: 4 },
  time: { fontSize: 14, color: '#555', width: 60, flexShrink: 0 },
  label: { flex: 1, fontSize: 15, color: '#1a202c', textTransform: 'capitalize' },
  check: { width: 22, height: 22, cursor: 'pointer', accentColor: '#5b8dd9' },
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function WalkPage() {
  const nav = useNavigate()
  const { signal, queueCount, syncVersion, syncNow, refreshQueueCount } = useSyncContext()

  const [dogs, setDogs] = useState([])
  const [dogIdx, setDogIdx] = useState(0)
  const [eventIdx, setEventIdx] = useState(0)
  const [events, setEvents] = useState([])
  const [status, setStatus] = useState([])
  const [checked, setChecked] = useState({})
  const [logging, setLogging] = useState(false)

  const loadDogs = useCallback(async () => {
    try {
      const data = await api.get('/dogs/')
      setDogs([...data].sort((a, b) => b.name.localeCompare(a.name)))
    } catch { /* offline */ }
  }, [])

  const loadEvents = useCallback(async () => {
    try {
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const data = await api.get(`/events/?since=${today.toISOString()}&limit=50`)
      setEvents(data)
    } catch { /* offline */ }
  }, [])

  const loadStatus = useCallback(async () => {
    try {
      const data = await api.get('/status/')
      setStatus(data.dogs)
    } catch { /* offline */ }
  }, [])

  useEffect(() => {
    loadDogs()
    loadEvents()
    loadStatus()
  }, [loadDogs, loadEvents, loadStatus])

  useEffect(() => {
    if (syncVersion === 0) return
    loadEvents()
    loadStatus()
  }, [syncVersion, loadEvents, loadStatus])

  async function handleLog() {
    if (!dogs.length || logging) return
    navigator.vibrate?.(40)
    const dog = dogs[dogIdx]
    const type = EVENT_TYPE_VALUES[EVENT_TYPES[eventIdx]]
    setLogging(true)
    try {
      try {
        await api.post('/events/', { dog_id: dog.id, type })
      } catch {
        await queueEvent({ dog_id: dog.id, type })
      }
      await refreshQueueCount()
      await loadEvents()
      await loadStatus()
    } finally {
      setLogging(false)
    }
  }

  async function handleDelete() {
    const ids = Object.entries(checked).filter(([, v]) => v).map(([k]) => parseInt(k))
    for (const id of ids) {
      await deleteEvent(id)
    }
    setChecked({})
    await refreshQueueCount()
    await loadEvents()
    await loadStatus()
  }

  function toggleCheck(id, val) {
    setChecked(prev => ({ ...prev, [id]: val }))
  }

  const anyChecked = Object.values(checked).some(Boolean)
  const dogMap = Object.fromEntries(dogs.map(d => [d.id, d.name]))

  const signalColor = signal === 'good' ? '#2f855a' : signal === 'weak' ? '#d97706' : '#e53e3e'
  const signalLabel = signal === 'good' ? '●' : signal === 'weak' ? '◑' : '○'

  return (
    <div style={p.page}>

      {/* Header */}
      <div style={p.header}>
        <button style={p.hamburger} onClick={() => nav('/connect')}>☰</button>
        <span style={p.title}>Dog Log</span>
        <span style={p.signalDot} title={signal}>
          <span style={{ color: signalColor }}>{signalLabel}</span>
        </span>
        {queueCount > 0 && <span style={p.queue}>{queueCount}</span>}
      </div>

      {/* Status strip */}
      <StatusStrip dogs={dogs} status={status} />

      {/* History — fills available space */}
      <div style={p.history}>
        {events.map(ev => (
          <HistoryRow
            key={ev.id}
            event={ev}
            dogName={dogMap[ev.dog_id] || '?'}
            checked={!!checked[ev.id]}
            onCheck={toggleCheck}
          />
        ))}
        {events.length === 0 && <div style={p.empty}>No events today</div>}
      </div>

      {/* Delete button */}
      {anyChecked && (
        <div style={p.deleteRow}>
          <button style={p.deleteBtn} onClick={handleDelete}>Delete selected</button>
        </div>
      )}

      {/* Dog carousel */}
      {dogs.length > 0 ? (
        <Carousel
          label="Dog"
          items={dogs.map(d => d.name)}
          index={dogIdx}
          onAdvance={() => setDogIdx(i => (i + 1) % dogs.length)}
        />
      ) : (
        <div style={p.loading}>Loading dogs…</div>
      )}

      {/* Event type carousel */}
      <Carousel
        label="Type"
        items={EVENT_TYPES}
        index={eventIdx}
        onAdvance={() => setEventIdx(i => (i + 1) % EVENT_TYPES.length)}
      />

      {/* Log button */}
      <div style={p.logRow}>
        <button
          style={{ ...p.logBtn, ...(logging || !dogs.length ? p.logBtnDisabled : {}) }}
          onClick={handleLog}
          disabled={logging || !dogs.length}
        >
          {logging ? 'Logging…' : 'Log'}
        </button>
      </div>

      {/* Bottom tab bar */}
      <div style={p.tabBar}>
        <button style={{ ...p.tab, ...p.tabActive }}>Walk</button>
        <button style={p.tab} onClick={() => nav('/meals')}>Meals</button>
        <button style={p.tab} onClick={() => nav('/health')}>Health</button>
      </div>
    </div>
  )
}

const p = {
  page: { display: 'flex', flexDirection: 'column', position: 'fixed', top: 0, right: 0, bottom: 0, left: 0, background: '#f5f5f5', paddingBottom: 50, boxSizing: 'border-box' },
  header: { display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', background: '#5b8dd9', color: '#fff' },
  hamburger: { background: 'none', border: 'none', color: '#fff', fontSize: 22, cursor: 'pointer', padding: '0 4px' },
  title: { flex: 1, fontWeight: 700, fontSize: 18 },
  signalDot: { background: '#fff', borderRadius: '50%', width: 32, height: 32, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 20 },
  queue: { background: '#e53e3e', color: '#fff', borderRadius: 10, fontSize: 12, padding: '1px 6px', fontWeight: 700 },
  loading: { padding: 16, textAlign: 'center', color: '#888', background: '#fff', borderBottom: '1px solid #e2e8f0' },
  logRow: { display: 'flex', justifyContent: 'flex-end', padding: '10px 12px', background: '#f5f5f5' },
  logBtn: { width: 100, height: 52, background: '#fff', color: '#000', border: '2px solid #5b8dd9', borderRadius: 10, fontSize: 20, fontWeight: 400, cursor: 'pointer' },
  logBtnDisabled: { opacity: 0.5, cursor: 'default' },
  history: { flex: 1, minHeight: 0, overflowY: 'auto', background: '#f5f5f5', padding: '8px 12px' },
  empty: { padding: '20px 12px', color: '#aaa', textAlign: 'center', fontSize: 14 },
  deleteRow: { padding: '8px 12px', background: '#f5f5f5', display: 'flex', justifyContent: 'flex-end' },
  deleteBtn: { padding: '10px 20px', background: '#e53e3e', color: '#fff', border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 600, cursor: 'pointer' },
  tabBar: { position: 'fixed', bottom: 0, left: 0, right: 0, display: 'flex', borderTop: '1px solid #ddd', background: '#fff', zIndex: 10 },
  tab: { flex: 1, padding: '12px 0', background: 'none', border: 'none', fontSize: 14, color: '#888', cursor: 'pointer', fontWeight: 500 },
  tabActive: { color: '#5b8dd9', fontWeight: 700, borderTop: '2px solid #5b8dd9' },
}
