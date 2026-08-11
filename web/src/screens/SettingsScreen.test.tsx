import { render, screen, fireEvent } from '@testing-library/react'
import { beforeEach, expect, test } from 'vitest'
import SettingsScreen from './SettingsScreen'
import { loadSettings } from '../storage'

beforeEach(() => localStorage.clear())

test('saves provider and key', () => {
  render(<SettingsScreen onDone={() => {}} />)
  fireEvent.change(screen.getByLabelText(/provider/i), { target: { value: 'openai' } })
  fireEvent.change(screen.getByLabelText(/api key/i), { target: { value: 'sk-test' } })
  fireEvent.click(screen.getByRole('button', { name: /save/i }))
  expect(loadSettings()).toMatchObject({ provider: 'openai', apiKey: 'sk-test' })
})
