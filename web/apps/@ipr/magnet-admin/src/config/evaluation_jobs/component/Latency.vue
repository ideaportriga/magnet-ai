<template>
  <div v-if="latency !== 0" class="km-small-chip">
    <div class="km-field">{{ label }}</div>
  </div>
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
    label() {
      return new Intl.NumberFormat(undefined, {
        maximumFractionDigits: 0,
      }).format(this.latency)
    },
    latency() {
      return this.row?.average_latency || 0
    },
  },
})
</script>
