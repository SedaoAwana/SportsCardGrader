import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, expect, test, vi } from 'vitest'
import HistoryScreen from './HistoryScreen'
import { pushHistory } from '../storage'
import type { HistoryEntry, ScanResponse } from '../types'

beforeEach(() => {
  localStorage.clear()
})

const response: ScanResponse = {
  vision: {
    photo_ok: true, photo_issue: null,
    identity: { player: 'Luka Doncic', year: '2018', set_name: 'Panini Prizm',
                card_number: '280', variant: null,
                search_string: '2018 Panini Prizm Luka Doncic #280', confidence: 0.92 },
    condition: { observations: [], grade_low: 6, grade_high: 8 },
    authenticity: { red_flags: [], risk: 'low' }, ai_value_note: null,
  },
  comps: null,
  comps_error: null,
  verdict: { value_low: 60, value_high: 90, verdict: 'undervalued', reasoning: 'Cheap!' },
}

test('empty state shows "No scans yet."', () => {
  render(<HistoryScreen onSelect={() => {}} />)
  expect(screen.getByText(/no scans yet/i)).toBeTruthy()
})

test('renders a row and onSelect fires with the entry', () => {
  const entry: HistoryEntry = { at: '2026-08-06T12:00:00.000Z', response, askingPrice: 50 }
  pushHistory(entry)
  const onSelect = vi.fn()
  render(<HistoryScreen onSelect={onSelect} />)
  const row = screen.getByText(/Luka Doncic/)
  expect(screen.getByText('Undervalued')).toBeTruthy() // human label, not raw enum
  fireEvent.click(row)
  expect(onSelect).toHaveBeenCalledOnce()
  expect(onSelect.mock.calls[0][0]).toEqual(entry)
})

test('row without identity shows "Unreadable photo"', () => {
  const bad: ScanResponse = {
    vision: { photo_ok: false, photo_issue: 'blur', identity: null,
              condition: null, authenticity: null, ai_value_note: null },
    comps: null, comps_error: null, verdict: null,
  }
  pushHistory({ at: '2026-08-06T12:00:00.000Z', response: bad })
  render(<HistoryScreen onSelect={() => {}} />)
  expect(screen.getByText(/unreadable photo/i)).toBeTruthy()
})
