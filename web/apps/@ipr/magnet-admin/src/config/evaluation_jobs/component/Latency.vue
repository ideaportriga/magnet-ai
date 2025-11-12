<template lang="pug">
.km-small-chip(v-if='latency !== 0', :color='color', :text-color='textColor')
  .km-field {{ label }}
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
