<template>
  <pre class="wrapped-text km-button-xs-text">{{ displayText }}</pre>
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
  overflow-wrap: break-word;
  max-block-size: 4.5em;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
