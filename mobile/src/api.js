import { db } from './db'

const URL_KEY = 'doglog_backend_url'

export function getBackendUrl() {
  return localStorage.getItem(URL_KEY) || ''
}

export function setBackendUrl(url) {
  localStorage.setItem(URL_KEY, url.replace(/\/+$/, ''))
}

export function clearBackendUrl() {
  localStorage.removeItem(URL_KEY)
}

async function localGet(path) {
  if (path === '/dogs/') return db.dogs.filter(d => d.active).toArray()

  const eventMatch = path.match(/^\/events\/\?.*dog_id=(\d+)/)
  if (eventMatch) {
    return db.events
      .where('dog_id').equals(parseInt(eventMatch[1]))
      .reverse()
      .limit(50)
      .toArray()
  }

  if (path === '/events/') return db.events.orderBy('timestamp').reverse().limit(50).toArray()

  throw new Error(`No offline fallback for GET ${path}`)
}

async function req(method, path, body) {
  const base = getBackendUrl()
  if (!base) throw new Error('No backend configured')
  try {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 4000)
    let res
    try {
      res = await fetch(`${base}/doglog${path}`, {
        method,
        headers: body ? { 'Content-Type': 'application/json' } : {},
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      })
    } finally {
      clearTimeout(timer)
    }
    if (!res.ok) throw new Error(`${res.status} ${method} ${path}`)
    if (res.status === 204) return null
    return res.json()
  } catch (err) {
    if (method === 'GET') return localGet(path)
    throw err
  }
}

export const api = {
  get: (path) => req('GET', path),
  post: (path, body) => req('POST', path, body),
  patch: (path, body) => req('PATCH', path, body),
  delete: (path) => req('DELETE', path),
}
