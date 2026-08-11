import { useEffect, useMemo, useState } from 'react'

interface Props {
  onSubmit: (front: File, back: File | null, askingPrice: number | null) => void
  busy: boolean
}

// Stable preview URL per file; revoked when the file changes or on unmount.
function useObjectUrl(file: File | null) {
  const url = useMemo(() => (file ? URL.createObjectURL(file) : null), [file])
  useEffect(() => () => { if (url) URL.revokeObjectURL(url) }, [url])
  return url
}

export default function ScanScreen({ onSubmit, busy }: Props) {
  const [front, setFront] = useState<File | null>(null)
  const [back, setBack] = useState<File | null>(null)
  const [ask, setAsk] = useState('')
  const frontUrl = useObjectUrl(front)
  const backUrl = useObjectUrl(back)

  return (
    <div className="screen">
      <label className="capture">
        {frontUrl ? <img src={frontUrl} alt="card front" /> : 'Tap to photograph card front'}
        <input type="file" accept="image/*" capture="environment" hidden
               onChange={e => setFront(e.target.files?.[0] ?? null)} />
      </label>
      <label className="capture small">
        {backUrl ? <img src={backUrl} alt="card back" /> : '+ back (optional)'}
        <input type="file" accept="image/*" capture="environment" hidden
               onChange={e => setBack(e.target.files?.[0] ?? null)} />
      </label>
      <label>
        Asking price (optional)
        <input type="number" inputMode="decimal" min="0" placeholder="$" value={ask}
               onChange={e => setAsk(e.target.value)} />
      </label>
      <button disabled={!front || busy}
              onClick={() => onSubmit(front!, back, ask ? Number(ask) : null)}>
        {busy ? 'Scanning…' : 'Scan card'}
      </button>
    </div>
  )
}
