<template lang="pug">
.status-chip
  q-chip.q-ma-none.text-uppercase(
    v-if="statusLabel"
    size="sm"
    :color="chipColor"
    :text-color="textColor"
    :label="statusLabel"
  )
    q-tooltip(v-if="tooltip", :offset="[0, 10]")
      span {{ tooltip }}
  span.text-grey-6(v-else)
    | —
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface DeepResearchRunRow {
  status?: string | null
  status_message?: string | null
  error?: string | null
}

const props = defineProps<{ row: DeepResearchRunRow }>()

const rawStatus = computed(() => (props.row?.status ?? '').toString().trim())
const statusKey = computed(() => rawStatus.value.toLowerCase())
const statusLabel = computed(() => (rawStatus.value ? rawStatus.value.replace(/_/g, ' ') : ''))
const tooltip = computed(() => props.row?.status_message || props.row?.error || '')

const chipColor = computed(() => {
  switch (statusKey.value) {
    case 'completed':
    case 'success':
      return 'status-ready'
    case 'running':
    case 'in_progress':
      return 'info'
    case 'pending':
    case 'queued':
      return 'warning'
    case 'failed':
    case 'error':
      return 'error-bg'
    default:
      return 'chip-accent-bg'
  }
})

const textColor = computed(() => {
  switch (statusKey.value) {
    case 'completed':
    case 'success':
      return 'status-ready-text'
    case 'running':
    case 'in_progress':
      return 'white'
    case 'pending':
    case 'queued':
      return 'warning-text'
    case 'failed':
    case 'error':
      return 'error-text'
    default:
      return 'primary'
  }
})
</script>

<style scoped>
.status-chip {
  display: flex;
  align-items: center;
  min-height: 24px;
}
</style>
