<template>
  <div class="kg-source-status">
    <div class="kg-source-status__pipeline">
      <kg-sync-progress-bar v-if="isSyncing && row.sync_progress" :progress="row.sync_progress" />
      <kg-pipeline-strip v-else :phases="phases" mode="compact" />
    </div>
    <div class="kg-source-status__meta">
      <q-icon :name="statusSummary.icon" size="14px" :class="{ 'kg-source-status__icon--rotating': isSyncing }" />
      <span class="kg-source-status__summary">{{ statusSummary.label }}</span>
      <span class="kg-source-status__separator">•</span>
      <span class="kg-source-status__meta-label">Last sync</span>
      <span class="kg-source-status__meta-value">{{ relativeLastSync }}</span>
      <q-tooltip v-if="row.last_sync_at" anchor="top middle" self="bottom middle">
        {{ fullLastSync }}
      </q-tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatRelative } from '@shared/utils'
import { computed } from 'vue'
import { KgPipelineStrip, KgSyncProgressBar, type KgPhaseState, type KgPipelinePhase } from '../common'
import type { SourcePhaseStats, SourceRow } from './models'

const props = defineProps<{
  row: SourceRow
  /** Override of `row.status` for the duration of an in-flight UI-triggered sync. */
  effectiveStatus: string
}>()

const isSyncing = computed(() => props.effectiveStatus === 'syncing')

const statusSummary = computed(() => {
  switch (props.effectiveStatus) {
    case 'completed':
      return { label: 'Ready', icon: 'check_circle' }
    case 'syncing':
    case 'processing':
      return { label: 'Syncing', icon: 'sync' }
    case 'failed':
    case 'error':
      return { label: 'Needs attention', icon: 'error' }
    case 'pending':
      return { label: 'Pending', icon: 'schedule' }
    default:
      return { label: props.effectiveStatus || 'Not started', icon: 'radio_button_unchecked' }
  }
})

const relativeLastSync = computed(() => {
  if (!props.row.last_sync_at) return 'Never'
  return formatRelative(props.row.last_sync_at)
})

const fullLastSync = computed(() => {
  if (!props.row.last_sync_at) return 'Never'
  try {
    return new Date(props.row.last_sync_at).toLocaleString()
  } catch {
    return '—'
  }
})

/** Map aggregate phase counts to a single visual state. */
function phaseStateFor(stats: SourcePhaseStats | null | undefined): KgPhaseState {
  if (!stats || stats.total === 0) return 'not_run'
  if (stats.running > 0) return 'running'
  if (stats.failed > 0 && stats.completed === 0) return 'failed'
  if (stats.failed > 0) return 'failed'
  if (stats.completed >= stats.total) return 'completed'
  if (stats.completed > 0) return 'pending'
  return 'pending'
}

function lineForPhase(stats: SourcePhaseStats | null | undefined): string[] {
  if (!stats) return []
  const lines: string[] = []
  if (stats.failed > 0) lines.push(`${stats.failed} failed`)
  if (stats.running > 0) lines.push(`${stats.running} running`)
  return lines
}

const phases = computed<KgPipelinePhase[]>(() => {
  const stats = props.row.stats
  const sync = stats?.sync
  const meta = stats?.metadata
  const ent = stats?.entities
  return [
    {
      phase: 'sync',
      state: phaseStateFor(sync),
      count: sync && sync.total > 0 ? { done: sync.completed, total: sync.total } : null,
      tooltipLines: lineForPhase(sync),
    },
    {
      phase: 'metadata',
      state: phaseStateFor(meta),
      count: meta && meta.total > 0 ? { done: meta.completed, total: meta.total } : null,
      tooltipLines: lineForPhase(meta),
    },
    {
      phase: 'entities',
      state: phaseStateFor(ent),
      count: ent && ent.total > 0 ? { done: ent.completed, total: ent.total } : null,
      tooltipLines: lineForPhase(ent),
    },
  ]
})
</script>

<style scoped>
.kg-source-status {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 240px;
}

.kg-source-status__pipeline {
  display: flex;
  align-items: center;
  min-height: 20px;
}

.kg-source-status__meta {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
  color: var(--q-secondary-text, rgba(0, 0, 0, 0.55));
  font-size: 12px;
  margin-left: 2px;
}

.kg-source-status__summary {
  color: rgba(0, 0, 0, 0.72);
  font-weight: 600;
}

.kg-source-status__separator {
  color: rgba(0, 0, 0, 0.28);
}

.kg-source-status__meta-label {
  color: var(--q-secondary-text, rgba(0, 0, 0, 0.5));
}

.kg-source-status__meta-value {
  color: var(--q-secondary-text, rgba(0, 0, 0, 0.75));
}

@keyframes kg-source-status-rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.kg-source-status__icon--rotating {
  animation: kg-source-status-rotate 1.2s linear infinite;
}
</style>
