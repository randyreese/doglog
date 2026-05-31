import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { queueMealLog, localISOString } from '../sync'
import { useSyncContext } from '../SyncContext'
import { useConfig } from '../ConfigContext'
import { db } from '../db'
import HamburgerMenu from '../components/HamburgerMenu'

const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const PCT_OPTIONS = [0, 25, 50, 75, 100]

function localDateString(d = new Date()) {
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function formatDateDisplay(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  return `${DAYS[d.getDay()].slice(0, 3)}, ${MONTHS[d.getMonth()]} ${d.getDate()}`
}

function offsetDate(dateStr, days) {
  const d = new Date(dateStr + 'T00:00:00')
  d.setDate(d.getDate() + days)
  return localDateString(d)
}

function fmtShortDate(dateStr) {
  const [, m, d] = dateStr.split('-').map(Number)
  return `${m}/${d}`
}

function abbrevSlot(label) {
  const first = label.trim().split(/\s+/)[0].toLowerCase()
  return first.length <= 3 ? first : first.slice(0, 3)
}

function barColor(log) {
  if (!log || log.percent_consumed === null || log.percent_consumed === undefined) return '#d1d5db'
  if (log.percent_consumed === 0) return '#ef4444'
  if (log.percent_consumed === 100) return '#22c55e'
  return '#f59e0b'
}

// ── Edit sheet ────────────────────────────────────────────────────────────────
function EditSheet({ target, open, mealIngredients, onClose, onSave }) {
  const [pct, setPct] = useState(100)
  const [notes, setNotes] = useState('')
  const [ingredients, setIngredients] = useState({})
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)

  useEffect(() => {
    if (target) {
      const log = target.log
      const ingList = target.ingredients || mealIngredients
      setPct(log?.percent_consumed ?? 100)
      setNotes(log?.notes || '')
      const saved = log?.ingredients || {}
      // Default all ingredients to checked unless explicitly saved as false
      setIngredients(Object.fromEntries(ingList.map(i => [i.value, saved[i.value] ?? true])))
      setSaveError(null)
    }
  }, [target, mealIngredients])

  async function handleSave() {
    setSaving(true)
    setSaveError(null)
    try {
      await onSave(target.dog.id, target.slot.value, target.meal_date, pct, notes, ingredients)
      onClose()
    } catch {
      setSaveError('Save failed — try again')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      style={{ ...sh.overlay, opacity: open ? 1 : 0, pointerEvents: open ? 'auto' : 'none' }}
      onClick={onClose}
    >
      <div
        style={{ ...sh.sheet, padding: 16, gap: 14, display: 'flex', flexDirection: 'column', transform: open ? 'translateY(0)' : 'translateY(100%)' }}
        onClick={e => e.stopPropagation()}
      >
        <div style={ed.title}>
          {target ? `${target.dog.name} — ${target.slot.label}` : ''}
        </div>

        {/* % selector */}
        <div>
          <div style={ed.fieldLabel}>% consumed</div>
          <div style={ed.pctRow}>
            {PCT_OPTIONS.map(v => (
              <button
                key={v}
                style={{ ...ed.pctBtn, ...(pct === v ? ed.pctBtnActive : {}) }}
                onClick={() => setPct(v)}
              >
                {v}
              </button>
            ))}
          </div>
        </div>

        {/* Notes */}
        <div>
          <div style={ed.fieldLabel}>Notes</div>
          <textarea
            style={ed.textarea}
            placeholder="Optional"
            value={notes}
            onChange={e => setNotes(e.target.value)}
            rows={2}
          />
        </div>

        {/* Ingredients */}
        {(() => {
          const ingList = target?.ingredients || mealIngredients
          return ingList.length > 0 && (
            <div>
              <div style={ed.fieldLabel}>Ingredients</div>
              {ingList.map(ing => (
                <label key={ing.value} style={ed.checkRow}>
                  <input
                    type="checkbox"
                    checked={!!ingredients[ing.value]}
                    onChange={e => setIngredients(prev => ({ ...prev, [ing.value]: e.target.checked }))}
                    style={ed.checkbox}
                  />
                  <span style={ed.checkLabel}>{ing.label}</span>
                </label>
              ))}
            </div>
          )
        })()}

        {saveError && <div style={ed.error}>{saveError}</div>}

        <div style={ed.actions}>
          <button style={ed.cancel} onClick={onClose}>Cancel</button>
          <button style={ed.save} onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

const sh = {
  overlay: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 50, display: 'flex', alignItems: 'flex-end', transition: 'opacity 0.2s' },
  sheet: { background: '#fff', width: '100%', borderRadius: '16px 16px 0 0', overflow: 'hidden', transition: 'transform 0.25s ease-out' },
}

const ed = {
  title: { fontSize: 16, fontWeight: 700, color: '#1a202c' },
  fieldLabel: { fontSize: 12, color: '#888', marginBottom: 6 },
  pctRow: { display: 'flex', gap: 8 },
  pctBtn: { flex: 1, padding: '10px 0', borderRadius: 8, border: '1px solid #ccc', background: '#f5f5f5', fontSize: 15, fontWeight: 500, cursor: 'pointer', color: '#555' },
  pctBtnActive: { background: '#5b8dd9', color: '#fff', borderColor: '#5b8dd9' },
  textarea: { width: '100%', border: '1px solid #ccc', borderRadius: 8, padding: 10, fontSize: 15, fontFamily: 'inherit', resize: 'vertical', boxSizing: 'border-box' },
  checkRow: { display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', cursor: 'pointer' },
  checkbox: { width: 20, height: 20, accentColor: '#5b8dd9', cursor: 'pointer' },
  checkLabel: { fontSize: 15, color: '#1a202c' },
  error: { fontSize: 13, color: '#e53e3e', textAlign: 'center' },
  actions: { display: 'flex', justifyContent: 'flex-end', gap: 10 },
  cancel: { padding: '10px 20px', background: '#fff', border: '1px solid #ccc', borderRadius: 8, fontSize: 15, cursor: 'pointer' },
  save: { padding: '10px 20px', background: '#5b8dd9', color: '#fff', border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 600, cursor: 'pointer' },
}

// ── Meal row ──────────────────────────────────────────────────────────────────
function MealRow({ slot, log, onTap }) {
  const logged = log && log.percent_consumed !== null && log.percent_consumed !== undefined
  const pctDisplay = logged ? `${log.percent_consumed}%` : '—'
  const isSkipped = logged && log.percent_consumed === 0
  const hasNote = !!(log?.notes?.trim())
  const hasException = logged && log.ingredients && Object.values(log.ingredients).some(v => v === false)
  const isQueued = !!(log?._queued)
  return (
    <div style={mr.row} onClick={onTap}>
      <span style={mr.slot}>{slot.label}</span>
      <span style={mr.icons}>
        {hasNote && <span style={mr.noteIcon}>✎</span>}
        {hasException && <span style={mr.exceptIcon}>!</span>}
      </span>
      {isQueued && <span style={mr.queueDot} />}
      <span style={{ ...mr.pct, color: isSkipped ? '#e53e3e' : logged ? '#2f855a' : '#bbb' }}>
        {pctDisplay}
      </span>
    </div>
  )
}

const mr = {
  row: { display: 'flex', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #f0f0f0', background: '#fff', cursor: 'pointer' },
  slot: { flex: 1, fontSize: 15, color: '#1a202c' },
  icons: { display: 'flex', gap: 4, marginRight: 8, alignItems: 'center' },
  noteIcon: { fontSize: 14, color: '#5b8dd9', lineHeight: 1 },
  exceptIcon: { width: 18, height: 18, background: '#fee2e2', color: '#e53e3e', borderRadius: '50%', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 800 },
  queueDot: { width: 8, height: 8, borderRadius: '50%', background: '#e53e3e', flexShrink: 0, marginRight: 6 },
  pct: { fontSize: 15, fontWeight: 600, width: 44, textAlign: 'right' },
}

// ── Multi-day summary ─────────────────────────────────────────────────────────
function MultiDayView({ dogId, mealSlots }) {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.get(`/meal-logs/range/?dog_id=${dogId}&days=30`)
      .then(data => { setLogs(data); setLoading(false) })
      .catch(() => { setLogs([]); setLoading(false) })
  }, [dogId])

  const byDate = {}
  logs.forEach(log => {
    if (!byDate[log.meal_date]) byDate[log.meal_date] = {}
    byDate[log.meal_date][log.slot] = log
  })

  const dates = []
  for (let i = 0; i < 30; i++) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    dates.push(localDateString(d))
  }

  if (loading) return <div style={{ padding: 24, textAlign: 'center', color: '#aaa', fontSize: 14 }}>Loading…</div>

  return (
    <div>
      {/* Header row */}
      <div style={{ ...md.row, position: 'sticky', top: 0, background: '#f0f4ff', borderBottom: '1px solid #d0d8f0' }}>
        <span style={md.dateLabel} />
        <div style={md.bars}>
          {mealSlots.map(slot => (
            <div key={slot.value} style={md.barHeader}>{abbrevSlot(slot.label)}</div>
          ))}
        </div>
      </div>
      {dates.map(dateStr => {
        const dayLogs = byDate[dateStr] || {}
        return (
          <div key={dateStr} style={md.row}>
            <span style={md.dateLabel}>{fmtShortDate(dateStr)}</span>
            <div style={md.bars}>
              {mealSlots.map(slot => (
                <div
                  key={slot.value}
                  style={{ ...md.bar, background: barColor(dayLogs[slot.value]) }}
                  title={`${slot.label}: ${dayLogs[slot.value]?.percent_consumed ?? 'not logged'}%`}
                />
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

const md = {
  row: { display: 'flex', alignItems: 'center', padding: '6px 16px', borderBottom: '1px solid #f0f0f0', background: '#fff' },
  dateLabel: { width: 40, flexShrink: 0, fontSize: 12, color: '#555', fontWeight: 500 },
  bars: { display: 'flex', gap: 4, flex: 1 },
  bar: { flex: 1, height: 22, borderRadius: 4 },
  barHeader: { flex: 1, textAlign: 'center', fontSize: 11, color: '#666', fontWeight: 600 },
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function MealsPage() {
  const nav = useNavigate()
  const { signal, queueCount, syncVersion, refreshQueueCount } = useSyncContext()
  const { dogs, mealSlots, mealIngredients, mealConfigs } = useConfig()

  const today = localDateString()
  const [currentDate, setCurrentDate] = useState(today)
  const [logs, setLogs] = useState([])
  const [editTarget, setEditTarget] = useState(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [multiDayOpen, setMultiDayOpen] = useState(false)
  const [multiDayDogId, setMultiDayDogId] = useState(null)

  // Swipe navigation
  const swipeStartX = useRef(null)
  const swipeStartY = useRef(null)

  function onPageTouchStart(e) {
    if (multiDayOpen) return
    swipeStartX.current = e.touches[0].clientX
    swipeStartY.current = e.touches[0].clientY
  }

  function onPageTouchEnd(e) {
    if (swipeStartX.current === null) return
    const dx = e.changedTouches[0].clientX - swipeStartX.current
    const dy = e.changedTouches[0].clientY - swipeStartY.current
    swipeStartX.current = null
    if (multiDayOpen) return
    if (Math.abs(dx) < 100 || Math.abs(dx) < Math.abs(dy) * 2) return
    if (dx < 0) nav('/health')
    else nav('/')
  }

  const loadLogs = useCallback(async () => {
    try {
      const data = await api.get(`/meal-logs/?meal_date=${currentDate}`)
      setLogs(data)
    } catch {
      const local = await db.mealLogs.where('meal_date').equals(currentDate).toArray()
      setLogs(local)
    }
  }, [currentDate])

  useEffect(() => { loadLogs() }, [loadLogs])
  useEffect(() => { if (syncVersion > 0) loadLogs() }, [syncVersion, loadLogs])

  // build lookup: `${dog_id}:${slot}` → log
  const logMap = Object.fromEntries(logs.map(l => [`${l.dog_id}:${l.slot}`, l]))

  const isToday = currentDate === today

  function goBack() { setCurrentDate(d => offsetDate(d, -1)) }
  function goForward() { if (!isToday) setCurrentDate(d => offsetDate(d, 1)) }

  function toggleHistory() {
    const next = !multiDayOpen
    setMultiDayOpen(next)
    if (!next) loadLogs()
  }

  async function handleSave(dogId, slot, meal_date, pct, notes, ingredients) {
    const body = { dog_id: dogId, slot, meal_date, percent_consumed: pct, notes: notes || null, ingredients }
    try {
      await api.post('/meal-logs/', body)
    } catch {
      await queueMealLog({ dog_id: dogId, slot, meal_date, percent_consumed: pct, notes: notes || null, ingredients })
      await refreshQueueCount()
    }
    await loadLogs()
  }

  const signalColor = signal === 'good' ? '#2f855a' : signal === 'weak' ? '#d97706' : '#e53e3e'
  const signalLabel = signal === 'good' ? '●' : signal === 'weak' ? '◑' : '○'

  return (
    <>
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

        {/* Date pager — hidden in history mode */}
        {!multiDayOpen && (
          <div style={p.pager}>
            <button style={p.pagerBtn} onClick={goBack}>‹</button>
            <span style={p.pagerDate}>{formatDateDisplay(currentDate)}</span>
            <button style={{ ...p.pagerBtn, ...(isToday ? p.pagerBtnDisabled : {}) }} onClick={goForward} disabled={isToday}>›</button>
          </div>
        )}

        {/* Dog chips for history mode */}
        {multiDayOpen && (
          <div style={p.chipRow}>
            {dogs.map(dog => {
              const activeDogId = multiDayDogId ?? dogs[0]?.id
              return (
                <button
                  key={dog.id}
                  style={{ ...p.chip, ...(activeDogId === dog.id ? p.chipActive : {}) }}
                  onClick={() => setMultiDayDogId(dog.id)}
                >
                  {dog.name}
                </button>
              )
            })}
          </div>
        )}

        {/* Content */}
        <div style={p.content}>
          {multiDayOpen ? (
            (multiDayDogId ?? dogs[0]?.id) != null && (
              <MultiDayView dogId={multiDayDogId ?? dogs[0]?.id} mealSlots={mealSlots} />
            )
          ) : (
            <>
              {dogs.map(dog => (
                <div key={dog.id} style={p.dogSection}>
                  <div style={p.dogHeader}>{dog.name}</div>
                  {mealSlots.map(slot => (
                    <MealRow
                      key={slot.value}
                      slot={slot}
                      log={logMap[`${dog.id}:${slot.value}`] || null}
                      onTap={() => setEditTarget({
                        dog,
                        slot,
                        meal_date: currentDate,
                        log: logMap[`${dog.id}:${slot.value}`] || null,
                        ingredients: mealConfigs[`${dog.id}:${slot.value}`] || null,
                      })}
                    />
                  ))}
                </div>
              ))}
              {dogs.length === 0 && <div style={p.empty}>Loading…</div>}
            </>
          )}
        </div>

        {/* Action row */}
        <div style={p.actionRow}>
          <button
            style={{ ...p.historyBtn, ...(multiDayOpen ? p.historyBtnActive : {}) }}
            onClick={toggleHistory}
          >
            History
          </button>
        </div>

        {/* Tab bar */}
        <div style={p.tabBar}>
          <button style={p.tab} onClick={() => nav('/')}>Walk</button>
          <button style={{ ...p.tab, ...p.tabActive }}>Meals</button>
          <button style={p.tab} onClick={() => nav('/health')}>Health</button>
        </div>
      </div>

      <EditSheet
        target={editTarget}
        open={!!editTarget}
        mealIngredients={mealIngredients}
        onClose={() => setEditTarget(null)}
        onSave={handleSave}
      />
    </>
  )
}

const p = {
  page: { display: 'flex', flexDirection: 'column', position: 'fixed', top: 0, right: 0, bottom: 0, left: 0, background: '#f5f5f5', paddingBottom: 50, boxSizing: 'border-box' },
  header: { display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', background: '#5b8dd9', color: '#fff' },
  hamburger: { background: 'none', border: 'none', color: '#fff', fontSize: 22, cursor: 'pointer', padding: '0 4px' },
  title: { flex: 1, fontWeight: 700, fontSize: 18 },
  signalDot: { background: '#fff', borderRadius: '50%', width: 32, height: 32, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 20 },
  queue: { background: '#e53e3e', color: '#fff', borderRadius: 10, fontSize: 12, padding: '1px 6px', fontWeight: 700 },
  pager: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', background: '#fff', borderBottom: '1px solid #e2e8f0' },
  pagerBtn: { width: 40, height: 40, fontSize: 26, background: 'none', border: 'none', cursor: 'pointer', color: '#5b8dd9', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' },
  pagerBtnDisabled: { color: '#ccc', cursor: 'default' },
  pagerDate: { fontSize: 16, fontWeight: 600, color: '#1a202c' },
  content: { flex: 1, minHeight: 0, overflowY: 'auto' },
  dogSection: { marginBottom: 8 },
  dogHeader: { padding: '6px 16px 4px', fontSize: 16, fontWeight: 600, color: '#1a202c', background: '#f5f5f5' },
  empty: { padding: 24, textAlign: 'center', color: '#aaa', fontSize: 14 },
  actionRow: { display: 'flex', justifyContent: 'flex-start', padding: '10px 12px', background: '#f5f5f5', flexShrink: 0 },
  historyBtn: { height: 52, padding: '0 16px', background: '#fff', color: '#5b8dd9', border: '2px solid #5b8dd9', borderRadius: 10, fontSize: 20, fontWeight: 400, cursor: 'pointer' },
  historyBtnActive: { background: '#5b8dd9', color: '#fff' },
  chipRow: { display: 'flex', gap: 8, padding: '10px 16px', background: '#f5f5f5', borderBottom: '1px solid #e2e8f0', flexShrink: 0 },
  chip: { padding: '6px 16px', borderRadius: 20, border: '1px solid #ccc', background: '#fff', fontSize: 14, color: '#555', cursor: 'pointer' },
  chipActive: { background: '#5b8dd9', color: '#fff', borderColor: '#5b8dd9' },
  tabBar: { position: 'fixed', bottom: 0, left: 0, right: 0, display: 'flex', borderTop: '1px solid #ddd', background: '#fff', zIndex: 10 },
  tab: { flex: 1, padding: '12px 0', background: 'none', border: 'none', fontSize: 20, color: '#888', cursor: 'pointer', fontWeight: 500 },
  tabActive: { color: '#5b8dd9', fontWeight: 700, borderTop: '2px solid #5b8dd9' },
}
