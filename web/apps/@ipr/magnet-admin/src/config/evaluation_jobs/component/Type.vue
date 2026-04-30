<template>
  <km-chip v-if="latency !== 0" class="km-small-chip" tone="neutral" :label="typeLabel" />
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
  },
})
</script>
