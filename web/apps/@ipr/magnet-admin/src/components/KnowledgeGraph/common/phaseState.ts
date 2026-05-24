import type { KgPhaseState } from './KgPhasePill.vue'

export type PhaseStatsLike = {
  completed: number
  failed: number
  running: number
  pending: number
  total: number
}

/**
 * Map aggregate phase counts to a single visual state.
 *
 * A phase is ``not_run`` when no document has entered it (the backend now
 * excludes untouched documents from the per-phase totals for metadata and
 * entity extraction). A phase is only ``pending`` when there are real pending
 * documents — never as a fallback for "nothing has happened yet".
 */
export function phaseStateFor(stats: PhaseStatsLike | null | undefined): KgPhaseState {
  if (!stats) return 'not_run'
  const touched = stats.completed + stats.failed + stats.running + stats.pending
  if (touched === 0) return 'not_run'
  if (stats.running > 0) return 'running'
  if (stats.failed > 0 && stats.completed === 0) return 'failed'
  if (stats.failed > 0) return 'failed'
  if (stats.completed >= stats.total && stats.pending === 0) return 'completed'
  if (stats.pending > 0) return 'pending'
  return 'pending'
}

export function phaseTooltipLines(stats: PhaseStatsLike | null | undefined): string[] {
  if (!stats) return []
  const lines: string[] = []
  if (stats.failed > 0) lines.push(`${stats.failed} failed`)
  if (stats.running > 0) lines.push(`${stats.running} running`)
  if (stats.pending > 0) lines.push(`${stats.pending} pending`)
  return lines
}
