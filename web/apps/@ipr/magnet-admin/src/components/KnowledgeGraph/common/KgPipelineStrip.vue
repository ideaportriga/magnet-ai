<template>
  <div :class="['kg-pipeline-strip', `kg-pipeline-strip--${mode}`]">
    <div v-for="(p, index) in enrichedPhases" :key="p.phase" :class="['kg-pipeline-strip__item', `kg-pipeline-strip__item--${p.tone}`]">
      <div v-if="index > 0" class="kg-pipeline-strip__connector" />
      <div class="kg-pipeline-strip__step">
        <span class="kg-pipeline-strip__marker">
          <q-icon :name="p.icon" size="12px" :class="{ 'kg-pipeline-strip__icon--rotating': p.state === 'running' }" />
        </span>
        <span class="kg-pipeline-strip__label">{{ p.shortLabel }}</span>
        <span v-if="p.count" class="kg-pipeline-strip__count">
          {{ p.count.done }}
          <span class="kg-pipeline-strip__sep">/</span>
          {{ p.count.total }}
        </span>
      </div>
      <q-tooltip v-if="p.tooltipLines.length" anchor="top middle" self="bottom middle" :offset="[0, 6]" class="kg-pipeline-strip__tooltip">
        <div class="text-weight-medium q-mb-xs">{{ p.title }}</div>
        <div v-for="(line, lineIndex) in p.tooltipLines" :key="lineIndex" class="kg-pipeline-strip__tooltip-line">
          {{ line }}
        </div>
      </q-tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { KgPhaseName, KgPhaseState } from './KgPhasePill.vue'

export type KgPipelinePhase = {
  phase: KgPhaseName
  state: KgPhaseState
  count?: { done: number; total: number } | null
  tooltipLines?: string[]
}

const props = withDefaults(
  defineProps<{
    phases: KgPipelinePhase[]
    mode?: 'compact' | 'expanded'
  }>(),
  { mode: 'compact' }
)

function titleFor(phase: KgPhaseName): string {
  switch (phase) {
    case 'sync':
      return 'Sync'
    case 'metadata':
      return 'Metadata extraction'
    case 'entities':
      return 'Entity extraction'
    default:
      return ''
  }
}

function shortLabelFor(phase: KgPhaseName): string {
  switch (phase) {
    case 'sync':
      return 'Sync'
    case 'metadata':
      return props.mode === 'expanded' ? 'Metadata' : 'Meta'
    case 'entities':
      return props.mode === 'expanded' ? 'Entities' : 'Entities'
    default:
      return ''
  }
}

function stateLabelFor(state: KgPhaseState): string {
  switch (state) {
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
}

function toneFor(state: KgPhaseState): string {
  switch (state) {
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
}

function iconFor(state: KgPhaseState): string {
  switch (state) {
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
}

const enrichedPhases = computed(() =>
  props.phases.map((phase) => {
    const tooltipLines = [stateLabelFor(phase.state)]
    if (phase.count) tooltipLines.push(`${phase.count.done} of ${phase.count.total} documents`)
    for (const line of phase.tooltipLines ?? []) {
      if (line) tooltipLines.push(line)
    }

    return {
      ...phase,
      title: titleFor(phase.phase),
      shortLabel: shortLabelFor(phase.phase),
      tone: toneFor(phase.state),
      icon: iconFor(phase.state),
      tooltipLines,
    }
  })
)
</script>

<style scoped>
.kg-pipeline-strip {
  display: inline-flex;
  align-items: center;
  gap: 0;
  flex-wrap: nowrap;
  min-width: 0;
}

.kg-pipeline-strip--expanded {
  gap: 0;
}

.kg-pipeline-strip__item {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  color: rgba(0, 0, 0, 0.5);
}

.kg-pipeline-strip__connector {
  width: 18px;
  height: 1px;
  margin: 0 4px;
  background: rgba(0, 0, 0, 0.14);
}

.kg-pipeline-strip__step {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
  line-height: 1;
  white-space: nowrap;
}

.kg-pipeline-strip__marker {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  flex: 0 0 18px;
  border-radius: 50%;
  color: currentColor;
  background: currentColor;
}

.kg-pipeline-strip__marker :deep(.q-icon) {
  color: white;
}

.kg-pipeline-strip__label {
  color: rgba(0, 0, 0, 0.72);
  font-size: 12px;
  font-weight: 600;
}

.kg-pipeline-strip--compact .kg-pipeline-strip__label {
  max-width: 52px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kg-pipeline-strip__count {
  color: rgba(0, 0, 0, 0.56);
  font-size: 11px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.kg-pipeline-strip__sep {
  opacity: 0.55;
  margin: 0 1px;
  font-weight: 500;
}

.kg-pipeline-strip__tooltip-line {
  font-size: 12px;
  line-height: 1.35;
  opacity: 0.85;
}

.kg-pipeline-strip__item--success {
  color: var(--q-status-ready-text);
}

.kg-pipeline-strip__item--info {
  color: var(--q-processing-ready-text);
}

.kg-pipeline-strip__item--pending {
  color: var(--q-warning-text);
}

.kg-pipeline-strip__item--error {
  color: var(--q-error-text);
}

.kg-pipeline-strip__item--muted,
.kg-pipeline-strip__item--idle {
  color: rgba(0, 0, 0, 0.34);
}

@keyframes kg-pipeline-rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.kg-pipeline-strip__icon--rotating {
  animation: kg-pipeline-rotate 1.2s linear infinite;
}
</style>
