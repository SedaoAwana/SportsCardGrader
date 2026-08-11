import type { AiSettings, ScanResponse } from './types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {}

export async function scanCard(front: File, back: File | null,
                               askingPrice: number | null,
                               settings: AiSettings): Promise<ScanResponse> {
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
    resp = await fetch(`${API_BASE}/api/scan`, { method: 'POST', body: form, headers })
  } catch {
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
    const resp = await fetch(`${API_BASE}/api/health`)
    return resp.ok
  } catch {
    return false
  }
}
