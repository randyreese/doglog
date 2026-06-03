import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { db } from '../db'
import { queueDiaryEntry, deleteDiaryEntry } from '../sync'
import { useSyncContext } from '../SyncContext'
import { useConfig } from '../ConfigContext'
import HamburgerMenu from '../components/HamburgerMenu'
import SwipeableRow from '../components/SwipeableRow'

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function fmtDate(dateStr) {
  if (!dateStr) return '—'
  const [y, m, d] = dateStr.split('-')
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${months[parseInt(m, 10) - 1]} ${parseInt(d, 10)}, ${y}`
}

function isUrl(str) {
  return str && (str.startsWith('http://') || str.startsWith('https://'))
}

// ── Diary row ─────────────────────────────────────────────────────────────────
function DiaryRow({ entry, dogMap, typeMap, onDelete, onEdit }) {
  const dogName = entry.dog_id ? (dogMap[entry.dog_id] || '?') : 'All'
  const typeLabel = typeMap[entry.event_type] || entry.event_type
  const hasUrl = isUrl(entry.notes2)
  const canEdit = !entry._queued

  return (
    <SwipeableRow onDelete={onDelete}>
      <div
        style={{ ...dr.row, cursor: canEdit ? 'pointer' : 'default' }}
        onClick={() => canEdit && onEdit(entry)}
      >
        <div style={dr.dateBlock}>
          <span style={dr.date}>{fmtDate(entry.date)}</span>
        </div>
        <div style={dr.content}>
          <div style={dr.topLine}>
            <span style={dr.dogLabel}>{dogName}</span>
            <span style={dr.sep}> · </span>
            <span style={dr.typeLabel}>{typeLabel}</span>
          </div>
          {entry.notes1 ? <span style={dr.notes}>{entry.notes1}</span> : null}
          {hasUrl ? (
            <a
              href={entry.notes2}
              target="_blank"
              rel="noopener noreferrer"
              style={dr.viewLink}
              onClick={e => e.stopPropagation()}
            >
              View →
            </a>
          ) : null}
        </div>
        {entry._queued && <span style={dr.queueDot} />}
      </div>
    </SwipeableRow>
  )
}

const dr = {
  row: { display: 'flex', alignItems: 'flex-start', gap: 8, padding: '8px 12px', border: '1px solid #e8e8e8', background: '#fff' },
  dateBlock: { flexShrink: 0, paddingTop: 1, minWidth: 80 },
  date: { fontSize: 12, color: '#888' },
  content: { flex: 1, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 },
  topLine: { display: 'flex', alignItems: 'center' },
  dogLabel: { fontSize: 15, color: '#1a202c', fontWeight: 600 },
  sep: { fontSize: 15, color: '#bbb', margin: '0 2px' },
  typeLabel: { fontSize: 15, color: '#555' },
  notes: { fontSize: 12, color: '#888', fontStyle: 'italic', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  viewLink: { fontSize: 12, color: '#3182ce', textDecoration: 'none' },
  queueDot: { width: 8, height: 8, borderRadius: '50%', background: '#e53e3e', flexShrink: 0, marginTop: 4 },
}

// ── Edit sheet ────────────────────────────────────────────────────────────────
function EditSheet({ target, open, dogs, milestoneEventTypes, onClose, onSave }) {
  const [dateVal, setDateVal] = useState(todayStr())
  const [dogId, setDogId] = useState(null)
  const [eventType, setEventType] = useState('')
  const [notes1, setNotes1] = useState('')
  const [notes2, setNotes2] = useState('')
  const [hasWeight, setHasWeight] = useState(false)
  const [weightLbs, setWeightLbs] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)

  useEffect(() => {
    if (target !== null) {
      if (target === 'new') {
        setDateVal(todayStr())
        setDogId(null)
        setEventType(milestoneEventTypes[0]?.value || '')
        setNotes1('')
        setNotes2('')
        setHasWeight(false)
        setWeightLbs('')
      } else {
        setDateVal(target.date || todayStr())
        setDogId(target.dog_id ?? null)
        setEventType(target.event_type || '')
        setNotes1(target.notes1 || '')
        setNotes2(target.notes2 || '')
        setHasWeight(target.weight_lbs != null)
        setWeightLbs(target.weight_lbs != null ? String(target.weight_lbs) : '')
      }
      setSaveError(null)
    }
  }, [target, milestoneEventTypes])

  async function handleSave() {
    if (!eventType) { setSaveError('Type required'); return }
    setSaving(true)
    setSaveError(null)
    try {
      const body = {
        dog_id: dogId ?? null,
        date: dateVal,
        event_type: eventType,
        notes1: notes1.trim() || null,
        notes2: notes2.trim() || null,
        weight_lbs: hasWeight && weightLbs ? parseFloat(weightLbs) : null,
      }
      await onSave(target === 'new' ? null : target.id, body)
      onClose()
    } catch (e) {
      setSaveError(e.message || 'Save failed — try again')
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
        style={{ ...sh.sheet, padding: 16, gap: 14, display: 'flex', flexDirection: 'column', transform: open ? 'translateY(0)' : 'translateY(100%)', maxHeight: '85vh', overflowY: 'auto' }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={ed.title}>{target === 'new' ? 'Add Entry' : 'Edit Entry'}</span>
          <button style={ed.cancelBtn} onClick={onClose}>Cancel</button>
        </div>

        <div>
          <div style={ed.fieldLabel}>Date</div>
          <input type="date" style={ed.input} value={dateVal} onChange={e => setDateVal(e.target.value)} />
        </div>

        <div>
          <div style={ed.fieldLabel}>Dog</div>
          <select style={ed.input} value={dogId ?? ''} onChange={e => setDogId(e.target.value ? Number(e.target.value) : null)}>
            <option value="">All</option>
            {dogs.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>

        <div>
          <div style={ed.fieldLabel}>Type</div>
          <select style={ed.input} value={eventType} onChange={e => setEventType(e.target.value)}>
            {milestoneEventTypes.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input type="checkbox" id="wt-chk" checked={hasWeight} onChange={e => setHasWeight(e.target.checked)} />
          <label htmlFor="wt-chk" style={{ ...ed.fieldLabel, marginBottom: 0, cursor: 'pointer' }}>Weight</label>
          {hasWeight && <>
            <input
              type="number" step="0.1" min="0"
              style={{ ...ed.input, width: 80, marginBottom: 0 }}
              placeholder="lbs"
              value={weightLbs}
              onChange={e => setWeightLbs(e.target.value)}
            />
            <span style={{ fontSize: 13, color: '#555' }}>lbs</span>
          </>}
        </div>

        <div>
          <div style={ed.fieldLabel}>Notes</div>
          <textarea style={ed.textarea} placeholder="Optional" value={notes1} onChange={e => setNotes1(e.target.value)} rows={3} />
        </div>

        <div>
          <div style={ed.fieldLabel}>Link (optional)</div>
          <input type="url" style={ed.input} placeholder="https://…" value={notes2} onChange={e => setNotes2(e.target.value)} />
        </div>

        {saveError && <div style={ed.error}>{saveError}</div>}

        <button style={ed.saveBtn} disabled={saving} onClick={handleSave}>
          {saving ? 'Saving…' : 'Save'}
        </button>
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
  fieldLabel: { fontSize: 13, color: '#555', marginBottom: 4 },
  input: { width: '100%', padding: '8px 10px', border: '1px solid #ccc', borderRadius: 8, fontSize: 15, boxSizing: 'border-box', fontFamily: 'inherit' },
  textarea: { width: '100%', border: '1px solid #ccc', borderRadius: 8, padding: 10, fontSize: 15, fontFamily: 'inherit', resize: 'vertical', boxSizing: 'border-box' },
  error: { fontSize: 13, color: '#e53e3e', textAlign: 'center' },
  cancelBtn: { padding: '8px 16px', background: '#fff', border: '1px solid #ccc', borderRadius: 8, fontSize: 15, cursor: 'pointer' },
  saveBtn: { padding: 12, background: '#5b8dd9', color: '#fff', border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 600, cursor: 'pointer', width: '100%' },
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function DiaryPage() {
  const nav = useNavigate()
  const { syncVersion, signal, queueCount, refreshQueueCount } = useSyncContext()
  const { dogs, milestoneEventTypes, dogMap } = useConfig()
  const [entries, setEntries] = useState([])
  const [selectedDogs, setSelectedDogs] = useState(new Set())
  const [selectedType, setSelectedType] = useState('')
  const [editTarget, setEditTarget] = useState(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const swipeStartX = useRef(null)
  const swipeStartY = useRef(null)
  const swipeFromRow = useRef(false)

  const typeMap = Object.fromEntries((milestoneEventTypes || []).map(t => [t.value, t.label]))

  const loadEntries = useCallback(async () => {
    const all = await db.diaryEntries.orderBy('date').reverse().toArray()
    setEntries(all)
  }, [])

  useEffect(() => { loadEntries() }, [loadEntries])
  useEffect(() => { if (syncVersion > 0) loadEntries() }, [syncVersion, loadEntries])

  function toggleDog(dogId) {
    setSelectedDogs(prev => {
      const next = new Set(prev)
      if (next.has(dogId)) next.delete(dogId)
      else next.add(dogId)
      return next
    })
  }

  // Dog filter: show All-dogs records (dog_id=null) regardless; filter by selected dogs otherwise
  const filtered = entries.filter(e => {
    if (selectedDogs.size > 0 && e.dog_id !== null && !selectedDogs.has(e.dog_id)) return false
    if (selectedType && e.event_type !== selectedType) return false
    return true
  })

  async function handleSave(id, body) {
    if (id === null) {
      try {
        const result = await api.post('/milestones/', body)
        await db.diaryEntries.put(result)
      } catch {
        await queueDiaryEntry(body)
        await refreshQueueCount()
      }
    } else {
      const result = await api.patch(`/milestones/${id}`, body)
      await db.diaryEntries.put(result)
    }
    await loadEntries()
  }

  async function handleDelete(entry) {
    await deleteDiaryEntry(entry.id)
    await refreshQueueCount()
    await loadEntries()
  }

  function onPageTouchStart(e) {
    swipeStartX.current = e.touches[0].clientX
    swipeStartY.current = e.touches[0].clientY
    swipeFromRow.current = !!e.target.closest('[data-swipeable]')
  }

  function onPageTouchEnd(e) {
    if (swipeStartX.current === null) return
    const dx = e.changedTouches[0].clientX - swipeStartX.current
    const dy = e.changedTouches[0].clientY - swipeStartY.current
    swipeStartX.current = null
    if (swipeFromRow.current) return
    if (Math.abs(dx) < 100 || Math.abs(dx) < Math.abs(dy) * 2) return
    if (dx > 0) nav('/health')
  }

  const signalEmoji = { good: '🟢', weak: '🟡', offline: '🔴' }[signal] || '🔴'

  return (
    <>
      <div style={p.page} onTouchStart={onPageTouchStart} onTouchEnd={onPageTouchEnd}>
        {menuOpen && <HamburgerMenu onClose={() => setMenuOpen(false)} />}

        <div style={p.header}>
          <button style={p.hamburger} onClick={() => setMenuOpen(true)}>☰</button>
          <span style={p.title}>Diary</span>
          {queueCount > 0 && <span style={p.queue}>{queueCount}</span>}
          <span style={p.signalDot}>{signalEmoji}</span>
        </div>

        <div style={p.filterBar}>
          <div style={p.chips}>
            {dogs.map(d => (
              <button
                key={d.id}
                style={{ ...p.chip, ...(selectedDogs.has(d.id) ? p.chipActive : {}) }}
                onClick={() => toggleDog(d.id)}
              >
                {d.name}
              </button>
            ))}
          </div>
          <select style={p.typeSelect} value={selectedType} onChange={e => setSelectedType(e.target.value)}>
            <option value="">All types</option>
            {(milestoneEventTypes || []).map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          <button style={p.addBtn} onClick={() => setEditTarget('new')}>+</button>
        </div>

        <div style={p.list}>
          {filtered.length === 0 ? (
            <div style={p.empty}>No entries</div>
          ) : (
            filtered.map(e => (
              <DiaryRow
                key={e.id}
                entry={e}
                dogMap={dogMap}
                typeMap={typeMap}
                onDelete={() => handleDelete(e)}
                onEdit={entry => setEditTarget(entry)}
              />
            ))
          )}
        </div>

        <div style={p.tabBar}>
          <button style={p.tab} onClick={() => nav('/')}>Walk</button>
          <button style={p.tab} onClick={() => nav('/meals')}>Meals</button>
          <button style={p.tab} onClick={() => nav('/health')}>Health</button>
          <button style={{ ...p.tab, ...p.tabActive }}>Diary</button>
        </div>
      </div>

      <EditSheet
        target={editTarget}
        open={editTarget !== null}
        dogs={dogs}
        milestoneEventTypes={milestoneEventTypes || []}
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
  filterBar: { display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: '#fff', borderBottom: '1px solid #e2e8f0', flexShrink: 0 },
  chips: { display: 'flex', gap: 6 },
  chip: { padding: '4px 10px', borderRadius: 16, border: '1px solid #ccc', background: '#f5f5f5', fontSize: 13, cursor: 'pointer', fontWeight: 500, color: '#555' },
  chipActive: { background: '#5b8dd9', color: '#fff', borderColor: '#5b8dd9' },
  typeSelect: { flex: 1, padding: '4px 8px', border: '1px solid #ccc', borderRadius: 8, fontSize: 13, background: '#fff' },
  addBtn: { padding: '4px 14px', background: '#5b8dd9', color: '#fff', border: 'none', borderRadius: 8, fontSize: 20, cursor: 'pointer', lineHeight: '1.4' },
  list: { flex: 1, minHeight: 0, overflowY: 'auto', background: '#f5f5f5', padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: 4 },
  empty: { padding: '20px 12px', color: '#aaa', textAlign: 'center', fontSize: 14 },
  tabBar: { position: 'fixed', bottom: 0, left: 0, right: 0, display: 'flex', borderTop: '1px solid #ddd', background: '#fff', zIndex: 10 },
  tab: { flex: 1, padding: '12px 0', background: 'none', border: 'none', fontSize: 15, color: '#888', cursor: 'pointer', fontWeight: 500 },
  tabActive: { color: '#5b8dd9', fontWeight: 700, borderTop: '2px solid #5b8dd9' },
}
