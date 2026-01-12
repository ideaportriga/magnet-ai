<template>
  <q-chip
    :class="['text-uppercase q-ma-none', { 'chip-rotating': normalizedStatus === 'syncing' }]"
    size="sm"
    :color="statusColor"
    :text-color="statusTextColor"
    :label="label"
    :icon="statusIcon"
  >
    <q-tooltip v-if="message" :offset="[0, 10]" style="max-width: 520px; white-space: pre-wrap">
      {{ message }}
    </q-tooltip>
  </q-chip>
</template>

<script setup lang="ts">
import { computed } from 'vue'

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

const statusColor = computed(() => {
  switch (normalizedStatus.value) {
    case 'completed':
      return 'status-ready'
    case 'processing':
    case 'extracted':
    case 'syncing':
      return 'info'
    case 'pending':
    case 'partial':
      return 'warning'
    case 'failed':
    case 'error':
      return 'error-bg'
    case 'not_synced':
      return 'gray'
    default:
      return 'gray'
  }
})

const statusTextColor = computed(() => {
  switch (normalizedStatus.value) {
    case 'completed':
      return 'status-ready-text'
    case 'processing':
    case 'extracted':
    case 'syncing':
      return 'white'
    case 'pending':
    case 'partial':
      return 'black'
    case 'failed':
    case 'error':
      return 'error-text'
    default:
      return 'text-gray'
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
@keyframes chip-rotate {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

::deep(.chip-rotating .q-chip__icon) {
  animation: chip-rotate 1s linear infinite;
}
</style>


