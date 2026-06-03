import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import { getBackendUrl } from './api'
import { SyncProvider } from './SyncContext'
import { ConfigProvider } from './ConfigContext'
import ConnectPage from './pages/ConnectPage'
import WalkPage from './pages/WalkPage'
import HealthPage from './pages/HealthPage'
import MealsPage from './pages/MealsPage'
import DiaryPage from './pages/DiaryPage'

function RequireBackend({ children }) {
  return getBackendUrl() ? children : <Navigate to="/connect" replace />
}

export default function App() {
  return (
    <SyncProvider>
      <ConfigProvider>
      <HashRouter>
        <Routes>
          <Route path="/connect" element={<ConnectPage />} />
          <Route path="/" element={<RequireBackend><WalkPage /></RequireBackend>} />
          <Route path="/health" element={<RequireBackend><HealthPage /></RequireBackend>} />
          <Route path="/meals" element={<RequireBackend><MealsPage /></RequireBackend>} />
          <Route path="/diary" element={<RequireBackend><DiaryPage /></RequireBackend>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </HashRouter>
      </ConfigProvider>
    </SyncProvider>
  )
}
