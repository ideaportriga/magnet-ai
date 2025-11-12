<template lang="pug">
.row.items-center.q-mt-md.bg-grey-2.ba-border.q-px-md.q-py-xs.cursor-pointer
  .km-title.text-left Group: {{ tool }}

  q-space
  .column
    .km-field.text-left Average latency: {{ latencyLabel }}
    .km-field.text-left Records: {{ records }}
</template>
<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: ['row'],

  setup() {},
  computed: {
    tool() {
      return this.row?.tool.name || ''
    },

    test_set() {
      return this.row?.test_sets?.[0]
    },
    records() {
      return `${this.row?.records_count} records`
    },
    latency() {
      return this.row?.average_latency || 0
    },
    latencyLabel() {
      return new Intl.NumberFormat(undefined, {
        maximumFractionDigits: 0,
        style: 'unit',
        unit: 'millisecond',
        unitDisplay: 'short',
      }).format(this.latency)
    },
  },
})
</script>
