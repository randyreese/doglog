import { useState, useEffect, useCallback, useRef } from 'react'
import SwipeableRow from '../components/SwipeableRow'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { db } from '../db'
import { queueEvent, deleteEvent, localISOString } from '../sync'
import { useSyncContext } from '../SyncContext'
import { useConfig } from '../ConfigContext'
import HamburgerMenu from '../components/HamburgerMenu'

const PEE_YELLOW_H = 4
const PEE_RED_H = 6
const POO_YELLOW_H = 8
const POO_RED_H = 12

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

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function fmtTime(isoTs) {
  if (!isoTs) return '—'
  const d = new Date(isoTs)
  const day = DAYS[d.getDay()]
  let h = d.getHours(), m = d.getMinutes()
  const ampm = h >= 12 ? 'pm' : 'am'
  h = h % 12 || 12
  return `${day} ${h}:${String(m).padStart(2, '0')}${ampm}`
}

function fmtElapsed(isoTs) {
  if (!isoTs) return ''
  const h = elapsedHours(isoTs)
  if (h < 1) return `${Math.round(h * 60)}m ago`
  return `${h.toFixed(1)}h ago`
}

// ── Status strip (always expanded) ────────────────────────────────────────────
function StatusStrip({ dogs, status }) {
  if (!status || status.length === 0) return null
  const statusByDog = Object.fromEntries(status.map(d => [d.id, d]))
  return (
    <div style={ss.strip}>
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
    </div>
  )
}

const ss = {
  strip: { background: '#fff', borderBottom: '1px solid #e2e8f0', padding: '8px 12px' },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 14 },
  th: { textAlign: 'center', fontWeight: 600, padding: '2px 8px', color: '#555', fontSize: 12 },
  td: { textAlign: 'center', padding: '4px 8px', fontWeight: 600 },
  tdName: { textAlign: 'left', padding: '4px 8px', fontWeight: 700, color: '#333' },
}

// ── Carousel (no label) ───────────────────────────────────────────────────────
function Carousel({ items, index, onAdvance }) {
  return (
    <div style={cs.row}>
      <div style={cs.display}>{items[index]}</div>
      <button style={cs.btn} onClick={onAdvance}>›</button>
    </div>
  )
}

const cs = {
  row: { display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', background: '#fff', borderBottom: '1px solid #e2e8f0' },
  display: { flex: 1, fontSize: 22, fontWeight: 700, color: '#1a202c', textAlign: 'center' },
  btn: { width: 52, height: 52, fontSize: 32, background: 'transparent', color: '#5b8dd9', border: '1.5px solid #5b8dd9', borderRadius: '50%', cursor: 'pointer', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 400 },
}

// ── History row ───────────────────────────────────────────────────────────────
function HistoryRow({ event, dogName, onDelete, useDayName }) {
  const d = new Date(event.timestamp)
  let h = d.getHours(), m = d.getMinutes()
  const ampm = h >= 12 ? 'pm' : 'am'
  h = h % 12 || 12
  const timeStr = `${h}:${String(m).padStart(2, '0')}${ampm}`
  const dateStr = useDayName
    ? DAYS[d.getDay()]
    : `${d.getMonth() + 1}/${d.getDate()}/${String(d.getFullYear()).slice(2)}`

  return (
    <SwipeableRow onDelete={onDelete}>
      <div style={hr.row}>
        <div style={hr.timeBlock}>
          <span style={hr.day}>{dateStr}</span>
          <span style={hr.time}>{timeStr}</span>
        </div>
        <span style={hr.label}>{dogName}: {EVENT_TYPE_LABELS[event.type] || event.type}</span>
        {event._queued && <span style={hr.queueDot} />}
      </div>
    </SwipeableRow>
  )
}

const hr = {
  row: { display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', border: '1px solid #e8e8e8', background: '#fff' },
  timeBlock: { width: 68, flexShrink: 0, display: 'flex', flexDirection: 'column' },
  day: { fontSize: 11, color: '#999', lineHeight: '1.3' },
  time: { fontSize: 14, color: '#555', lineHeight: '1.3' },
  label: { flex: 1, fontSize: 15, color: '#1a202c', textTransform: 'capitalize' },
  queueDot: { width: 8, height: 8, borderRadius: '50%', background: '#e53e3e', flexShrink: 0 },
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function WalkPage() {
  const nav = useNavigate()
  const { signal, queueCount, syncVersion, refreshQueueCount } = useSyncContext()
  const { dogs } = useConfig()

  const [dogIdx, setDogIdx] = useState(0)
  const [eventIdx, setEventIdx] = useState(0)
  const [events, setEvents] = useState([])
  const [status, setStatus] = useState([])
  const [logging, setLogging] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [historyDogId, setHistoryDogId] = useState(null)
  const [historyEvents, setHistoryEvents] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)

  // Swipe navigation
  const swipeStartX = useRef(null)
  const swipeStartY = useRef(null)
  const swipeFromRow = useRef(false)

  function onPageTouchStart(e) {
    if (historyOpen) return
    swipeStartX.current = e.touches[0].clientX
    swipeStartY.current = e.touches[0].clientY
    swipeFromRow.current = !!e.target.closest('[data-swipeable]')
  }

  function onPageTouchEnd(e) {
    if (swipeStartX.current === null) return
    const dx = e.changedTouches[0].clientX - swipeStartX.current
    const dy = e.changedTouches[0].clientY - swipeStartY.current
    swipeStartX.current = null
    if (historyOpen || swipeFromRow.current) return
    if (Math.abs(dx) < 100 || Math.abs(dx) < Math.abs(dy) * 2) return
    if (dx < 0) nav('/meals')
  }

  const loadEvents = useCallback(async () => {
    try {
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const data = await api.get(`/events/?since=${localISOString(today)}&limit=50`)
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
    loadEvents()
    loadStatus()
  }, [loadEvents, loadStatus])

  useEffect(() => {
    if (syncVersion === 0) return
    loadEvents()
    loadStatus()
  }, [syncVersion, loadEvents, loadStatus])

  const loadHistoryEvents = useCallback(async () => {
    setHistoryLoading(true)
    try {
      const since = new Date()
      since.setDate(since.getDate() - 7)
      since.setHours(0, 0, 0, 0)
      let url = `/events/?since=${localISOString(since)}&limit=200`
      if (historyDogId !== null) url += `&dog_id=${historyDogId}`
      const data = await api.get(url)
      setHistoryEvents(data)
    } catch { /* LAN only */ }
    finally { setHistoryLoading(false) }
  }, [historyDogId])

  useEffect(() => {
    if (historyOpen) loadHistoryEvents()
  }, [historyOpen, loadHistoryEvents])

  async function handleLog() {
    if (!dogs.length || logging) return
    navigator.vibrate?.(40)
    const dog = dogs[dogIdx]
    const type = EVENT_TYPE_VALUES[EVENT_TYPES[eventIdx]]
    setLogging(true)
    try {
      try {
        const event = await api.post('/events/', { dog_id: dog.id, type, timestamp: localISOString() })
        await db.events.put(event)
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

  async function handleDeleteSingle(id) {
    await deleteEvent(id)
    await refreshQueueCount()
    await loadEvents()
    await loadStatus()
  }

  async function handleDeleteHistory(id) {
    await deleteEvent(id)
    await refreshQueueCount()
    await loadHistoryEvents()
    await loadStatus()
  }

  const dogMap = Object.fromEntries(dogs.map(d => [d.id, d.name]))
  const signalColor = signal === 'good' ? '#2f855a' : signal === 'weak' ? '#d97706' : '#e53e3e'
  const signalLabel = signal === 'good' ? '●' : signal === 'weak' ? '◑' : '○'

  return (
    <div style={p.page} onTouchStart={onPageTouchStart} onTouchEnd={onPageTouchEnd}>

      {menuOpen && <HamburgerMenu onClose={() => setMenuOpen(false)} />}

      {/* Header */}
      <div style={p.header}>
        <button style={p.hamburger} onClick={() => setMenuOpen(true)}>☰</button>
        <span style={p.title}>Dog Log</span>
        <span style={p.signalDot} title={signal}>
          <span style={{ color: signalColor }}>{signalLabel}</span>
        </span>
        {queueCount > 0 && <span style={p.queue}>{queueCount}</span>}
      </div>

      {/* Status strip */}
      <StatusStrip dogs={dogs} status={status} />

      {/* Dog filter chips — only in history mode */}
      {historyOpen && (
        <div style={p.chipRow}>
          <button style={{ ...p.chip, ...(historyDogId === null ? p.chipActive : {}) }} onClick={() => setHistoryDogId(null)}>All</button>
          {dogs.map(dog => (
            <button key={dog.id} style={{ ...p.chip, ...(historyDogId === dog.id ? p.chipActive : {}) }} onClick={() => setHistoryDogId(dog.id)}>{dog.name}</button>
          ))}
        </div>
      )}

      {/* History list — fills available space */}
      <div style={p.history}>
        {historyOpen ? (
          <>
            {historyLoading && <div style={p.empty}>Loading…</div>}
            {!historyLoading && historyEvents.map(ev => (
              <HistoryRow key={ev.id} event={ev} dogName={dogMap[ev.dog_id] || '?'} onDelete={() => handleDeleteHistory(ev.id)} useDayName={false} />
            ))}
            {!historyLoading && historyEvents.length === 0 && <div style={p.empty}>No events in last 7 days</div>}
          </>
        ) : (
          <>
            {events.map(ev => (
              <HistoryRow key={ev.id} event={ev} dogName={dogMap[ev.dog_id] || '?'} onDelete={() => handleDeleteSingle(ev.id)} useDayName={true} />
            ))}
            {events.length === 0 && <div style={p.empty}>No events today</div>}
          </>
        )}
      </div>

      {/* Dog + type carousels — hidden in history mode */}
      {!historyOpen && (dogs.length > 0 ? (
        <Carousel
          items={dogs.map(d => d.name)}
          index={dogIdx}
          onAdvance={() => setDogIdx(i => (i + 1) % dogs.length)}
        />
      ) : (
        <div style={p.loading}>Loading dogs…</div>
      ))}

      {!historyOpen && (
        <Carousel
          items={EVENT_TYPES}
          index={eventIdx}
          onAdvance={() => setEventIdx(i => (i + 1) % EVENT_TYPES.length)}
        />
      )}

      {/* Action row */}
      <div style={p.logRow}>
        <button
          style={{ ...p.historyBtn, ...(historyOpen ? p.historyBtnActive : {}) }}
          onClick={() => setHistoryOpen(o => !o)}
        >
          History
        </button>
        {!historyOpen && (
          <button
            style={{ ...p.logBtn, ...(logging || !dogs.length ? p.logBtnDisabled : {}) }}
            onClick={handleLog}
            disabled={logging || !dogs.length}
          >
            {logging ? 'Logging…' : 'Log'}
          </button>
        )}
      </div>

      {/* Bottom tab bar */}
      <div style={p.tabBar}>
        <button style={{ ...p.tab, ...p.tabActive }}>Walk</button>
        <button style={p.tab} onClick={() => nav('/meals')}>Meals</button>
        <button style={p.tab} onClick={() => nav('/health')}>Health</button>
        <button style={p.tab} onClick={() => nav('/diary')}>Diary</button>
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
  logRow: { display: 'flex', justifyContent: 'space-between', padding: '10px 12px', background: '#f5f5f5' },
  historyBtn: { height: 52, padding: '0 16px', background: '#fff', color: '#5b8dd9', border: '2px solid #5b8dd9', borderRadius: 10, fontSize: 20, fontWeight: 400, cursor: 'pointer' },
  historyBtnActive: { background: '#5b8dd9', color: '#fff' },
  chipRow: { display: 'flex', gap: 8, padding: '8px 12px', background: '#fff', borderBottom: '1px solid #e2e8f0', flexShrink: 0 },
  chip: { padding: '6px 14px', borderRadius: 20, border: '1px solid #ccc', background: '#f5f5f5', fontSize: 14, color: '#555', cursor: 'pointer' },
  chipActive: { background: '#5b8dd9', color: '#fff', borderColor: '#5b8dd9' },
  logBtn: { width: 100, height: 52, background: '#fff', color: '#000', border: '2px solid #5b8dd9', borderRadius: 10, fontSize: 20, fontWeight: 400, cursor: 'pointer' },
  logBtnDisabled: { opacity: 0.5, cursor: 'default' },
  history: { flex: 1, minHeight: 0, overflowY: 'auto', background: '#f5f5f5', padding: '8px 12px' },
  empty: { padding: '20px 12px', color: '#aaa', textAlign: 'center', fontSize: 14 },
  tabBar: { position: 'fixed', bottom: 0, left: 0, right: 0, display: 'flex', borderTop: '1px solid #ddd', background: '#fff', zIndex: 10 },
  tab: { flex: 1, padding: '12px 0', background: 'none', border: 'none', fontSize: 15, color: '#888', cursor: 'pointer', fontWeight: 500 },
  tabActive: { color: '#5b8dd9', fontWeight: 700, borderTop: '2px solid #5b8dd9' },
}
