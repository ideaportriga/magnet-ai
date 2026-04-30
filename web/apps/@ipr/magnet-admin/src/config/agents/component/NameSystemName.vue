<template>
  <div>
    <div class="km-title text-left ellipsis">{{ row?.name }}</div>
    <km-chip class="km-small-chip" tone="neutral" :label="row?.system_name" />
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
})
</script>
