import { render, screen, fireEvent } from '@testing-library/react'
import { beforeAll, beforeEach, expect, test, vi } from 'vitest'
import App from './App'
import { ApiError } from './api'
import { loadHistory, saveSettings } from './storage'
import type { ScanResponse } from './types'

const mocks = vi.hoisted(() => ({ scanCard: vi.fn() }))

// Keep the health check quiet in tests (healthy server -> no banner, no state update).
vi.mock('./api', async importOriginal => ({
  ...(await importOriginal<typeof import('./api')>()),
  checkHealth: () => Promise.resolve(true),
  scanCard: mocks.scanCard,
}))

// jsdom does not implement URL.createObjectURL; the front-photo preview needs it.
beforeAll(() => {
  URL.createObjectURL = vi.fn(() => 'blob:mock')
})

beforeEach(() => {
  localStorage.clear()
  mocks.scanCard.mockReset()
})

const stubResponse: ScanResponse = {
  vision: {
    photo_ok: true,
    photo_issue: null,
    identity: null,
    condition: null,
    authenticity: null,
    ai_value_note: null,
  },
  comps: null,
  comps_error: null,
  verdict: null,
}

function pickFrontAndScan() {
  fireEvent.change(screen.getByLabelText(/photograph card front/i), {
    target: { files: [new File(['x'], 'f.jpg', { type: 'image/jpeg' })] },
  })
  fireEvent.click(screen.getByRole('button', { name: /scan card/i }))
}

test('renders header title', () => {
  render(<App />)
  expect(screen.getByRole('heading', { name: 'Card Scanner' })).toBeDefined()
})

test('first run forces settings view when no settings saved', () => {
  render(<App />)
  expect(screen.getByText(/bring your own ai/i)).toBeDefined()
})

test('shows scan view when settings exist, nav switches views', () => {
  saveSettings({ provider: 'anthropic', apiKey: 'sk-test' })
  render(<App />)
  expect(screen.getByText(/photograph card front/i)).toBeDefined()
  fireEvent.click(screen.getByRole('button', { name: 'Settings' }))
  expect(screen.getByText(/bring your own ai/i)).toBeDefined()
  fireEvent.click(screen.getByRole('button', { name: 'Scan' }))
  expect(screen.getByText(/photograph card front/i)).toBeDefined()
})

test('successful scan pushes history and switches to results', async () => {
  saveSettings({ provider: 'anthropic', apiKey: 'sk-test' })
  mocks.scanCard.mockResolvedValue(stubResponse)
  render(<App />)
  pickFrontAndScan()
  await screen.findByText(/result ready/i)
  expect(loadHistory()).toHaveLength(1)
  expect(mocks.scanCard).toHaveBeenCalledOnce()
})

test('failed scan shows dismissible error and stays on scan view', async () => {
  saveSettings({ provider: 'anthropic', apiKey: 'sk-test' })
  mocks.scanCard.mockRejectedValue(new ApiError('Scan failed (500). Try again.'))
  render(<App />)
  pickFrontAndScan()
  const alert = await screen.findByRole('alert')
  expect(alert.textContent).toContain('Scan failed (500). Try again.')
  // Still on the scan view.
  expect(screen.getByRole('button', { name: /scan card/i })).toBeDefined()
  fireEvent.click(screen.getByRole('button', { name: 'Dismiss' }))
  expect(screen.queryByRole('alert')).toBeNull()
})
