<template>
  <div class="status-chip">
    <km-chip v-if="statusLabel" class="m-0 text-uppercase" size="sm" :tone="tone" :label="statusLabel">
      <km-tooltip v-if="tooltip" :offset="[0, 10]"><span>{{ tooltip }}</span></km-tooltip>
    </km-chip><span v-else class="text-grey-6">—</span>
  </div>
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

const tone = computed(() => {
  switch (statusKey.value) {
    case 'completed':
    case 'success':
      return 'success'
    case 'running':
    case 'in_progress':
      return 'info'
    case 'pending':
    case 'queued':
      return 'warning'
    case 'failed':
    case 'error':
      return 'danger'
    default:
      return 'brand'
  }
})
</script>

<style scoped>
.status-chip {
  display: flex;
  align-items: center;
  min-block-size: 24px;
}
</style>
