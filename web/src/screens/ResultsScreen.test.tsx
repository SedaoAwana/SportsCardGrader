import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import ResultsScreen from './ResultsScreen'
import type { ScanResponse } from '../types'

const base: ScanResponse = {
  vision: {
    photo_ok: true, photo_issue: null,
    identity: { player: 'Luka Doncic', year: '2018', set_name: 'Panini Prizm',
                card_number: '280', variant: null,
                search_string: '2018 Panini Prizm Luka Doncic #280', confidence: 0.92 },
    condition: { observations: [], grade_low: 6, grade_high: 8 },
    authenticity: { red_flags: [], risk: 'low' }, ai_value_note: null,
  },
  comps: { source: 'active_listings', raw_count: 4, raw_low: 60, raw_median: 90,
           graded_count: 0, graded_low: null, graded_median: null },
  comps_error: null,
  verdict: { value_low: 60, value_high: 90, verdict: 'undervalued', reasoning: 'Cheap!' },
}

test('shows identity, grade range, and verdict', () => {
  render(<ResultsScreen result={base} onRescan={() => {}} />)
  expect(screen.getByText(/Luka Doncic/)).toBeTruthy()
  expect(screen.getByText(/PSA 6–8/)).toBeTruthy()
  expect(screen.getByText(/undervalued/i)).toBeTruthy()
})

test('bad photo shows retake prompt', () => {
  const r: ScanResponse = { vision: { photo_ok: false, photo_issue: 'too much glare',
    identity: null, condition: null, authenticity: null, ai_value_note: null },
    comps: null, comps_error: null, verdict: null }
  render(<ResultsScreen result={r} onRescan={() => {}} />)
  expect(screen.getByText(/glare/)).toBeTruthy()
  expect(screen.getByRole('button', { name: /retake/i })).toBeTruthy()
})

test('comps failure still shows grade with value unavailable', () => {
  const r = { ...base, comps: null, verdict: null, comps_error: 'eBay down' }
  render(<ResultsScreen result={r} onRescan={() => {}} />)
  expect(screen.getByText(/PSA 6–8/)).toBeTruthy()
  expect(screen.getByText(/value unavailable/i)).toBeTruthy()
})

test('authenticity red flags surface prominently', () => {
  const r = structuredClone(base)
  r.vision.authenticity = { red_flags: ['print pattern looks off'], risk: 'high' }
  render(<ResultsScreen result={r} onRescan={() => {}} />)
  expect(screen.getByText(/print pattern looks off/)).toBeTruthy()
})

test('half grades render without trailing zeros', () => {
  const r = structuredClone(base)
  r.vision.condition = { observations: [], grade_low: 6.5, grade_high: 8.5 }
  render(<ResultsScreen result={r} onRescan={() => {}} />)
  expect(screen.getByText(/PSA 6\.5–8\.5/)).toBeTruthy()
})

test('low-confidence identity shows uncertainty warning', () => {
  const r = structuredClone(base)
  r.vision.identity!.confidence = 0.4
  render(<ResultsScreen result={r} onRescan={() => {}} />)
  expect(screen.getByText(/identification uncertain — price may not be reliable/i)).toBeTruthy()
})

test('verdict badge shows human label, not raw enum value', () => {
  const r = structuredClone(base)
  r.verdict = { value_low: 60, value_high: 90, verdict: 'no_ask', reasoning: 'No asking price given.' }
  render(<ResultsScreen result={r} onRescan={() => {}} />)
  expect(screen.getByText('Value estimate')).toBeTruthy()
  expect(screen.queryByText('no_ask')).toBeNull()
})
