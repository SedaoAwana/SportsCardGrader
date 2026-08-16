// Mirrors server/app/hive/record.py field-for-field (snake_case, matching
// the JSON embedded in a Binder post's json_metadata.card).

import type {
  Authenticity,
  CompListing,
  CompsSummary,
  Condition,
  Identity,
  ScanResponse,
  Slab,
  Verdict,
} from './types'

export interface CardComps {
  summary: CompsSummary
  top_sales: CompListing[]
  as_of: string
}

export interface CardImages {
  front: string // images.hive.blog URL
  back: string | null
}

export interface Attribution {
  client_id: string // anonymous per-install UUID; never an identity claim
  display_name: string | null
}

export interface CardRecord {
  v: 1
  kind: 'card'
  record_id: string
  identity: Identity
  condition: Condition | null
  slab: Slab | null
  authenticity: Authenticity | null
  verdict: Verdict | null
  comps: CardComps | null
  images: CardImages
  asking_price: number | null
  attribution: Attribution
  scanned_at: string
}

// What POST /api/publish accepts: the record before images are uploaded.
export type CardRecordDraft = Omit<CardRecord, 'images'>

// Client-only staging types

export type StagedStatus =
  | 'draft'
  | 'queued'
  | 'publishing'
  | 'published'
  | 'failed'

export interface StagedCard {
  record_id: string
  at: string // ISO timestamp of the scan
  response: ScanResponse
  askingPrice?: number
  status: StagedStatus
  publishRequested?: boolean // user consented; retry on reconnect
  permlink?: string
  hive_url?: string
  job_id?: string
  error?: string
  legacy?: boolean // migrated from localStorage — has no images, can't publish
}

export interface PublishJobStatus {
  job_id: string
  permlink: string
  status: 'queued' | 'publishing' | 'confirmed' | 'failed'
  position: number
  eta_seconds: number
  hive_url: string | null
  last_error: string | null
}

export interface BinderCard {
  permlink: string
  author: string
  created: string | null
  card: CardRecord
  hive_url?: string
}

export interface HiveStatus {
  configured: boolean
  account?: string
  community?: string
  dry_run?: boolean
  rc_percent?: number | null
  queue_depth?: number
  eta_seconds?: number
}
