import { useNavigate } from 'react-router-dom'
import { getBackendUrl } from '../api'

export default function HamburgerMenu({ onClose }) {
  const nav = useNavigate()

  function go(path) {
    onClose()
    nav(path)
  }

  const backendHost = (() => {
    try { return new URL(getBackendUrl()).host } catch { return getBackendUrl() }
  })()

  const buildTime = (() => {
    try { return new Date(__BUILD_TIME__).toLocaleString() } catch { return '' }
  })()

  async function handleClearAndReload() {
    if ('serviceWorker' in navigator) {
      const regs = await navigator.serviceWorker.getRegistrations()
      await Promise.all(
        regs.filter(r => r.scope.includes('/doglog/')).map(r => r.unregister())
      )
    }
    if ('caches' in window) {
      const keys = await caches.keys()
      await Promise.all(keys.map(async k => {
        const cache = await caches.open(k)
        const requests = await cache.keys()
        const mine = requests.filter(r => r.url.includes('/doglog/'))
        if (mine.length === requests.length) {
          await caches.delete(k)
        } else {
          await Promise.all(mine.map(r => cache.delete(r)))
        }
      }))
    }
    window.location.href = window.location.origin + '/doglog/'
  }

  return (
    <>
      {/* Backdrop */}
      <div style={s.backdrop} onClick={onClose} />

      {/* Drawer */}
      <div style={s.drawer}>
        <div style={s.header}>
          <span style={s.title}>Dog Log</span>
          <button style={s.close} onClick={onClose}>✕</button>
        </div>

        <div style={s.divider} />

        <button style={s.item} onClick={handleClearAndReload}>↺ Force refresh</button>

        <div style={s.divider} />

        <button style={s.itemMeta} onClick={() => go('/connect')} title="Tap to reconfigure">
          {backendHost || 'Not connected'}
        </button>
        {buildTime && <div style={s.itemMeta}>Built {buildTime}</div>}
      </div>
    </>
  )
}

const s = {
  backdrop: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)', zIndex: 100 },
  drawer: { position: 'fixed', top: 0, left: 0, bottom: 0, width: 260, background: '#fff', zIndex: 101, display: 'flex', flexDirection: 'column', boxShadow: '2px 0 12px rgba(0,0,0,0.15)' },
  header: { display: 'flex', alignItems: 'center', padding: '14px 16px', background: '#5b8dd9', color: '#fff' },
  title: { flex: 1, fontWeight: 700, fontSize: 18 },
  close: { background: 'none', border: 'none', color: '#fff', fontSize: 18, cursor: 'pointer', padding: '0 4px' },
  item: { display: 'block', width: '100%', padding: '16px 20px', background: 'none', border: 'none', textAlign: 'left', fontSize: 16, color: '#1a202c', cursor: 'pointer', borderBottom: '1px solid #f0f0f0' },
  divider: { borderTop: '1px solid #e2e8f0', margin: '8px 0' },
  itemMeta: { display: 'block', width: '100%', padding: '8px 20px', background: 'none', border: 'none', textAlign: 'left', fontSize: 13, color: '#888', cursor: 'pointer' },
}
