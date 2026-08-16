import { act, render, screen, fireEvent } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import ScanOverlay from './ScanOverlay'

beforeEach(() => vi.useFakeTimers())
afterEach(() => vi.useRealTimers())

test('renders as a status region with thumbnail, caption and spinner', () => {
  render(<ScanOverlay previewUrl="blob:front" onCancel={() => {}} />)
  const overlay = screen.getByRole('status')
  expect(overlay).toBeDefined()
  expect(screen.getByAltText(/card being scanned/i).getAttribute('src')).toBe('blob:front')
  expect(screen.getByText(/usually takes 10–20 seconds/i)).toBeDefined()
})

test('staged copy progresses on a timer', () => {
  render(<ScanOverlay previewUrl={null} onCancel={() => {}} />)
  expect(screen.getByText('Reading the card…')).toBeDefined()

  act(() => vi.advanceTimersByTime(4000))
  expect(screen.queryByText('Reading the card…')).toBeNull()
  expect(screen.getByText('Estimating condition…')).toBeDefined()

  act(() => vi.advanceTimersByTime(4000))
  expect(screen.getByText('Checking recent sales…')).toBeDefined()

  // Final stage holds — no further copy changes however long the scan runs.
  act(() => vi.advanceTimersByTime(60_000))
  expect(screen.getByText('Checking recent sales…')).toBeDefined()
})

test('cancel button calls onCancel', () => {
  const onCancel = vi.fn()
  render(<ScanOverlay previewUrl={null} onCancel={onCancel} />)
  fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
  expect(onCancel).toHaveBeenCalledOnce()
})

test('no thumbnail rendered when previewUrl is null', () => {
  render(<ScanOverlay previewUrl={null} onCancel={() => {}} />)
  expect(screen.queryByAltText(/card being scanned/i)).toBeNull()
})
