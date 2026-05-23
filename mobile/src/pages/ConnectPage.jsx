import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getBackendUrl, setBackendUrl } from '../api'

export default function ConnectPage() {
  const [url, setUrl] = useState(getBackendUrl)
  const [status, setStatus] = useState('')
  const [connecting, setConnecting] = useState(false)
  const nav = useNavigate()

  async function connect() {
    const trimmed = url.trim().replace(/\/+$/, '')
    if (!trimmed) return
    setConnecting(true)
    setStatus('Connecting…')
    try {
      const res = await fetch(`${trimmed}/doglog/health`, { signal: AbortSignal.timeout(5000) })
      if (!res.ok) throw new Error()
      setBackendUrl(trimmed)
      nav('/', { replace: true })
    } catch {
      setStatus('Could not reach backend. Check URL and Wi-Fi.')
    } finally {
      setConnecting(false)
    }
  }

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.logo}>Dog Log</div>
        <p style={s.hint}>Enter your backend URL to connect.</p>
        <input
          style={s.input}
          type="url"
          placeholder="https://mint.local"
          value={url}
          onChange={e => setUrl(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !connecting && connect()}
        />
        <button
          style={{ ...s.btn, ...(!url.trim() || connecting ? s.btnDisabled : {}) }}
          onClick={connect}
          disabled={!url.trim() || connecting}
        >
          {connecting ? 'Connecting…' : 'Connect'}
        </button>
        {status && <p style={s.status}>{status}</p>}
      </div>
      <p style={s.build}>build {new Date(__BUILD_TIME__).toLocaleString()}</p>
    </div>
  )
}

const s = {
  page: { minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem', background: '#f5f5f5' },
  card: { background: '#fff', borderRadius: 12, padding: '2rem 1.5rem', maxWidth: 360, width: '100%', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
  logo: { fontSize: '1.75rem', fontWeight: 700, color: '#5b8dd9', marginBottom: '0.5rem', textAlign: 'center' },
  hint: { color: '#666', marginBottom: '1.5rem', textAlign: 'center', fontSize: '0.9rem' },
  input: { display: 'block', width: '100%', padding: '0.75rem', fontSize: '1rem', border: '1px solid #ccc', borderRadius: 6, marginBottom: '0.75rem', boxSizing: 'border-box' },
  btn: { width: '100%', padding: '0.75rem', background: '#5b8dd9', color: '#fff', border: 'none', borderRadius: 6, fontSize: '1rem', fontWeight: 600, cursor: 'pointer' },
  btnDisabled: { opacity: 0.5, cursor: 'default' },
  status: { marginTop: '1rem', color: '#c00', fontSize: '0.875rem', textAlign: 'center' },
  build: { marginTop: '1rem', color: '#bbb', fontSize: '0.75rem', textAlign: 'center' },
}
