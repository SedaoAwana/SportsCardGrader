import { afterEach, expect, test, vi } from 'vitest'
import { scanCard, checkHealth, ApiError, SCAN_TIMEOUT_MS } from './api'

const settings = { provider: 'anthropic' as const, apiKey: 'sk-x' }
const file = new File(['x'], 'card.jpg', { type: 'image/jpeg' })

afterEach(() => vi.restoreAllMocks())

test('posts multipart with AI headers', async () => {
  const mock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify({ vision: { photo_ok: false } }), { status: 200 }))
  await scanCard(file, null, 30, settings)
  const [url, init] = mock.mock.calls[0]
  expect(String(url)).toContain('/api/scan')
  expect((init!.headers as Record<string, string>)['X-AI-Key']).toBe('sk-x')
  expect(init!.body).toBeInstanceOf(FormData)
})

test('maps 401 to a settings hint', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify({ detail: 'Your AI provider rejected the API key. Check it in Settings.' }),
      { status: 401 }))
  await expect(scanCard(file, null, null, settings)).rejects.toThrow(/Settings/)
})

test('network failure gives readable error', async () => {
  vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('fetch failed'))
  await expect(scanCard(file, null, null, settings)).rejects.toThrow(ApiError)
})

test('exports a scan timeout budget of 90s', () => {
  expect(SCAN_TIMEOUT_MS).toBe(90_000)
})

test('scanCard forwards the abort signal to fetch', async () => {
  const mock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify({ vision: { photo_ok: false } }), { status: 200 }))
  const controller = new AbortController()
  await scanCard(file, null, null, settings, controller.signal)
  expect(mock.mock.calls[0][1]!.signal).toBe(controller.signal)
})

test('scanCard rethrows abort/timeout DOMExceptions untouched', async () => {
  // The caller tells user-cancel apart from timeout by exception name;
  // wrapping these in ApiError would erase that.
  vi.spyOn(globalThis, 'fetch').mockRejectedValue(new DOMException('gone', 'AbortError'))
  await expect(scanCard(file, null, null, settings)).rejects.toSatisfy(
    (e: unknown) => e instanceof DOMException && e.name === 'AbortError')
  vi.spyOn(globalThis, 'fetch').mockRejectedValue(new DOMException('slow', 'TimeoutError'))
  await expect(scanCard(file, null, null, settings)).rejects.toSatisfy(
    (e: unknown) => e instanceof DOMException && e.name === 'TimeoutError')
})

test('checkHealth fetches with a timeout signal', async () => {
  const mock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify({ status: 'ok' }), { status: 200 }))
  await checkHealth()
  expect(mock.mock.calls[0][1]!.signal).toBeInstanceOf(AbortSignal)
})

test('checkHealth true when server responds ok', async () => {
  const mock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify({ status: 'ok' }), { status: 200 }))
  await expect(checkHealth()).resolves.toBe(true)
  expect(String(mock.mock.calls[0][0])).toContain('/api/health')
})

test('checkHealth false on network error', async () => {
  vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('fetch failed'))
  await expect(checkHealth()).resolves.toBe(false)
})
