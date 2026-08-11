import { render, screen, fireEvent } from '@testing-library/react'
import { beforeAll, expect, test, vi } from 'vitest'
import ScanScreen from './ScanScreen'

// jsdom does not implement URL.createObjectURL; the preview <img> needs it.
beforeAll(() => {
  URL.createObjectURL = vi.fn(() => 'blob:mock')
})

test('scan button is disabled until a front photo is chosen', () => {
  render(<ScanScreen onSubmit={() => {}} busy={false} />)
  const button = screen.getByRole('button', { name: /scan card/i }) as HTMLButtonElement
  expect(button.disabled).toBe(true)

  fireEvent.change(screen.getByLabelText(/photograph card front/i), {
    target: { files: [new File(['x'], 'front.jpg', { type: 'image/jpeg' })] },
  })
  expect(button.disabled).toBe(false)
  expect(screen.getByAltText('card front')).toBeDefined()
})

test('busy prop shows Scanning… and disables the button', () => {
  render(<ScanScreen onSubmit={() => {}} busy />)
  const button = screen.getByRole('button', { name: /scanning/i }) as HTMLButtonElement
  expect(button.disabled).toBe(true)
})
