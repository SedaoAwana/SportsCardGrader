import { useState } from 'react'
import { loadSettings, saveSettings } from '../storage'
import type { Provider } from '../types'

export default function SettingsScreen({ onDone }: { onDone: () => void }) {
  const existing = loadSettings()
  const [provider, setProvider] = useState<Provider>(existing?.provider ?? 'anthropic')
  const [apiKey, setApiKey] = useState(existing?.apiKey ?? '')

  return (
    <div className="screen">
      <h2>Bring your own AI</h2>
      <p>
        Scans run on your own AI account. Your key is stored only on this device and sent only to
        your chosen provider.
      </p>
      <label>
        Provider
        <select value={provider} onChange={e => setProvider(e.target.value as Provider)}>
          <option value="anthropic">Anthropic (Claude)</option>
          <option value="openai">OpenAI</option>
        </select>
      </label>
      <label>
        API key
        <input
          type="password"
          value={apiKey}
          placeholder="sk-..."
          onChange={e => setApiKey(e.target.value)}
        />
      </label>
      <button
        disabled={!apiKey}
        onClick={() => {
          saveSettings({ provider, apiKey })
          onDone()
        }}
      >
        Save
      </button>
    </div>
  )
}
