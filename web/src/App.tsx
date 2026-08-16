import { useEffect, useState } from 'react'
import { ApiError, checkHealth, scanCard } from './api'
import { prepareImage } from './imagePrep'
import HistoryScreen from './screens/HistoryScreen'
import ResultsScreen from './screens/ResultsScreen'
import ScanScreen from './screens/ScanScreen'
import SettingsScreen from './screens/SettingsScreen'
import { loadSettings, pushHistory } from './storage'
import type { ScanResponse } from './types'

type View = 'scan' | 'results' | 'settings' | 'history'

function App() {
  // First run: no saved settings yet, force onboarding.
  const [view, setView] = useState<View>(() => (loadSettings() ? 'scan' : 'settings'))
  const [lastResult, setLastResult] = useState<ScanResponse | null>(null)
  const [lastAskingPrice, setLastAskingPrice] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [serverDown, setServerDown] = useState(false)

  useEffect(() => {
    checkHealth().then(ok => {
      if (!ok) setServerDown(true)
    })
  }, [])

  async function handleScan(front: File, back: File | null, askingPrice: number | null) {
    const settings = loadSettings()
    if (!settings) {
      setView('settings')
      return
    }
    setBusy(true)
    setError(null)
    try {
      // Downscale/re-encode to JPEG before upload; previews keep the originals.
      const [prepFront, prepBack] = await Promise.all([
        prepareImage(front),
        back ? prepareImage(back) : Promise.resolve(null),
      ])
      const response = await scanCard(prepFront, prepBack, askingPrice, settings)
      pushHistory({ at: new Date().toISOString(), response, askingPrice: askingPrice ?? undefined })
      setLastResult(response)
      setLastAskingPrice(askingPrice)
      setView('results')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Try again.')
    } finally {
      setBusy(false)
    }
  }

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
        <>
          {error && (
            <p role="alert">
              {error} <button onClick={() => setError(null)}>Dismiss</button>
            </p>
          )}
          <ScanScreen onSubmit={handleScan} busy={busy} />
        </>
      )}
      {view === 'results' && lastResult && (
        <>
          {lastAskingPrice != null && (
            <p className="caption">Asking price: ${lastAskingPrice}</p>
          )}
          <ResultsScreen result={lastResult} onRescan={() => setView('scan')} />
        </>
      )}
      {view === 'history' && (
        <HistoryScreen
          onSelect={e => {
            setLastResult(e.response)
            setLastAskingPrice(e.askingPrice ?? null)
            setView('results')
          }}
        />
      )}
    </div>
  )
}

export default App
