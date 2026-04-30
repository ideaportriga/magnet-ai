<template>
  <div class="cluster mt-md bg-grey-2 ba-border px-md py-xs cursor-pointer">
    <div class="km-title text-left">Job Id:</div>
    <km-btn class="ml-sm" :label="tool" icon="eye" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="viewDetails" />
    <div class="km-space" />
    <div class="stack" data-gap="0">
      <div class="km-field text-left">Average latency: {{ latencyLabel }}</div>
      <div class="km-field text-left">Records: {{ records }}</div>
    </div>
    <km-btn class="ml-sm" label="Report" icon="download" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="viewDetails" />
  </div>
</template>
<script>
import { defineComponent } from 'vue'

export default defineComponent({
  props: ['row'],

  setup() {},
  computed: {
    tool() {
      return this.row?.groupId || ''
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
  methods: {
    viewDetails(event) {
      // stop propogation
      event.stopPropagation()
    },
  },
})
</script>
