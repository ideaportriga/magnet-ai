<template lang="pug">
.column.q-gap-4
  div(v-for='(topic, index) in topics', :key='topic') {{ topic + `${index < topics.length - 1 ? ', ' : ''}` }}
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  row: {
    type: Object,
    required: true,
    default: () => ({}),
  },
})
const topics = computed(() => {
  if (!props.row?.conversation_data?.topics) return []
  return props.row.conversation_data.topics.map((topic) => topic)
})
</script>
