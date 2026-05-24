<template>
  <div :class="['kg-phase-pill', `kg-phase-pill--${tone}`]">
    <q-icon :name="stateIcon" size="12px" :class="['kg-phase-pill__icon', { 'kg-phase-pill__icon--rotating': state === 'running' }]" />
    <span class="kg-phase-pill__label">{{ shortLabel }}</span>
    <span v-if="count" class="kg-phase-pill__count">
      {{ count.done }}
      <span class="kg-phase-pill__sep">/</span>
      {{ count.total }}
    </span>
    <q-tooltip v-if="tooltipLines.length" anchor="top middle" self="bottom middle" :offset="[0, 6]" class="kg-phase-pill__tooltip">
      <div class="text-weight-medium q-mb-xs">{{ phaseTitle }}</div>
      <div v-for="(line, idx) in tooltipLines" :key="idx" class="kg-phase-pill__tooltip-line">{{ line }}</div>
    </q-tooltip>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export type KgPhaseName = 'sync' | 'metadata' | 'entities'
export type KgPhaseState = 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'not_run'

const props = withDefaults(
  defineProps<{
    phase: KgPhaseName
    state: KgPhaseState
    count?: { done: number; total: number } | null
    label?: string
    /** Extra tooltip lines beyond the auto-generated state summary. */
    extraTooltip?: string[]
  }>(),
  { count: null, label: '', extraTooltip: () => [] }
)

const phaseTitle = computed(() => {
  switch (props.phase) {
    case 'sync':
      return 'Sync'
    case 'metadata':
      return 'Metadata extraction'
    case 'entities':
      return 'Entity extraction'
    default:
      return ''
  }
})

const shortLabel = computed(() => {
  if (props.label) return props.label
  switch (props.phase) {
    case 'sync':
      return 'Sync'
    case 'metadata':
      return 'Meta'
    case 'entities':
      return 'aaa'
    default:
      return ''
  }
})

const tone = computed(() => {
  switch (props.state) {
    case 'completed':
      return 'success'
    case 'running':
      return 'info'
    case 'pending':
      return 'pending'
    case 'failed':
      return 'error'
    case 'skipped':
      return 'muted'
    case 'not_run':
    default:
      return 'idle'
  }
})

// State icon — the primary visual signal. We deliberately use *state* icons
// rather than per-phase icons here: at this size, three identical spinning
// sync icons read as "all loading" even when the document is fully done.
const stateIcon = computed(() => {
  switch (props.state) {
    case 'completed':
      return 'check'
    case 'running':
      return 'sync'
    case 'pending':
      return 'schedule'
    case 'failed':
      return 'close'
    case 'skipped':
      return 'remove'
    case 'not_run':
    default:
      return 'remove'
  }
})

const stateLabel = computed(() => {
  switch (props.state) {
    case 'completed':
      return 'Completed'
    case 'running':
      return 'Running'
    case 'pending':
      return 'Pending'
    case 'failed':
      return 'Failed'
    case 'skipped':
      return 'Skipped'
    case 'not_run':
    default:
      return 'Not run'
  }
})

const tooltipLines = computed(() => {
  const lines: string[] = [stateLabel.value]
  if (props.count) {
    lines.push(`${props.count.done} of ${props.count.total} documents`)
  }
  for (const line of props.extraTooltip) {
    if (line) lines.push(line)
  }
  return lines
})
</script>

<style scoped>
.kg-phase-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 20px;
  padding: 0 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  border: 1px solid transparent;
  user-select: none;
  transition:
    background 120ms ease,
    border-color 120ms ease;
}

.kg-phase-pill__icon {
  flex-shrink: 0;
}

.kg-phase-pill__label {
  letter-spacing: 0.01em;
}

.kg-phase-pill__count {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  margin-left: 2px;
  opacity: 0.85;
}

.kg-phase-pill__sep {
  opacity: 0.5;
  margin: 0 1px;
  font-weight: 500;
}

.kg-phase-pill__tooltip-line {
  font-size: 12px;
  line-height: 1.35;
  opacity: 0.85;
}

/* Tones. Color tokens match the existing KgStatusBadge palette. */
.kg-phase-pill--success {
  background: var(--q-status-ready);
  color: var(--q-status-ready-text);
}
.kg-phase-pill--info {
  background: var(--q-processing-ready);
  color: var(--q-processing-ready-text);
}
.kg-phase-pill--pending {
  background: var(--q-warning-bg);
  color: var(--q-warning-text);
}
.kg-phase-pill--error {
  background: var(--q-error-bg);
  color: var(--q-error-text);
}
.kg-phase-pill--muted {
  background: rgba(0, 0, 0, 0.06);
  color: rgba(0, 0, 0, 0.55);
}
.kg-phase-pill--idle {
  background: rgba(0, 0, 0, 0.035);
  color: rgba(0, 0, 0, 0.4);
  border-color: rgba(0, 0, 0, 0.06);
}

@keyframes kg-phase-rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.kg-phase-pill__icon--rotating {
  animation: kg-phase-rotate 1.2s linear infinite;
}
</style>
