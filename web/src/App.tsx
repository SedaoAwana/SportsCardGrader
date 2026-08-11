import { useEffect, useState } from 'react'
import { checkHealth } from './api'
import SettingsScreen from './screens/SettingsScreen'
import { loadSettings } from './storage'
import type { ScanResponse } from './types'

type View = 'scan' | 'results' | 'settings' | 'history'

function App() {
  // First run: no saved settings yet, force onboarding.
  const [view, setView] = useState<View>(() => (loadSettings() ? 'scan' : 'settings'))
  // Setters land in Tasks 16-17 when scan/results views are implemented.
  const [lastResult] = useState<ScanResponse | null>(null)
  const [lastAskingPrice] = useState<number | null>(null)
  const [busy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [serverDown, setServerDown] = useState(false)

  useEffect(() => {
    checkHealth().then(ok => {
      if (!ok) setServerDown(true)
    })
  }, [])

  return (
    <div className="app">
      <header>
        <h1>Card Scanner</h1>
        <nav>
          <button onClick={() => setView('scan')}>Scan</button>
          <button onClick={() => setView('history')}>History</button>
          <button onClick={() => setView('settings')}>Settings</button>
        </nav>
      </header>

      {serverDown && (
        <div className="banner" role="alert">
          Scan server unreachable
          <button onClick={() => setServerDown(false)}>Dismiss</button>
        </div>
      )}

      {view === 'settings' && <SettingsScreen onDone={() => setView('scan')} />}
      {view === 'scan' && (
        <div className="screen">
          {busy && <p>Scanning…</p>}
          {error && (
            <p role="alert">
              {error} <button onClick={() => setError(null)}>Dismiss</button>
            </p>
          )}
          <p>coming soon</p>
        </div>
      )}
      {view === 'results' && (
        <div className="screen">
          {/* Task 17 renders lastResult / lastAskingPrice here. */}
          <p>{lastResult || lastAskingPrice != null ? 'Result ready' : 'coming soon'}</p>
        </div>
      )}
      {view === 'history' && (
        <div className="screen">
          <p>coming soon</p>
        </div>
      )}
    </div>
  )
}

export default App
