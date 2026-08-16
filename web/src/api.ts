import type { AiSettings, ScanResponse } from './types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {}

// Client-side budget for the whole scan round-trip. Comfortably above the
// server's own 55s pipeline budget, so the server's 504 (with its more
// specific message) normally wins; this is the backstop for a dead network.
export const SCAN_TIMEOUT_MS = 90_000

export async function scanCard(front: File, back: File | null,
                               askingPrice: number | null,
                               settings: AiSettings,
                               signal?: AbortSignal): Promise<ScanResponse> {
  const form = new FormData()
  form.append('front', front)
  if (back) form.append('back', back)
  if (askingPrice != null) form.append('asking_price', String(askingPrice))

  const headers: Record<string, string> = {
    'X-AI-Provider': settings.provider,
    'X-AI-Key': settings.apiKey,
  }
  if (settings.model) headers['X-AI-Model'] = settings.model

  let resp: Response
  try {
    resp = await fetch(`${API_BASE}/api/scan`, { method: 'POST', body: form, headers, signal })
  } catch (err) {
    // Rethrow aborts untouched: the caller tells user-cancel (AbortError)
    // apart from timeout (TimeoutError) by the exception name.
    if (err instanceof DOMException &&
        (err.name === 'AbortError' || err.name === 'TimeoutError')) throw err
    throw new ApiError('Could not reach the scan server. Check your connection.')
  }
  if (!resp.ok) {
    const detail = await resp.json().then(b => b.detail).catch(() => null)
    throw new ApiError(detail ?? `Scan failed (${resp.status}). Try again.`)
  }
  return resp.json()
}

export async function checkHealth(): Promise<boolean> {
  try {
    // Health is instant server-side; if 5s pass the server is effectively down.
    const resp = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(5000) })
    return resp.ok
  } catch {
    return false
  }
}
