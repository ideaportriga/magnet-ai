<template>
  <div class="cluster mt-md bg-grey-2 ba-border px-md py-xs cursor-pointer">
    <div class="km-title text-left">Group: {{ tool }}</div>
    <div class="km-space" />
    <div class="stack" data-gap="0">
      <div class="km-field text-left">Average latency: {{ latencyLabel }}</div>
      <div class="km-field text-left">Records: {{ records }}</div>
    </div>
  </div>
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
