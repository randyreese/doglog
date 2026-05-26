import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { queueHealthEvent, deleteHealthEvent, localISOString } from '../sync'
import { useSyncContext } from '../SyncContext'
import { useConfig } from '../ConfigContext'
import HamburgerMenu from '../components/HamburgerMenu'

function fmtTime(isoTs) {
  if (!isoTs) return { date: '—', time: '—' }
  const d = new Date(isoTs)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const year = String(d.getFullYear()).slice(-2)
  let h = d.getHours(), m = d.getMinutes()
  const ampm = h >= 12 ? 'pm' : 'am'
  h = h % 12 || 12
  return { date: `${month}/${day}/${year}`, time: `${h}:${String(m).padStart(2, '0')}${ampm}` }
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      URL.revokeObjectURL(url)
      const MAX = 1200
      let { width, height } = img
      if (width > MAX || height > MAX) {
        if (width > height) { height = Math.round(height * MAX / width); width = MAX }
        else { width = Math.round(width * MAX / height); height = MAX }
      }
      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      canvas.getContext('2d').drawImage(img, 0, 0, width, height)
      resolve(canvas.toDataURL('image/jpeg', 0.85).split(',')[1])
    }
    img.onerror = reject
    img.src = url
  })
}

// ── History row ───────────────────────────────────────────────────────────────
function HealthRow({ event, dogName, typeLabel, checked, onCheck, onEdit }) {
  const { date, time } = fmtTime(event.timestamp)
  const canEdit = !event._queued
  return (
    <div
      style={{ ...hr.row, cursor: canEdit ? 'pointer' : 'default' }}
      onClick={() => canEdit && onEdit(event)}
    >
      <div style={hr.timeBlock}>
        <span style={hr.date}>{date}</span>
        <span style={hr.time}>{time}</span>
      </div>
      <div style={hr.label}>
        <span style={hr.labelMain}>{dogName}: {typeLabel}</span>
        {event.notes ? <span style={hr.notes}>{event.notes}</span> : null}
      </div>
      <input
        type="checkbox"
        checked={checked}
        onChange={e => onCheck(event.id, e.target.checked)}
        onClick={e => e.stopPropagation()}
        style={hr.check}
      />
    </div>
  )
}

const hr = {
  row: { display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', border: '1px solid #e8e8e8', background: '#fff', marginBottom: 2, borderRadius: 4 },
  timeBlock: { width: 68, flexShrink: 0, display: 'flex', flexDirection: 'column' },
  date: { fontSize: 11, color: '#999', lineHeight: '1.3' },
  time: { fontSize: 14, color: '#555', lineHeight: '1.3' },
  label: { flex: 1, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 },
  labelMain: { fontSize: 15, color: '#1a202c' },
  notes: { fontSize: 12, color: '#888', fontStyle: 'italic', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  check: { width: 22, height: 22, cursor: 'pointer', accentColor: '#5b8dd9', flexShrink: 0 },
}

// ── Type picker row (opens bottom sheet) ─────────────────────────────────────
function TypePickerRow({ selectedType, typeLabel, onOpen }) {
  return (
    <div style={cs.row}>
      <div style={cs.label}>Type</div>
      <div style={cs.display}>{typeLabel}</div>
      <button style={cs.btn} onClick={onOpen}>^</button>
    </div>
  )
}

// ── Dog carousel ─────────────────────────────────────────────────────────────
function Carousel({ label, items, index, onAdvance }) {
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

// ── Bottom sheet (type picker) ────────────────────────────────────────────────
function TypeSheet({ open, options, selectedType, onSelect, onClose }) {
  return (
    <div
      style={{ ...sh.overlay, opacity: open ? 1 : 0, pointerEvents: open ? 'auto' : 'none' }}
      onClick={onClose}
    >
      <div
        style={{ ...sh.sheet, transform: open ? 'translateY(0)' : 'translateY(100%)' }}
        onClick={e => e.stopPropagation()}
      >
        {options.map(opt => (
          <button
            key={opt.value ?? '__all__'}
            style={{ ...sh.option, background: opt.value === selectedType ? '#eef3fd' : '#fff' }}
            onClick={() => { onSelect(opt.value); onClose() }}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Edit sheet (notes + photo) ────────────────────────────────────────────────
function EditSheet({ event, open, onClose, onSave }) {
  const [notes, setNotes] = useState('')
  const [photo, setPhoto] = useState(null)
  const [photoChanged, setPhotoChanged] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)
  const [lightbox, setLightbox] = useState(false)
  const fileRef = useRef(null)

  useEffect(() => {
    if (event) {
      setNotes(event.notes || '')
      setPhoto(event.photo || null)
      setPhotoChanged(false)
      setSaveError(null)
    }
  }, [event])

  async function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    const b64 = await fileToBase64(file)
    setPhoto(b64)
    setPhotoChanged(true)
  }

  async function handleSave() {
    setSaving(true)
    setSaveError(null)
    try {
      await onSave(event.id, notes, photoChanged ? photo : undefined)
      onClose()
    } catch {
      setSaveError('Save failed — try again')
    } finally {
      setSaving(false)
    }
  }

  const photoSrc = photo ? `data:image/jpeg;base64,${photo}` : null

  return (
    <div
      style={{ ...sh.overlay, opacity: open ? 1 : 0, pointerEvents: open ? 'auto' : 'none' }}
      onClick={onClose}
    >
      <div
        style={{ ...sh.sheet, padding: 16, gap: 12, display: 'flex', flexDirection: 'column', transform: open ? 'translateY(0)' : 'translateY(100%)' }}
        onClick={e => e.stopPropagation()}
      >
        <div style={ed.title}>Edit health event</div>

        <textarea
          style={ed.textarea}
          placeholder="Notes (optional)"
          value={notes}
          onChange={e => setNotes(e.target.value)}
          rows={3}
        />

        {lightbox && (
          <div style={ed.lightbox} onClick={() => setLightbox(false)}>
            <img src={photoSrc} alt="full size" style={ed.lightboxImg} />
          </div>
        )}

        <div style={ed.photoSection}>
          {photoSrc
            ? <img src={photoSrc} alt="health event" style={ed.thumb} onClick={() => setLightbox(true)} />
            : <div style={ed.noPhoto}>No photo</div>
          }
          <button style={ed.photoBtn} onClick={() => fileRef.current?.click()}>
            {photo ? 'Change photo' : 'Add photo'}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
        </div>

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
  option: { display: 'block', width: '100%', padding: '18px 20px', border: 'none', borderBottom: '1px solid #eee', fontSize: 17, textAlign: 'left', cursor: 'pointer' },
}

const ed = {
  title: { fontSize: 16, fontWeight: 700, color: '#1a202c' },
  textarea: { width: '100%', border: '1px solid #ccc', borderRadius: 8, padding: 10, fontSize: 15, fontFamily: 'inherit', resize: 'vertical', boxSizing: 'border-box' },
  photoSection: { display: 'flex', alignItems: 'center', gap: 12 },
  lightbox: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.9)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' },
  lightboxImg: { width: '100vw', height: '100vh', objectFit: 'contain' },
  thumb: { width: 72, height: 72, objectFit: 'cover', borderRadius: 8, border: '1px solid #ddd', cursor: 'pointer' },
  noPhoto: { width: 72, height: 72, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5', borderRadius: 8, border: '1px solid #ddd', fontSize: 12, color: '#aaa' },
  photoBtn: { padding: '10px 16px', background: '#fff', border: '1px solid #5b8dd9', borderRadius: 8, fontSize: 14, color: '#5b8dd9', cursor: 'pointer' },
  error: { fontSize: 13, color: '#e53e3e', textAlign: 'center' },
  actions: { display: 'flex', justifyContent: 'flex-end', gap: 10 },
  cancel: { padding: '10px 20px', background: '#fff', border: '1px solid #ccc', borderRadius: 8, fontSize: 15, cursor: 'pointer' },
  save: { padding: '10px 20px', background: '#5b8dd9', color: '#fff', border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 600, cursor: 'pointer' },
}

// ── Filter bar ────────────────────────────────────────────────────────────────
const DATE_OPTIONS = [
  { label: '7d',  days: 7 },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
  { label: 'All', days: null },
]

function FilterBar({ dogs, healthTypes, filter, setFilter }) {
  const [typeSheetOpen, setTypeSheetOpen] = useState(false)

  const typeOptions = [{ value: null, label: 'All types' }, ...healthTypes]
  const activeTypeLabel = filter.type
    ? (healthTypes.find(t => t.value === filter.type)?.label ?? filter.type)
    : 'All types'

  return (
    <div style={fb.container}>
      <div style={fb.row}>
        {DATE_OPTIONS.map(opt => (
          <button
            key={opt.label}
            style={{ ...fb.pill, ...(filter.days === opt.days ? fb.pillActive : {}) }}
            onClick={() => setFilter(f => ({ ...f, days: opt.days }))}
          >
            {opt.label}
          </button>
        ))}
      </div>
      <div style={fb.row}>
        <button
          style={{ ...fb.pill, ...(filter.dogId === null ? fb.pillActive : {}) }}
          onClick={() => setFilter(f => ({ ...f, dogId: null }))}
        >
          All dogs
        </button>
        {dogs.map(d => (
          <button
            key={d.id}
            style={{ ...fb.pill, ...(filter.dogId === d.id ? fb.pillActive : {}) }}
            onClick={() => setFilter(f => ({ ...f, dogId: d.id }))}
          >
            {d.name}
          </button>
        ))}
        <button
          style={{ ...fb.pill, ...(filter.type !== null ? fb.pillActive : {}), marginLeft: 'auto' }}
          onClick={() => setTypeSheetOpen(true)}
        >
          {activeTypeLabel} ▾
        </button>
      </div>
      <TypeSheet
        open={typeSheetOpen}
        options={typeOptions}
        selectedType={filter.type}
        onSelect={type => setFilter(f => ({ ...f, type }))}
        onClose={() => setTypeSheetOpen(false)}
      />
    </div>
  )
}

const fb = {
  container: { background: '#fff', borderBottom: '1px solid #e2e8f0', padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: 6 },
  row: { display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' },
  pill: { padding: '5px 12px', borderRadius: 14, border: '1px solid #ccc', background: '#f5f5f5', fontSize: 13, cursor: 'pointer', fontWeight: 500, color: '#555' },
  pillActive: { background: '#5b8dd9', color: '#fff', borderColor: '#5b8dd9' },
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function HealthPage() {
  const nav = useNavigate()
  const { signal, queueCount, syncVersion, refreshQueueCount } = useSyncContext()
  const { dogs, healthTypes, dogMap } = useConfig()

  const [dogIdx, setDogIdx] = useState(0)
  const [selectedType, setSelectedType] = useState('')
  const [events, setEvents] = useState([])
  const [checked, setChecked] = useState({})
  const [logging, setLogging] = useState(false)
  const [typeSheetOpen, setTypeSheetOpen] = useState(false)
  const [editEvent, setEditEvent] = useState(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [filter, setFilter] = useState({ days: 30, dogId: null, type: null })

  // default selectedType to first in list once loaded
  useEffect(() => {
    if (healthTypes.length > 0 && !selectedType) {
      setSelectedType(healthTypes[0].value)
    }
  }, [healthTypes, selectedType])

  const loadEvents = useCallback(async () => {
    try {
      const data = await api.get('/health-events/?limit=200')
      setEvents(data)
    } catch { /* offline */ }
  }, [])

  useEffect(() => { loadEvents() }, [loadEvents])

  useEffect(() => {
    if (syncVersion === 0) return
    loadEvents()
  }, [syncVersion, loadEvents])

  async function handleLog() {
    if (!dogs.length || !selectedType || logging) return
    navigator.vibrate?.(40)
    const dog = dogs[dogIdx]
    const ts = localISOString()
    setLogging(true)
    try {
      try {
        await api.post('/health-events/', { dog_id: dog.id, type: selectedType, timestamp: ts })
      } catch {
        await queueHealthEvent({ dog_id: dog.id, type: selectedType, timestamp: ts })
      }
      await refreshQueueCount()
      await loadEvents()
    } finally {
      setLogging(false)
    }
  }

  async function handleDelete() {
    const ids = Object.entries(checked).filter(([, v]) => v).map(([k]) => parseInt(k))
    for (const id of ids) {
      await deleteHealthEvent(id)
    }
    setChecked({})
    await refreshQueueCount()
    await loadEvents()
  }

  async function handleEditSave(id, notes, photo) {
    const body = { notes }
    if (photo !== undefined) body.photo = photo
    await api.patch(`/health-events/${id}`, body)
    await loadEvents()
  }

  // client-side filter
  const now = Date.now()
  const filteredEvents = events.filter(ev => {
    if (filter.days !== null) {
      const cutoff = now - filter.days * 24 * 60 * 60 * 1000
      if (new Date(ev.timestamp).getTime() < cutoff) return false
    }
    if (filter.dogId !== null && ev.dog_id !== filter.dogId) return false
    if (filter.type !== null && ev.type !== filter.type) return false
    return true
  })

  const typeMap = Object.fromEntries((healthTypes || []).map(t => [t.value, t.label]))
  const anyChecked = Object.values(checked).some(Boolean)
  const signalColor = signal === 'good' ? '#2f855a' : signal === 'weak' ? '#d97706' : '#e53e3e'
  const signalLabel = signal === 'good' ? '●' : signal === 'weak' ? '◑' : '○'
  const currentTypeLabel = typeMap[selectedType] || selectedType

  return (
    <>
      <div style={p.page}>
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

        {/* Filter bar */}
        <FilterBar dogs={dogs} healthTypes={healthTypes} filter={filter} setFilter={setFilter} />

        {/* History */}
        <div style={p.history}>
          {filteredEvents.map(ev => (
            <HealthRow
              key={ev.id}
              event={ev}
              dogName={dogMap[ev.dog_id] || '?'}
              typeLabel={typeMap[ev.type] || ev.type}
              checked={!!checked[ev.id]}
              onCheck={(id, val) => setChecked(prev => ({ ...prev, [id]: val }))}
              onEdit={setEditEvent}
            />
          ))}
          {filteredEvents.length === 0 && (
            <div style={p.empty}>
              {events.length === 0 ? 'No health events logged' : 'No events match the current filter'}
            </div>
          )}
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

        {/* Type picker */}
        <TypePickerRow
          selectedType={selectedType}
          typeLabel={currentTypeLabel}
          onOpen={() => setTypeSheetOpen(true)}
        />

        {/* Log row */}
        <div style={p.logRow}>
          <button
            style={{ ...p.logBtn, ...(logging || !dogs.length || !selectedType ? p.logBtnDisabled : {}) }}
            onClick={handleLog}
            disabled={logging || !dogs.length || !selectedType}
          >
            {logging ? 'Logging…' : 'Log'}
          </button>
        </div>

        {/* Tab bar */}
        <div style={p.tabBar}>
          <button style={p.tab} onClick={() => nav('/')}>Walk</button>
          <button style={p.tab} onClick={() => nav('/meals')}>Meals</button>
          <button style={{ ...p.tab, ...p.tabActive }}>Health</button>
        </div>
      </div>

      <TypeSheet
        open={typeSheetOpen}
        options={healthTypes}
        selectedType={selectedType}
        onSelect={setSelectedType}
        onClose={() => setTypeSheetOpen(false)}
      />

      <EditSheet
        event={editEvent}
        open={!!editEvent}
        onClose={() => setEditEvent(null)}
        onSave={handleEditSave}
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
  history: { flex: 1, minHeight: 0, overflowY: 'auto', background: '#f5f5f5', padding: '8px 12px' },
  empty: { padding: '20px 12px', color: '#aaa', textAlign: 'center', fontSize: 14 },
  deleteRow: { padding: '8px 12px', background: '#f5f5f5', display: 'flex', justifyContent: 'flex-end' },
  deleteBtn: { padding: '10px 20px', background: '#e53e3e', color: '#fff', border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 600, cursor: 'pointer' },
  loading: { padding: 16, textAlign: 'center', color: '#888', background: '#fff', borderBottom: '1px solid #e2e8f0' },
  logRow: { display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 10, padding: '10px 12px', background: '#f5f5f5' },
  logBtn: { width: 100, height: 52, background: '#fff', color: '#000', border: '2px solid #5b8dd9', borderRadius: 10, fontSize: 20, fontWeight: 400, cursor: 'pointer' },
  logBtnDisabled: { opacity: 0.5, cursor: 'default' },
  tabBar: { position: 'fixed', bottom: 0, left: 0, right: 0, display: 'flex', borderTop: '1px solid #ddd', background: '#fff', zIndex: 10 },
  tab: { flex: 1, padding: '12px 0', background: 'none', border: 'none', fontSize: 14, color: '#888', cursor: 'pointer', fontWeight: 500 },
  tabActive: { color: '#5b8dd9', fontWeight: 700, borderTop: '2px solid #5b8dd9' },
}
