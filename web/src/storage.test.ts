import { beforeEach, expect, test } from 'vitest'
import { loadSettings, saveSettings, loadHistory, pushHistory, HISTORY_LIMIT } from './storage'

beforeEach(() => localStorage.clear())

test('settings round-trip', () => {
  expect(loadSettings()).toBeNull()
  saveSettings({ provider: 'anthropic', apiKey: 'sk-x' })
  expect(loadSettings()?.apiKey).toBe('sk-x')
})

test('history caps at limit, newest first', () => {
  for (let i = 0; i < HISTORY_LIMIT + 5; i++) {
    pushHistory({ at: `t${i}`, response: { vision: { photo_ok: false } } as never })
  }
  const h = loadHistory()
  expect(h.length).toBe(HISTORY_LIMIT)
  expect(h[0].at).toBe(`t${HISTORY_LIMIT + 4}`)
})

test('corrupt storage returns empty, not crash', () => {
  localStorage.setItem('cardscanner.history', '{not json')
  expect(loadHistory()).toEqual([])
})
