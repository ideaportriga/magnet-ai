<template lang="pug">
q-chip.q-ma-none(v-if='type', :label='type', size='sm')
</template>

<script>
import { defineComponent } from 'vue'
import { formatTraceType } from '@shared/utils'

export default defineComponent({
  props: {
    row: {
      type: Object,
      required: true,
    },
  },
  computed: {
    type() {
      return formatTraceType(this.row?.type)
    },
  },
})
</script>
