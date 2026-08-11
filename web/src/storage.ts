import type { AiSettings, HistoryEntry } from './types'

const SETTINGS_KEY = 'cardscanner.settings'
const HISTORY_KEY = 'cardscanner.history'
export const HISTORY_LIMIT = 50

function read<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    return null
  }
}

export const loadSettings = () => read<AiSettings>(SETTINGS_KEY)
export const saveSettings = (s: AiSettings) => localStorage.setItem(SETTINGS_KEY, JSON.stringify(s))
export const loadHistory = () => read<HistoryEntry[]>(HISTORY_KEY) ?? []
export function pushHistory(entry: HistoryEntry) {
  const next = [entry, ...loadHistory()].slice(0, HISTORY_LIMIT)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(next))
}
