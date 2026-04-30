<template>
  <km-chip v-if="channel" class="text-uppercase m-0" :label="channel" size="sm" />
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
    channel() {
      return this.row?.channel
    },
  },
})
</script>
