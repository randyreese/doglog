import { useNavigate } from 'react-router-dom'

export default function AdversePage() {
  const nav = useNavigate()
  return (
    <div style={p.page}>
      <div style={p.header}>
        <button style={p.hamburger} onClick={() => nav('/connect')}>☰</button>
        <span style={p.title}>Dog Log</span>
      </div>
      <div style={p.placeholder}>Adverse events — coming in Sprint 3</div>
      <div style={p.tabBar}>
        <button style={p.tab} onClick={() => nav('/')}>Walk</button>
        <button style={{ ...p.tab, ...p.tabActive }}>Adverse</button>
        <button style={p.tab} onClick={() => nav('/meals')}>Meals</button>
      </div>
    </div>
  )
}

const p = {
  page: { display: 'flex', flexDirection: 'column', height: '100dvh', background: '#f5f5f5' },
  header: { display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', background: '#5b8dd9', color: '#fff' },
  hamburger: { background: 'none', border: 'none', color: '#fff', fontSize: 22, cursor: 'pointer', padding: '0 4px' },
  title: { flex: 1, fontWeight: 700, fontSize: 18 },
  placeholder: { flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#aaa', fontSize: 15 },
  tabBar: { display: 'flex', borderTop: '1px solid #ddd', background: '#fff' },
  tab: { flex: 1, padding: '12px 0', background: 'none', border: 'none', fontSize: 14, color: '#888', cursor: 'pointer', fontWeight: 500 },
  tabActive: { color: '#5b8dd9', fontWeight: 700, borderTop: '2px solid #5b8dd9' },
}
