<template lang="pug">
.row.q-gap-4.no-wrap
  q-chip.text-uppercase.q-ma-none(
    v-if='row?.json_mode',
    size='sm',
    
  ) JSON Model
  q-chip.text-uppercase.q-ma-none(
    v-if='row?.structured_output',
    size='sm',
    
  ) Structured Outputs
  q-chip.text-uppercase.q-ma-none(
    v-if='row?.tool_calling',
    size='sm',
    
  ) Tool Calling
  q-chip.text-uppercase.q-ma-none(
    v-if='row?.reasoning',
    size='sm',
    
  ) Reasoning
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
})
</script>
