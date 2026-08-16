import { afterEach, describe, expect, test, vi } from 'vitest'
import { prepareImage, targetDimensions } from './imagePrep'

// jsdom has no real canvas or image decoder, so the decode/encode pipeline is
// exercised through stubs: createImageBitmap, Image, and document.createElement
// ('canvas') are mocked. The scaling arithmetic itself is a pure function
// (targetDimensions) tested directly with real numbers.

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('targetDimensions', () => {
  test('landscape over the limit scales long edge to max', () => {
    expect(targetDimensions(4000, 3000)).toEqual({ width: 1600, height: 1200 })
  })

  test('portrait over the limit scales long edge to max', () => {
    expect(targetDimensions(3000, 4000)).toEqual({ width: 1200, height: 1600 })
  })

  test('small image is never upscaled', () => {
    expect(targetDimensions(800, 600)).toEqual({ width: 800, height: 600 })
  })

  test('exactly at the limit is left unchanged', () => {
    expect(targetDimensions(1600, 1200)).toEqual({ width: 1600, height: 1200 })
  })
})

describe('prepareImage', () => {
  test('small jpeg shortcut: returns the same File without decoding', async () => {
    const createImageBitmap = vi.fn()
    vi.stubGlobal('createImageBitmap', createImageBitmap)
    const file = new File(['tiny'], 'small.jpg', { type: 'image/jpeg' })

    await expect(prepareImage(file)).resolves.toBe(file)
    expect(createImageBitmap).not.toHaveBeenCalled()
  })

  test('decode failure on both paths returns the original file (never throws)', async () => {
    vi.stubGlobal('createImageBitmap', vi.fn().mockRejectedValue(new Error('unsupported format')))
    // Fallback HTMLImageElement also fails to decode (e.g. true HEIC, no OS decoder).
    vi.stubGlobal('Image', class {
      onload: (() => void) | null = null
      onerror: (() => void) | null = null
      set src(_: string) {
        queueMicrotask(() => this.onerror?.())
      }
    })
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL: vi.fn(() => 'blob:mock'),
      revokeObjectURL: vi.fn(),
    })
    const file = new File(['heic-bytes'], 'photo.heic', { type: 'image/heic' })

    await expect(prepareImage(file)).resolves.toBe(file)
  })

  test('re-encodes oversized image to a scaled jpeg File with .jpg name', async () => {
    const close = vi.fn()
    vi.stubGlobal(
      'createImageBitmap',
      vi.fn().mockResolvedValue({ width: 4000, height: 3000, close }),
    )
    const drawImage = vi.fn()
    const jpegBlob = new Blob(['jpeg-bytes'], { type: 'image/jpeg' })
    const fakeCanvas = {
      width: 0,
      height: 0,
      getContext: vi.fn(() => ({ drawImage })),
      toBlob: vi.fn((cb: (b: Blob | null) => void, type: string, quality: number) => {
        expect(type).toBe('image/jpeg')
        expect(quality).toBe(0.85)
        cb(jpegBlob)
      }),
    }
    const realCreateElement = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag: string) =>
      tag === 'canvas' ? (fakeCanvas as unknown as HTMLCanvasElement) : realCreateElement(tag),
    )
    const file = new File(['heic-bytes'], 'photo.heic', { type: 'image/heic' })

    const out = await prepareImage(file)

    expect(out).not.toBe(file)
    expect(out.type).toBe('image/jpeg')
    expect(out.name).toBe('photo.jpg')
    expect(fakeCanvas.width).toBe(1600)
    expect(fakeCanvas.height).toBe(1200)
    expect(drawImage).toHaveBeenCalledWith(expect.anything(), 0, 0, 1600, 1200)
    expect(close).toHaveBeenCalled()
  })

  test('toBlob yielding null falls back to the original file', async () => {
    vi.stubGlobal(
      'createImageBitmap',
      vi.fn().mockResolvedValue({ width: 4000, height: 3000, close: vi.fn() }),
    )
    const fakeCanvas = {
      width: 0,
      height: 0,
      getContext: vi.fn(() => ({ drawImage: vi.fn() })),
      toBlob: (cb: (b: Blob | null) => void) => cb(null),
    }
    const realCreateElement = document.createElement.bind(document)
    vi.spyOn(document, 'createElement').mockImplementation((tag: string) =>
      tag === 'canvas' ? (fakeCanvas as unknown as HTMLCanvasElement) : realCreateElement(tag),
    )
    const file = new File(['x'], 'big.png', { type: 'image/png' })

    await expect(prepareImage(file)).resolves.toBe(file)
  })
})
