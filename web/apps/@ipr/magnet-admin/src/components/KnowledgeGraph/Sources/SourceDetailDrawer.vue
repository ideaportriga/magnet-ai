<template>
  <kg-dialog-base
    :model-value="modelValue"
    title="Sync Status"
    :subtitle="source?.name || ''"
    confirm-label="Delta Sync"
    cancel-label="Close"
    :show-confirm="isSyncable"
    :disable-confirm="!isSyncable"
    size="md"
    max-height="85vh"
    @update:model-value="$emit('update:modelValue', $event)"
    @cancel="$emit('update:modelValue', false)"
    @confirm="emitSync(false)"
  >
    <div class="column q-gap-16">
      <kg-dialog-section title="Current Status">
        <div class="kg-sync-status__status">
          <span :class="['kg-sync-status__dot', `kg-sync-status__dot--${statusTone}`]">
            <q-icon :name="statusIcon" size="12px" :class="{ 'kg-sync-status__spin': effectiveStatus === 'syncing' }" />
          </span>

          <div class="kg-sync-status__status-text">
            <span :class="['kg-sync-status__status-label', `kg-sync-status__status-label--${statusTone}`]">{{ statusTitle }}</span>
            <span v-if="statusSubtitle" class="kg-sync-status__status-sub">- {{ statusSubtitle }}</span>
          </div>

          <div
            v-if="effectiveStatus !== 'syncing' && source?.last_sync?.duration_seconds != null"
            class="kg-sync-status__duration"
            :title="`Duration: ${formatDuration(source.last_sync.duration_seconds)}`"
          >
            {{ formatDuration(source.last_sync.duration_seconds) }}
          </div>
        </div>

        <div v-if="effectiveStatus === 'syncing' && source?.sync_progress" class="kg-sync-status__live">
          <kg-sync-progress-bar :progress="source.sync_progress" />
          <div v-if="source.sync_progress.current_document" class="kg-sync-status__live-doc" :title="source.sync_progress.current_document">
            <q-icon name="description" size="12px" />
            <span class="ellipsis">{{ source.sync_progress.current_document }}</span>
          </div>
        </div>
      </kg-dialog-section>

      <kg-dialog-section title="Pipeline">
        <div class="kg-sync-status__pipeline-layout">
          <div :class="['kg-sync-status__phase', `kg-sync-status__phase--${phaseTone(syncPhase.state)}`]">
            <span class="kg-sync-status__phase-marker">
              <q-icon :name="phaseMarkerIcon(syncPhase.state)" size="11px" :class="{ 'kg-sync-status__spin': syncPhase.state === 'running' }" />
            </span>
            <span class="kg-sync-status__phase-label">Sync</span>
            <span v-if="syncPhase.total > 0" class="kg-sync-status__phase-count">
              {{ syncPhase.completed }}
              <span class="kg-sync-status__phase-sep">/</span>
              {{ syncPhase.total }}
            </span>
          </div>

          <div class="kg-sync-status__pipeline-connector" aria-hidden="true" />

          <div class="kg-sync-status__parallel-block">
            <div v-for="p in parallelPhases" :key="p.phase" :class="['kg-sync-status__phase', `kg-sync-status__phase--${phaseTone(p.state)}`]">
              <span class="kg-sync-status__phase-marker">
                <q-icon :name="phaseMarkerIcon(p.state)" size="11px" :class="{ 'kg-sync-status__spin': p.state === 'running' }" />
              </span>
              <span class="kg-sync-status__phase-label">{{ p.title }}</span>
              <span v-if="p.total > 0" class="kg-sync-status__phase-count">
                {{ p.completed }}
                <span class="kg-sync-status__phase-sep">/</span>
                {{ p.total }}
              </span>
            </div>
          </div>
        </div>

        <div v-if="pipelineExtras.length" class="kg-sync-status__pipeline-extras">
          <span
            v-for="extra in pipelineExtras"
            :key="`${extra.phase}-${extra.tone}`"
            :class="['kg-sync-status__extra', `kg-sync-status__extra--${extra.tone}`]"
          >
            <q-icon :name="extra.icon" size="11px" />
            {{ extra.label }}
          </span>
        </div>
      </kg-dialog-section>

      <kg-dialog-section v-if="source?.last_sync" title="Last Sync">
        <div class="kg-sync-status__summary-grid">
          <div class="kg-sync-status__summary-item">
            <span class="kg-sync-status__summary-label">Started</span>
            <span class="kg-sync-status__summary-value">{{ formatTimestamp(source.last_sync.started_at) }}</span>
          </div>
          <div class="kg-sync-status__summary-item">
            <span class="kg-sync-status__summary-label">Duration</span>
            <span class="kg-sync-status__summary-value">{{ formatDuration(source.last_sync.duration_seconds) }}</span>
          </div>
          <div v-if="source.last_sync.outcome" class="kg-sync-status__summary-item">
            <span class="kg-sync-status__summary-label">Outcome</span>
            <span class="kg-sync-status__summary-value kg-sync-status__outcome">{{ source.last_sync.outcome }}</span>
          </div>
        </div>

        <div v-if="lastSyncBreakdown.length" class="kg-sync-status__chips">
          <span v-for="part in lastSyncBreakdown" :key="part.label" :class="['kg-sync-status__chip', `kg-sync-status__chip--${part.tone}`]">
            <span class="kg-sync-status__chip-value">{{ part.value }}</span>
            <span>{{ part.label }}</span>
          </span>
        </div>
      </kg-dialog-section>

      <kg-dialog-section v-else title="Last Sync">
        <div class="kg-sync-status__empty">
          <q-icon name="history_toggle_off" size="16px" />
          <span>No sync has been run for this source yet.</span>
        </div>
      </kg-dialog-section>
    </div>

    <template v-if="isSyncable" #actions-before-confirm>
      <km-btn outline label="Sync All" size="sm" class="kg-sync-status__resync-button" @click="showFromScratchConfirm = true" />
    </template>

    <kg-confirm-dialog
      v-model="showFromScratchConfirm"
      title="Sync from scratch"
      icon-variant="warning"
      :description="`Re-process every document in '${source?.name}' regardless of whether it changed?`"
      confirm-label="Sync from scratch"
      destructive
      @confirm="confirmFromScratch"
    >
      <template #warning>
        Change detection is bypassed, so every document is re-fetched and re-processed. Existing document IDs are preserved, but the run may take
        significantly longer than a delta sync.
      </template>
    </kg-confirm-dialog>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { KgConfirmDialog, KgDialogBase, KgDialogSection, KgSyncProgressBar, phaseStateFor, type KgPhaseState } from '../common'
import { type SourcePhaseStats, type SourceRow } from './models'

const props = defineProps<{
  modelValue: boolean
  source: SourceRow | null
  effectiveStatus: string
  isSyncable: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'sync', opts: { fromScratch: boolean }): void
}>()

const showFromScratchConfirm = ref(false)

function emitSync(fromScratch: boolean) {
  emit('sync', { fromScratch })
  emit('update:modelValue', false)
}

function confirmFromScratch() {
  showFromScratchConfirm.value = false
  emitSync(true)
}

const statusTone = computed(() => {
  switch (props.effectiveStatus) {
    case 'syncing':
      return 'info'
    case 'error':
    case 'failed':
      return 'error'
    case 'ready':
    case 'completed':
    case 'success':
      return 'success'
    default:
      return 'idle'
  }
})

const statusIcon = computed(() => {
  switch (statusTone.value) {
    case 'info':
      return 'sync'
    case 'error':
      return 'priority_high'
    case 'success':
      return 'check'
    default:
      return 'circle'
  }
})

const statusIconColor = computed(() => {
  switch (statusTone.value) {
    case 'info':
      return 'primary'
    case 'error':
      return 'negative'
    case 'success':
      return 'positive'
    default:
      return 'grey-7'
  }
})

const statusTitle = computed(() => {
  switch (props.effectiveStatus) {
    case 'syncing':
      return 'Sync in progress'
    case 'error':
    case 'failed':
      return 'Last sync failed'
    case 'ready':
    case 'completed':
    case 'success':
      return 'Up to date'
    default:
      return props.source?.last_sync ? 'Idle' : 'Never synced'
  }
})

const statusSubtitle = computed(() => {
  const ls = props.source?.last_sync
  if (props.effectiveStatus === 'syncing') {
    const p = props.source?.sync_progress
    if (p?.total && p?.processed != null) {
      return `${p.processed} of ${p.total} processed`
    }
    return 'Processing documents...'
  }
  if (ls?.completed_at) {
    return `last run ${relativeFromNow(ls.completed_at)}`
  }
  return ''
})

function phaseTone(state: KgPhaseState): string {
  switch (state) {
    case 'completed':
      return 'success'
    case 'running':
      return 'info'
    case 'failed':
      return 'error'
    case 'pending':
      return 'pending'
    default:
      return 'idle'
  }
}

function phaseMarkerIcon(state: KgPhaseState): string {
  switch (state) {
    case 'completed':
      return 'check'
    case 'running':
      return 'sync'
    case 'failed':
      return 'close'
    case 'pending':
      return 'schedule'
    default:
      return 'remove'
  }
}

type PhaseDescriptor = {
  phase: 'sync' | 'metadata' | 'entities'
  title: string
  state: KgPhaseState
  completed: number
  failed: number
  running: number
  pending: number
  total: number
}

const phaseDescriptors = computed<PhaseDescriptor[]>(() => {
  const make = (phase: 'sync' | 'metadata' | 'entities', title: string, stats: SourcePhaseStats | null | undefined): PhaseDescriptor => ({
    phase,
    title,
    state: phaseStateFor(stats),
    completed: stats?.completed ?? 0,
    failed: stats?.failed ?? 0,
    running: stats?.running ?? 0,
    pending: stats?.pending ?? 0,
    total: stats?.total ?? 0,
  })

  return [
    make('sync', 'Sync', props.source?.stats?.sync),
    make('metadata', 'Metadata', props.source?.stats?.metadata),
    make('entities', 'Entities', props.source?.stats?.entities),
  ]
})

const syncPhase = computed(() => phaseDescriptors.value[0])
const parallelPhases = computed(() => phaseDescriptors.value.slice(1))

type PipelineExtra = { phase: string; tone: 'info' | 'error' | 'warning'; icon: string; label: string }

const pipelineExtras = computed<PipelineExtra[]>(() => {
  const out: PipelineExtra[] = []
  for (const p of phaseDescriptors.value) {
    if (p.running > 0) {
      out.push({ phase: p.phase, tone: 'info', icon: 'sync', label: `${p.running} ${p.title.toLowerCase()} running` })
    }
    if (p.pending > 0) {
      out.push({ phase: p.phase, tone: 'warning', icon: 'schedule', label: `${p.pending} ${p.title.toLowerCase()} pending` })
    }
    if (p.failed > 0) {
      out.push({ phase: p.phase, tone: 'error', icon: 'priority_high', label: `${p.failed} ${p.title.toLowerCase()} failed` })
    }
  }
  return out
})

type BreakdownPart = { label: string; value: number; tone: 'success' | 'info' | 'muted' | 'warning' | 'error' }

const lastSyncBreakdown = computed<BreakdownPart[]>(() => {
  const ls = props.source?.last_sync
  if (!ls) return []
  const parts: BreakdownPart[] = [
    { label: 'synced', value: ls.synced, tone: 'success' },
    { label: 'failed', value: ls.failed, tone: 'error' },
    { label: 'content changed', value: ls.content_changed, tone: 'info' },
    { label: 'metadata updated', value: ls.metadata_only_updated, tone: 'info' },
    { label: 'unchanged', value: ls.unchanged_skipped, tone: 'muted' },
    { label: 'skipped', value: ls.skipped, tone: 'muted' },
    { label: 'deleted', value: ls.deleted, tone: 'warning' },
  ]
  return parts.filter((p) => p.value > 0)
})

function formatTimestamp(value?: string | null): string {
  if (!value) return '-'
  try {
    return new Date(value).toLocaleString()
  } catch {
    return '-'
  }
}

function formatDuration(seconds?: number | null): string {
  if (seconds == null) return '-'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  if (mins < 60) return `${mins}m ${secs}s`
  const hours = Math.floor(mins / 60)
  return `${hours}h ${mins % 60}m`
}

function relativeFromNow(value: string): string {
  try {
    const then = new Date(value).getTime()
    const diffMs = Date.now() - then
    if (!Number.isFinite(diffMs) || diffMs < 0) return formatTimestamp(value)
    const mins = Math.floor(diffMs / 60000)
    if (mins < 1) return 'just now'
    if (mins < 60) return `${mins} minute${mins === 1 ? '' : 's'} ago`
    const hours = Math.floor(mins / 60)
    if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`
    const days = Math.floor(hours / 24)
    if (days < 7) return `${days} day${days === 1 ? '' : 's'} ago`
    return new Date(value).toLocaleDateString()
  } catch {
    return formatTimestamp(value)
  }
}
</script>

<style scoped>
@keyframes kg-sync-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.kg-sync-status__spin {
  animation: kg-sync-spin 1.2s linear infinite;
}

.kg-sync-status__status {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.kg-sync-status__dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: white;
}

.kg-sync-status__dot--info {
  background: var(--q-processing-ready-text, #1c4ec9);
}
.kg-sync-status__dot--success {
  background: var(--q-status-ready-text, #1a7a3a);
}
.kg-sync-status__dot--error {
  background: var(--q-error-text, #c43030);
}
.kg-sync-status__dot--idle {
  background: rgba(0, 0, 0, 0.34);
}

.kg-sync-status__status-text {
  flex: 1 1 auto;
  min-width: 0;
  font-size: 13px;
  line-height: 1.35;
  display: flex;
  align-items: baseline;
  gap: 5px;
  flex-wrap: wrap;
}

.kg-sync-status__status-label {
  font-weight: 600;
}
.kg-sync-status__status-label--info {
  color: var(--q-processing-ready-text, #1c4ec9);
}
.kg-sync-status__status-label--success {
  color: var(--q-status-ready-text, #1a7a3a);
}
.kg-sync-status__status-label--error {
  color: var(--q-error-text, #c43030);
}
.kg-sync-status__status-label--idle {
  color: var(--q-primary-text, #171717);
}

.kg-sync-status__status-sub {
  color: var(--q-secondary-text, rgba(0, 0, 0, 0.6));
  font-weight: 400;
}

.kg-sync-status__duration {
  font-size: 12px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--q-secondary-text, rgba(0, 0, 0, 0.55));
  flex-shrink: 0;
}

.kg-sync-status__live {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.kg-sync-status__live-doc {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--q-secondary-text, rgba(0, 0, 0, 0.6));
  min-width: 0;
}

.kg-sync-status__live-doc span {
  min-width: 0;
}

.kg-sync-status__pipeline-layout {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding-top: 2px;
}

.kg-sync-status__pipeline-connector {
  flex: 0 0 24px;
  height: 1px;
  background: rgba(0, 0, 0, 0.14);
}

.kg-sync-status__parallel-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kg-sync-status__parallel-block::before {
  content: '';
  position: absolute;
  margin-top: 12px;
  border-left: 1px solid rgba(0, 0, 0, 0.14);
  width: 2px;
  height: 31px;
}

.kg-sync-status__phase {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 24px;
}

.kg-sync-status__parallel-block .kg-sync-status__phase::before {
  content: '';
  width: 22px;
  height: 1px;
  flex-shrink: 0;
  background: rgba(0, 0, 0, 0.14);
}

.kg-sync-status__phase-marker {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: currentColor;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.kg-sync-status__phase-marker :deep(.q-icon) {
  color: white;
}
.kg-sync-status__phase--success {
  color: var(--q-status-ready-text, #1a7a3a);
}
.kg-sync-status__phase--info {
  color: var(--q-processing-ready-text, #1c4ec9);
}
.kg-sync-status__phase--error {
  color: var(--q-error-text, #c43030);
}
.kg-sync-status__phase--pending {
  color: var(--q-warning-text, #d97706);
}
.kg-sync-status__phase--idle {
  color: rgba(0, 0, 0, 0.3);
}

.kg-sync-status__phase-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.72);
}

.kg-sync-status__phase-count {
  font-size: 11px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: rgba(0, 0, 0, 0.5);
}

.kg-sync-status__phase-sep {
  opacity: 0.55;
  margin: 0 1px;
  font-weight: 400;
}

.kg-sync-status__pipeline-extras {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.kg-sync-status__extra,
.kg-sync-status__chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.kg-sync-status__extra--info,
.kg-sync-status__chip--info {
  color: var(--q-processing-ready-text, #1c4ec9);
  background: var(--q-processing-ready, #e8f0ff);
}

.kg-sync-status__extra--error,
.kg-sync-status__chip--error {
  color: var(--q-error-text, #c43030);
  background: var(--q-error-bg, #fdecec);
}

.kg-sync-status__extra--warning,
.kg-sync-status__chip--warning {
  color: var(--q-warning-text, #d97706);
  background: var(--q-warning-bg, #fff4e0);
}

.kg-sync-status__outcome {
  text-transform: capitalize;
}

.kg-sync-status__summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.kg-sync-status__summary-item {
  min-width: 0;
  padding: 8px 10px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  background: #fff;
}

.kg-sync-status__summary-label {
  display: block;
  margin-bottom: 4px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--q-secondary-text, rgba(0, 0, 0, 0.5));
}

.kg-sync-status__summary-value {
  display: block;
  min-width: 0;
  overflow: hidden;
  color: var(--q-primary-text, #171717);
  font-size: 13px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kg-sync-status__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.kg-sync-status__chip-value {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.kg-sync-status__chip--success {
  background: var(--q-status-ready, #e6f6ec);
  color: var(--q-status-ready-text, #1a7a3a);
}

.kg-sync-status__chip--muted {
  background: rgba(0, 0, 0, 0.04);
  color: rgba(0, 0, 0, 0.55);
}

.kg-sync-status__empty {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 0;
  font-size: 12px;
  color: var(--q-secondary-text, rgba(0, 0, 0, 0.55));
}

.kg-sync-status__resync-button {
  margin-right: 8px;
}

@media (max-width: 620px) {
  .kg-sync-status__summary-grid {
    grid-template-columns: 1fr;
  }

  .kg-sync-status__pipeline-layout {
    align-items: flex-start;
  }
}
</style>
