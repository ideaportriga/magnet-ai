<template>
  <div class="cluster" data-gap="xs" data-wrap="no">
    <km-chip v-if="row?.json_mode" class="text-uppercase m-0" size="sm">JSON Model</km-chip>
    <km-chip v-if="row?.structured_output" class="text-uppercase m-0" size="sm">Structured Outputs</km-chip>
    <km-chip v-if="row?.tool_calling" class="text-uppercase m-0" size="sm">Tool Calling</km-chip>
    <km-chip v-if="row?.reasoning" class="text-uppercase m-0" size="sm">Reasoning</km-chip>
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
    name: {
      type: String,
      required: true,
    },
  },
})
</script>
