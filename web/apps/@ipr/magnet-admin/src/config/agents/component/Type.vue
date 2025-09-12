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
      if (this.row?.type === 'prompt_template') {
        return 'Prompt Template'
      }
      if (this.row?.type === 'rag') {
        return 'RAG Tool'
      }

      if (this.row?.type === 'api') {
        return 'API Tool'
      }
      return this.row?.type
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
