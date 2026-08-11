import { render, screen, fireEvent } from '@testing-library/react'
import { beforeEach, expect, test, vi } from 'vitest'
import App from './App'
import { saveSettings } from './storage'

// Keep the health check quiet in tests (healthy server -> no banner, no state update).
vi.mock('./api', () => ({ checkHealth: () => Promise.resolve(true) }))

beforeEach(() => localStorage.clear())

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
  expect(screen.getByText(/coming soon/i)).toBeDefined()
  fireEvent.click(screen.getByRole('button', { name: 'Settings' }))
  expect(screen.getByText(/bring your own ai/i)).toBeDefined()
  fireEvent.click(screen.getByRole('button', { name: 'Scan' }))
  expect(screen.getByText(/coming soon/i)).toBeDefined()
})
