<template lang="pug">
q-chip.text-uppercase.q-ma-none(v-if='channel', :label='channel', size='sm')
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
