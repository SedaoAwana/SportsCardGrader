import type { VerdictLabel } from './types'

// Human-facing verdict badge text. Raw enum values stay in CSS classes (verdict-no_ask etc.).
export const verdictLabels: Record<VerdictLabel, string> = {
  undervalued: 'Undervalued',
  fair: 'Fair price',
  overpriced: 'Overpriced',
  no_ask: 'Value estimate',
  not_enough_data: 'Not enough data',
  authenticity_risk: 'Caution: authenticity',
  low_value: 'Too cheap to call',
  high_value: 'High value — verify first',
}
