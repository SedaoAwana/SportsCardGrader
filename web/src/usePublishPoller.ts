// Keeps staged cards in sync with the server's publish queue: polls pending
// jobs, re-submits consented-but-unsent publishes when connectivity returns.

import { useEffect, useState } from 'react'
import { getPublishStatus, resumePendingPublishes } from './binderApi'
import { setStatus } from './binderDb'
import type { PublishJobStatus, StagedCard, StagedStatus } from './binderTypes'

export const PUBLISH_POLL_MS = 30_000

const JOB_TO_STAGED: Record<PublishJobStatus['status'], StagedStatus> = {
  queued: 'queued',
  publishing: 'publishing',
  confirmed: 'published',
  failed: 'failed',
}

export function usePublishPoller(
  staged: StagedCard[] | null,
  refresh: () => void,
): Record<string, PublishJobStatus> {
  const [jobs, setJobs] = useState<Record<string, PublishJobStatus>>({})

  useEffect(() => {
    let cancelled = false

    async function poll() {
      const pending = (staged ?? []).filter(
        c => (c.status === 'queued' || c.status === 'publishing') && c.job_id)
      let changed = false
      const seen: Record<string, PublishJobStatus> = {}
      for (const card of pending) {
        try {
          const job = await getPublishStatus(card.job_id!)
          seen[card.record_id] = job
          const status = JOB_TO_STAGED[job.status]
          if (status !== card.status || (job.hive_url ?? undefined) !== card.hive_url) {
            await setStatus(card.record_id, {
              status,
              permlink: job.permlink,
              hive_url: job.hive_url ?? undefined,
              error: job.last_error ?? undefined,
            })
            changed = true
          }
        } catch {
          // Server unreachable — the next cycle will catch up.
        }
      }
      if (cancelled) return
      if (Object.keys(seen).length) setJobs(prev => ({ ...prev, ...seen }))
      if (changed) refresh()
    }

    // Startup sweep first (offline publishes from a previous session), then poll.
    resumePendingPublishes().catch(() => {}).then(() => { if (!cancelled) poll() })
    const timer = setInterval(poll, PUBLISH_POLL_MS)
    const onOnline = () => { resumePendingPublishes().catch(() => {}).then(refresh) }
    window.addEventListener('online', onOnline)
    return () => {
      cancelled = true
      clearInterval(timer)
      window.removeEventListener('online', onOnline)
    }
  }, [staged, refresh])

  return jobs
}
