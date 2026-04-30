<template>
  <km-chip
    :class="['text-uppercase m-0', { 'chip-rotating': normalizedStatus === 'syncing' }]"
    size="sm"
    :tone="statusTone"
    :label="label"
    :icon="statusIcon"
  >
    <km-tooltip v-if="message" :offset="[0, 10]" style="max-inline-size: 520px; white-space: pre-wrap">
      {{ message }}
    </km-tooltip>
  </km-chip>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { m } from '@/paraglide/messages'

const props = defineProps<{
  status?: string | null
  message?: string | null
}>()

const normalizedStatus = computed(() => String(props.status || '').toLowerCase())
const message = computed(() => props.message || '')

const label = computed(() => {
  const s = normalizedStatus.value
  if (!s) return 'unknown'
  return s.split('_').join(' ')
})

const statusTone = computed(() => {
  switch (normalizedStatus.value) {
    case 'completed':
      return 'success'
    case 'processing':
    case 'extracted':
    case 'syncing':
      return 'info'
    case 'pending':
    case 'partial':
      return 'warning'
    case 'failed':
    case 'error':
      return 'danger'
    case 'not_synced':
      return 'neutral'
    default:
      return 'neutral'
  }
})

const statusIcon = computed(() => {
  switch (normalizedStatus.value) {
    case 'completed':
      return 'check_circle'
    case 'syncing':
      return 'sync'
    case 'processing':
    case 'extracted':
      return 'hourglass_top'
    case 'pending':
    case 'not_synced':
      return 'schedule'
    case 'partial':
      return 'warning'
    case 'failed':
    case 'error':
      return 'error'
    default:
      return 'help_outline'
  }
})
</script>

<style scoped>
.chip-rotating :deep(svg) {
  animation: ds-spin 1s var(--ds-ease-linear) infinite;
}
</style>


