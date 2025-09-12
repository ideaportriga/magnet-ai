<template lang="pug">
q-chip.km-small-chip(v-if='latency !== 0', :color='color', :text-color='textColor', :label='typeLabel')
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    row: {
      type: Object,
      required: true,
    },
  },
  computed: {
    typeLabel() {
      if (this.row?.type === 'prompt_eval') {
        return 'Prompt Template'
      }
      return 'RAG'
    },
    statusStyles() {
      return { color: 'in-progress', textColor: 'text-gray' }
    },
    color() {
      return this.statusStyles?.color || ''
    },
    textColor() {
      return this.statusStyles?.textColor || ''
    },
  },
})
</script>
