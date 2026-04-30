<template>
  <template v-if="data">
    <km-chip class="my-xs" :label="data.label" :tone="data.tone" round />
  </template>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({
  row: Object,
  name: String,
})

//const extra_data = computed(() => props.row?.extra_data)
//const resolution_status = computed(() => extra_data.value?.resolution_status)
const data = computed(() => {
  if (!props.row?.conversation_data?.resolution_status) return ''
  if (props.row?.conversation_data?.resolution_status === 'resolved') return { tone: 'success', label: 'Resolved' }
  if (props.row?.conversation_data?.resolution_status === 'not_resolved') return { tone: 'danger', label: 'Not resolved' }
  return { tone: 'neutral', label: 'Transferred' }
})
</script>
