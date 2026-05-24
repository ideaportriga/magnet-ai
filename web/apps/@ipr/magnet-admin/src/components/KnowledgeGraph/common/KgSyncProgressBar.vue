<template>
  <div class="kg-sync-progress">
    <q-linear-progress
      :value="fraction"
      :indeterminate="indeterminate"
      color="primary"
      track-color="grey-3"
      rounded
      size="6px"
      class="kg-sync-progress__bar"
    />
    <div class="kg-sync-progress__caption">
      <span v-if="hasCounts" class="kg-sync-progress__count">
        {{ progress.processed }} / {{ progress.total }}
      </span>
      <span v-if="phaseLabel" class="kg-sync-progress__phase">{{ phaseLabel }}</span>
    </div>
    <q-tooltip v-if="tooltipText" anchor="top middle" self="bottom middle" :offset="[0, 6]">
      {{ tooltipText }}
    </q-tooltip>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export type KgSyncProgress = {
  phase?: string | null
  processed?: number | null
  total?: number | null
  current_document?: string | null
  started_at?: string | null
  updated_at?: string | null
}

const props = defineProps<{ progress: KgSyncProgress }>()

const hasCounts = computed(() => {
  const total = Number(props.progress?.total ?? 0)
  return Number.isFinite(total) && total > 0
})

const fraction = computed(() => {
  const total = Number(props.progress?.total ?? 0)
  const processed = Number(props.progress?.processed ?? 0)
  if (!Number.isFinite(total) || total <= 0) return 0
  return Math.max(0, Math.min(1, processed / total))
})

const indeterminate = computed(() => !hasCounts.value)

const phaseLabel = computed(() => {
  const phase = String(props.progress?.phase || '').toLowerCase()
  switch (phase) {
    case 'starting':
      return 'starting up'
    case 'listing':
      return 'discovering documents'
    case 'downloading':
      return 'downloading'
    case 'processing':
      return 'processing'
    case 'cleanup':
      return 'finishing up'
    default:
      return phase || ''
  }
})

const tooltipText = computed(() => props.progress?.current_document || '')
</script>

<style scoped>
.kg-sync-progress {
  display: inline-flex;
  flex-direction: column;
  gap: 4px;
  min-width: 160px;
  max-width: 260px;
}

.kg-sync-progress__bar {
  width: 100%;
}

.kg-sync-progress__caption {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--q-secondary-text, rgba(0, 0, 0, 0.6));
}

.kg-sync-progress__count {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.kg-sync-progress__phase {
  text-transform: lowercase;
  letter-spacing: 0.01em;
}
</style>
