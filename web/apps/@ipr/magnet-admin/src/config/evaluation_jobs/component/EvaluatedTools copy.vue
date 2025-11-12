<template lang="pug">
pre class="wrapped-text km-button-xs-text" {{ tool }}
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
    tool() {
      return this.row?.tool.name || ''
    },
  },
})
</script>

<style scoped>
.wrapped-text {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
