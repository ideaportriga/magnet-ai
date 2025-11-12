<template lang="pug">
template(v-if='data')
  km-chip.q-my-4(:label='data.label', :color='data.color', round, :class='data.text')
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
  if (props.row?.conversation_data?.resolution_status === 'resolved') return { color: 'like-bg', label: 'Resolved', text: 'text-like-text' }
  if (props.row?.conversation_data?.resolution_status === 'not_resolved') return { color: 'error-bg', label: 'Not resolved', text: 'text-error-text' }
  return { color: 'in-progress', label: 'Transferred', text: 'text-text-grey' }
})
</script>
