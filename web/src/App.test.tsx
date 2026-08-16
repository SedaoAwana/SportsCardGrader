import { render, screen, fireEvent } from '@testing-library/react'
import { beforeAll, beforeEach, expect, test, vi } from 'vitest'
import App from './App'
import { ApiError } from './api'
import { loadHistory, saveSettings } from './storage'
import type { ScanResponse } from './types'

const mocks = vi.hoisted(() => ({ scanCard: vi.fn(), prepareImage: vi.fn() }))

// Keep the health check quiet in tests (healthy server -> no banner, no state update).
vi.mock('./api', async importOriginal => ({
  ...(await importOriginal<typeof import('./api')>()),
  checkHealth: () => Promise.resolve(true),
  scanCard: mocks.scanCard,
}))

// Real prepareImage needs canvas/createImageBitmap (absent in jsdom); pass through.
vi.mock('./imagePrep', () => ({ prepareImage: mocks.prepareImage }))

// jsdom does not implement object URLs; the front-photo preview creates and revokes them.
beforeAll(() => {
  URL.createObjectURL = vi.fn(() => 'blob:mock')
  URL.revokeObjectURL = vi.fn()
})

beforeEach(() => {
  localStorage.clear()
  mocks.scanCard.mockReset()
  mocks.prepareImage.mockReset().mockImplementation((f: File) => Promise.resolve(f))
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
  // Real ResultsScreen: stubResponse has no verdict, so value is unavailable.
  await screen.findByText(/market value unavailable/i)
  expect(screen.getByRole('button', { name: /scan another/i })).toBeDefined()
  expect(loadHistory()).toHaveLength(1)
  expect(mocks.scanCard).toHaveBeenCalledOnce()
})

test('images are prepared before upload; scanCard gets the prepared files', async () => {
  saveSettings({ provider: 'anthropic', apiKey: 'sk-test' })
  mocks.scanCard.mockResolvedValue(stubResponse)
  const rawFront = new File(['raw-front'], 'front.heic', { type: 'image/heic' })
  const rawBack = new File(['raw-back'], 'back.heic', { type: 'image/heic' })
  const prepFront = new File(['prep-front'], 'front.jpg', { type: 'image/jpeg' })
  const prepBack = new File(['prep-back'], 'back.jpg', { type: 'image/jpeg' })
  mocks.prepareImage.mockImplementation((f: File) =>
    Promise.resolve(f === rawFront ? prepFront : prepBack))

  render(<App />)
  fireEvent.change(screen.getByLabelText(/photograph card front/i), {
    target: { files: [rawFront] },
  })
  fireEvent.change(screen.getByLabelText(/back \(optional\)/i), {
    target: { files: [rawBack] },
  })
  fireEvent.click(screen.getByRole('button', { name: /scan card/i }))

  await screen.findByText(/market value unavailable/i)
  expect(mocks.prepareImage).toHaveBeenCalledTimes(2)
  expect(mocks.prepareImage).toHaveBeenCalledWith(rawFront)
  expect(mocks.prepareImage).toHaveBeenCalledWith(rawBack)
  expect(mocks.scanCard).toHaveBeenCalledWith(prepFront, prepBack, null, expect.anything())
})

test('front-only scan prepares just the front image', async () => {
  saveSettings({ provider: 'anthropic', apiKey: 'sk-test' })
  mocks.scanCard.mockResolvedValue(stubResponse)
  render(<App />)
  pickFrontAndScan()
  await screen.findByText(/market value unavailable/i)
  expect(mocks.prepareImage).toHaveBeenCalledTimes(1)
  expect(mocks.scanCard).toHaveBeenCalledWith(
    mocks.prepareImage.mock.calls[0][0], null, null, expect.anything())
})

test('submit without settings redirects to settings view', () => {
  // No saved settings: App opens on settings; user navigates to scan anyway.
  render(<App />)
  fireEvent.click(screen.getByRole('button', { name: 'Scan' }))
  pickFrontAndScan()
  expect(screen.getByText(/bring your own ai/i)).toBeDefined()
  expect(mocks.scanCard).not.toHaveBeenCalled()
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
