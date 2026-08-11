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
        {history.map(entry => {
          const verdict = entry.response.verdict
          return (
            <li key={entry.at}>
              <button className="history-row" onClick={() => onSelect(entry)}>
                <span className="player">
                  {entry.response.vision.identity?.player ?? 'Unreadable photo'}
                </span>
                <span className="date">{new Date(entry.at).toLocaleDateString()}</span>
                {verdict && (
                  <span className={`verdict verdict-${verdict.verdict}`}>{verdict.verdict}</span>
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
