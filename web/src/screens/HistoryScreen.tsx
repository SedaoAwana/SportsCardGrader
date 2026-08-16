import { verdictLabels } from '../labels'
import { loadHistory } from '../storage'
import type { HistoryEntry } from '../types'

interface Props {
  onSelect: (entry: HistoryEntry) => void
}

export default function HistoryScreen({ onSelect }: Props) {
  const history = loadHistory()

  if (history.length === 0) {
    return (
      <div className="screen">
        <p>No scans yet.</p>
      </div>
    )
  }

  return (
    <div className="screen">
      <ul className="history">
        {history.map((entry, i) => {
          const verdict = entry.response.verdict
          const slab = entry.response.vision.slab
          return (
            <li key={`${entry.at}-${i}`}>
              <button className="history-row" onClick={() => onSelect(entry)}>
                <span className="player">
                  {entry.response.vision.identity?.player ?? 'Unreadable photo'}
                  {slab ? ` · ${slab.company} ${slab.grade}` : ''}
                </span>
                <span className="date">{new Date(entry.at).toLocaleDateString()}</span>
                {verdict && (
                  <span className={`verdict verdict-${verdict.verdict}`}>{verdictLabels[verdict.verdict]}</span>
                )}
                {entry.askingPrice != null && <span className="ask">${entry.askingPrice}</span>}
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
