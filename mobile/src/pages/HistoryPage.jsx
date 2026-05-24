import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

export default function HistoryPage() {
  const nav = useNavigate()
  const [data, setData] = useState(null)

  useEffect(() => {
    api.get('/history/?days=7').then(setData).catch(() => {})
  }, [])

  if (!data) return <div style={p.loading}>Loading…</div>

  const { dogs, days } = data

  return (
    <div style={p.page}>

      {/* Header */}
      <div style={p.header}>
        <button style={p.back} onClick={() => nav(-1)}>‹</button>
        <span style={p.title}>7-Day History</span>
      </div>

      <div style={p.scroll}>
        {dogs.map(dog => (
          <div key={dog.id} style={p.section}>
            <div style={p.dogName}>{dog.name}</div>
            <div style={p.grid}>

              {/* Day labels */}
              <div style={p.typeLabel} />
              {days.map(d => (
                <div key={d.date} style={{ ...p.cell, ...p.dayLabel }}>{d.label}</div>
              ))}

              {/* Poo row */}
              <div style={p.typeLabel}>Poop</div>
              {days.map(d => {
                const count = d.counts[String(dog.id)]?.poo ?? 0
                return (
                  <div key={d.date} style={{ ...p.cell, color: count === 0 ? '#e53e3e' : '#2f855a', fontWeight: 700 }}>
                    {count}
                  </div>
                )
              })}

              {/* Pee row — only for tracked dogs */}
              {dog.track_pee && <>
                <div style={p.typeLabel}>Pee</div>
                {days.map(d => {
                  const count = d.counts[String(dog.id)]?.pee ?? 0
                  return (
                    <div key={d.date} style={{ ...p.cell, color: '#555' }}>
                      {count}
                    </div>
                  )
                })}
              </>}

            </div>
          </div>
        ))}
      </div>

    </div>
  )
}

const COLS = 8  // label col + 7 days
const p = {
  page: { display: 'flex', flexDirection: 'column', position: 'fixed', inset: 0, background: '#f5f5f5' },
  header: { display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', background: '#5b8dd9', color: '#fff', flexShrink: 0 },
  back: { background: 'none', border: 'none', color: '#fff', fontSize: 28, cursor: 'pointer', padding: '0 4px', lineHeight: 1 },
  title: { fontWeight: 700, fontSize: 18 },
  scroll: { flex: 1, overflowY: 'auto', padding: '12px' },
  loading: { padding: 32, textAlign: 'center', color: '#888' },
  section: { background: '#fff', borderRadius: 8, marginBottom: 12, overflow: 'hidden', border: '1px solid #e2e8f0' },
  dogName: { padding: '10px 14px', fontWeight: 700, fontSize: 16, color: '#1a202c', borderBottom: '1px solid #f0f0f0' },
  grid: { display: 'grid', gridTemplateColumns: `80px repeat(7, 1fr)`, padding: '8px 4px' },
  dayLabel: { fontWeight: 600, color: '#888', fontSize: 12 },
  typeLabel: { padding: '6px 10px', fontSize: 13, color: '#555', display: 'flex', alignItems: 'center' },
  cell: { display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '6px 2px', fontSize: 16 },
}
