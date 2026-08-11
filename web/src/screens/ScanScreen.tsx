import { useState } from 'react'

interface Props {
  onSubmit: (front: File, back: File | null, askingPrice: number | null) => void
  busy: boolean
}

export default function ScanScreen({ onSubmit, busy }: Props) {
  const [front, setFront] = useState<File | null>(null)
  const [back, setBack] = useState<File | null>(null)
  const [ask, setAsk] = useState('')

  return (
    <div className="screen">
      <label className="capture">
        {front ? <img src={URL.createObjectURL(front)} alt="card front" /> : 'Tap to photograph card front'}
        <input type="file" accept="image/*" capture="environment" hidden
               onChange={e => setFront(e.target.files?.[0] ?? null)} />
      </label>
      <label className="capture small">
        {back ? <img src={URL.createObjectURL(back)} alt="card back" /> : '+ back (optional)'}
        <input type="file" accept="image/*" capture="environment" hidden
               onChange={e => setBack(e.target.files?.[0] ?? null)} />
      </label>
      <label>
        Asking price (optional)
        <input type="number" inputMode="decimal" placeholder="$" value={ask}
               onChange={e => setAsk(e.target.value)} />
      </label>
      <button disabled={!front || busy}
              onClick={() => onSubmit(front!, back, ask ? Number(ask) : null)}>
        {busy ? 'Scanning…' : 'Scan card'}
      </button>
    </div>
  )
}
