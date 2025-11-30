<template lang="pug">
pre.wrapped-text.km-button-xs-text {{ displayText }}
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    row: {
      type: Object,
      required: true,
    },
    name: {
      type: String,
      required: true,
    },
  },
  computed: {
    displayText() {
      return this.row?.[this.name] || ''
    },
  },
})
</script>

<style scoped>
.wrapped-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 4.5em;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
