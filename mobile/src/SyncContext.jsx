import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import { ping, signalFromRtt, syncFromBackend, flushQueue, getLastSynced } from './sync'
import { getBackendUrl } from './api'

const SyncContext = createContext(null)

const PING_INTERVAL_MS = 30_000

export function SyncProvider({ children }) {
  const [signal, setSignal] = useState('offline')
  const [lastSynced, setLastSynced] = useState(getLastSynced)
  const [syncing, setSyncing] = useState(false)
  const [queueCount, setQueueCount] = useState(0)
  const [syncVersion, setSyncVersion] = useState(0)
  const wasOnlineRef = useRef(false)
  const syncInProgressRef = useRef(false)

  const refreshQueueCount = useCallback(async () => {
    const { db } = await import('./db')
    const [peePoo, health] = await Promise.all([db.eventQueue.count(), db.healthQueue.count()])
    setQueueCount(peePoo + health)
  }, [])

  const doSync = useCallback(async () => {
    if (!getBackendUrl()) return
    if (syncInProgressRef.current) return
    syncInProgressRef.current = true
    setSyncing(true)
    try {
      await flushQueue()
      await syncFromBackend()
      const { getLastSynced: gls } = await import('./sync')
      setLastSynced(gls())
      await refreshQueueCount()
      setSyncVersion(v => v + 1)
    } catch {
      // sync failed — will retry on next ping
    } finally {
      setSyncing(false)
      syncInProgressRef.current = false
    }
  }, [refreshQueueCount])

  const checkConnectivity = useCallback(async () => {
    const { ok, rtt } = await ping()
    const newSignal = signalFromRtt(ok ? rtt : null)
    setSignal(newSignal)
    const isOnline = newSignal !== 'offline'
    if (isOnline && !wasOnlineRef.current) doSync()
    wasOnlineRef.current = isOnline
  }, [doSync])

  // periodic ping
  useEffect(() => {
    checkConnectivity()
    const interval = setInterval(checkConnectivity, PING_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [checkConnectivity])

  // auto-sync when WiFi is detected (Android Network Information API)
  useEffect(() => {
    const conn = navigator.connection
    if (!conn) return
    const handler = () => {
      if (conn.type === 'wifi') doSync()
    }
    conn.addEventListener('change', handler)
    return () => conn.removeEventListener('change', handler)
  }, [doSync])

  // sync on first load if configured
  useEffect(() => {
    if (getBackendUrl() && !getLastSynced()) doSync()
  }, [doSync])

  useEffect(() => { refreshQueueCount() }, [refreshQueueCount])

  return (
    <SyncContext.Provider value={{ signal, lastSynced, syncing, queueCount, syncVersion, syncNow: doSync, refreshQueueCount }}>
      {children}
    </SyncContext.Provider>
  )
}

export function useSyncContext() {
  return useContext(SyncContext)
}
